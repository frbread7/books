#!/usr/bin/env python3
"""Validate and safely register independently published textbook manifests."""
from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse

from jsonschema import Draft202012Validator, FormatChecker
import reference_intelligence as reference_gate

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "catalog" / "books"
DATA = ROOT / "site" / "data"
SCHEMA = ROOT / "schemas" / "book.schema.json"
REFERENCE_INVENTORY = ROOT / "catalog" / "reference-intelligence" / "inventory.json"
EDITORIAL_DECISIONS = ROOT / "catalog" / "reference-intelligence" / "editorial-decisions.json"
PROVENANCE_AUDIT = ROOT / "catalog" / "reference-intelligence" / "provenance-audit.json"
STATUSES = {"planned", "in-progress", "published", "archived"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ManifestError(ValueError):
    pass


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def fail(message: str) -> None:
    raise ManifestError(message)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path}: {exc}")


def check_url(value, field):
    if not isinstance(value, str):
        fail(f"{field} must be a URL string")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        fail(f"{field} must be an https URL without embedded credentials: {value!r}")
    if normalized_url_path(parsed.path) is None:
        fail(f"{field} must not contain encoded traversal, backslashes, or control characters")


def normalized_url_path(path):
    """Decode URL paths before checking boundaries; reject ambiguous traversal."""
    if re.search(r"%(?![0-9a-fA-F]{2})", path):
        return None
    decoded = path
    for _ in range(8):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    else:
        return None
    if any(ord(char) < 0x20 or ord(char) == 0x7f for char in decoded) or "\\" in decoded:
        return None
    if any(segment in {".", ".."} for segment in decoded.split("/")):
        return None
    normalized = posixpath.normpath(decoded)
    return normalized if normalized.startswith("/") else None


def path_is_within_production(target_path, production_path):
    target = normalized_url_path(target_path)
    root = normalized_url_path(production_path or "/")
    if target is None or root is None:
        return False
    root_prefix = root.rstrip("/") + "/"
    return target == root.rstrip("/") or target.startswith(root_prefix)


def localized(obj, field):
    if not isinstance(obj, dict) or set(obj) != {"en", "ko"}:
        fail(f"{field} must provide both en and ko values")
    if any(not isinstance(v, str) or not v.strip() for v in obj.values()):
        fail(f"{field} values must be non-empty strings")


def localized_list(obj, field):
    if not isinstance(obj, dict) or set(obj) != {"en", "ko"}:
        fail(f"{field} must provide both en and ko lists")
    if any(not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items) for items in obj.values()):
        fail(f"{field} values must be lists of non-empty strings")


def validate_manifest(book):
    schema = read_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(book))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "$"
        fail(f"schema validation at {location}: {first.message}")
    required = {"schemaVersion", "id", "slug", "title", "subtitle", "description", "category", "tags", "status", "repositoryUrl", "productionUrl", "languages", "version", "lastUpdated", "chapterCount", "chapters", "experiments", "prerequisites", "relatedBooks", "attribution", "cover", "theme"}
    if not isinstance(book, dict):
        fail("manifest root must be an object")
    allowed = required | {"languageUrls", "publicationEvidence"}
    extra = sorted(set(book) - allowed)
    if extra:
        fail("unknown fields: " + ", ".join(extra))
    missing = sorted(required - set(book))
    if missing:
        fail("missing required fields: " + ", ".join(missing))
    if book["schemaVersion"] != 1:
        fail("schemaVersion must be 1")
    for field in ("id", "slug"):
        if not isinstance(book[field], str) or not SLUG.fullmatch(book[field]):
            fail(f"{field} must be a lowercase URL-safe identifier")
    for field in ("title", "subtitle", "description"):
        localized(book[field], field)
    if not isinstance(book["category"], str) or not book["category"].strip():
        fail("category must be a non-empty string")
    if not isinstance(book["status"], str) or book["status"] not in STATUSES:
        fail(f"status must be one of {', '.join(sorted(STATUSES))}")
    if book["category"] not in {c.get("id") for c in read_json(ROOT / "catalog" / "categories.json").get("categories", [])}:
        fail(f"category is not registered in catalog/categories.json: {book['category']!r}")
    if not isinstance(book["tags"], list) or any(not isinstance(tag, str) or not tag.strip() for tag in book["tags"]):
        fail("tags must be a list of non-empty strings")
    if len(set(book["tags"])) != len(book["tags"]):
        fail("tags contains duplicates")
    if not isinstance(book["languages"], list) or not book["languages"] or any(not isinstance(lang, str) for lang in book["languages"]) or set(book["languages"]) - {"en", "ko"}:
        fail("languages must contain en and/or ko")
    if len(set(book["languages"])) != len(book["languages"]):
        fail("languages contains duplicates")
    for field in ("repositoryUrl", "productionUrl"):
        check_url(book[field], field)
    if "languageUrls" in book:
        if not isinstance(book["languageUrls"], dict) or not book["languageUrls"] or set(book["languageUrls"]) - set(book["languages"]):
            fail("languageUrls must map only deployed languages")
        for lang, url in book["languageUrls"].items():
            check_url(url, f"languageUrls.{lang}")
            if urlparse(url).netloc != urlparse(book["productionUrl"]).netloc:
                fail(f"languageUrls.{lang} must use the production host")
            if not path_is_within_production(urlparse(url).path, urlparse(book["productionUrl"]).path):
                fail(f"languageUrls.{lang} must remain under the production path")
    try:
        date.fromisoformat(book["lastUpdated"])
    except (ValueError, TypeError):
        fail("lastUpdated must be an ISO date")
    if not isinstance(book["chapters"], list):
        fail("chapters must be a list")
    if not isinstance(book["chapterCount"], int) or isinstance(book["chapterCount"], bool) or book["chapterCount"] != len(book["chapters"]):
        fail("chapterCount must equal the length of chapters")
    if book["status"] == "published" and book["chapterCount"] < 1:
        fail("published books must include at least one chapter")
    chapter_ids, chapter_numbers = set(), set()
    for chapter in book["chapters"]:
        if not isinstance(chapter, dict):
            fail("chapters must contain objects")
        for key in ("id", "number", "title", "urls", "topics"):
            if key not in chapter:
                fail(f"chapter is missing {key}")
        if not isinstance(chapter["id"], str) or not SLUG.fullmatch(chapter["id"]):
            fail("chapter IDs must be lowercase URL-safe identifiers")
        if not isinstance(chapter["number"], int) or isinstance(chapter["number"], bool) or chapter["number"] < 1:
            fail(f"chapter {chapter['id']} number must be a positive integer")
        if chapter["id"] in chapter_ids:
            fail(f"duplicate chapter id: {chapter['id']}")
        if chapter["number"] in chapter_numbers:
            fail(f"duplicate chapter number: {chapter['number']}")
        chapter_ids.add(chapter["id"]); chapter_numbers.add(chapter["number"])
        localized(chapter["title"], f"chapter {chapter['id']} title")
        if not isinstance(chapter["urls"], dict) or set(chapter["urls"]) != set(book["languages"]):
            fail(f"chapter {chapter['id']} URLs must match the book's available languages")
        for lang, url in chapter["urls"].items():
            check_url(url, f"chapter {chapter['id']} {lang} URL")
            if urlparse(url).netloc != urlparse(book["productionUrl"]).netloc:
                fail(f"chapter {chapter['id']} URL must use the book production host")
            if not path_is_within_production(urlparse(url).path, urlparse(book["productionUrl"]).path):
                fail(f"chapter {chapter['id']} URL must remain under the production path")
        if not isinstance(chapter["topics"], list) or any(not isinstance(t, str) for t in chapter["topics"]):
            fail(f"chapter {chapter['id']} topics must be a string list")
    if not isinstance(book["experiments"], list):
        fail("experiments must be a list")
    experiment_ids = set()
    for item in book["experiments"]:
        if not isinstance(item, dict) or not all(k in item for k in ("id", "title", "chapterId", "url", "kind")):
            fail("each experiment requires id, title, chapterId, url, and kind")
        if item["id"] in experiment_ids:
            fail(f"duplicate experiment id: {item['id']}")
        experiment_ids.add(item["id"])
        localized(item["title"], f"experiment {item['id']} title")
        localized(item["kind"], f"experiment {item['id']} kind")
        if item["chapterId"] not in chapter_ids:
            fail(f"experiment {item['id']} references unknown chapter {item['chapterId']}")
        check_url(item["url"], f"experiment {item['id']} URL")
        if urlparse(item["url"]).netloc != urlparse(book["productionUrl"]).netloc or not urlparse(item["url"]).fragment:
            fail(f"experiment {item['id']} must use the book host and include an anchor")
        if not path_is_within_production(urlparse(item["url"]).path, urlparse(book["productionUrl"]).path):
            fail(f"experiment {item['id']} URL must remain under the production path")
        verification = item.get("verification")
        if verification is not None:
            if not isinstance(verification, dict) or not all(isinstance(verification.get(key), str) and verification[key].strip() for key in ("checkedAt", "checkedUrl", "contentSha256", "sourceRevision", "sourceRevisionAttestation", "evidence")):
                fail(f"experiment {item['id']} verification requires checkedAt, checkedUrl, contentSha256, sourceRevision, sourceRevisionAttestation, and evidence")
            try:
                date.fromisoformat(verification["checkedAt"])
            except (ValueError, TypeError):
                fail(f"experiment {item['id']} verification.checkedAt must be an ISO date")
            check_url(verification["checkedUrl"], f"experiment {item['id']} verification.checkedUrl")
            if urlparse(verification["checkedUrl"]).netloc != urlparse(book["productionUrl"]).netloc or not path_is_within_production(urlparse(verification["checkedUrl"]).path, urlparse(book["productionUrl"]).path):
                fail(f"experiment {item['id']} verification.checkedUrl must remain under the production host and path")
            if verification["checkedUrl"] != item["url"] or verification.get("httpStatus") != 200 or verification.get("fragmentFound") is not True:
                fail(f"experiment {item['id']} verification must record a successful check of its exact URL and fragment")
    for field in ("prerequisites", "relatedBooks", "tags"):
        if not isinstance(book[field], list) or any(not isinstance(v, str) for v in book[field]):
            fail(f"{field} must be a string list")
    for field in ("relatedBooks", "prerequisites"):
        if book["id"] in book[field]:
            fail(f"a book cannot list itself in {field}")
    if not isinstance(book["cover"], str) or not book["cover"].startswith("assets/"):
        fail("cover must be a site-relative path under assets/")
    if not (ROOT / "site" / book["cover"]).is_file():
        fail(f"cover asset does not exist: site/{book['cover']}")
    if not isinstance(book["attribution"], dict) or not all(isinstance(book["attribution"].get(k), str) and book["attribution"][k].strip() for k in ("license", "repositoryUrl", "notes")):
        fail("attribution requires non-empty license, repositoryUrl, and notes")
    license_value = re.sub(r"[^a-z0-9]+", "", book["attribution"]["license"].casefold())
    unselected_licenses = {"chooseandrecord", "tbd", "todo", "none", "unlicensed", "nolicense", "nolicence", "notselected", "licensepending", "licencepending", "allrightsreserved"}
    if book["status"] == "published" and license_value in unselected_licenses:
        fail("published books require a selected license; attribution.license cannot be a placeholder or no-license statement")
    check_url(book["attribution"]["repositoryUrl"], "attribution.repositoryUrl")
    if not isinstance(book["theme"], dict) or not all(isinstance(book["theme"].get(k), str) for k in ("accent", "accentSoft", "motif")):
        fail("theme requires accent, accentSoft, and motif strings")
    for key in ("accent", "accentSoft"):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", book["theme"][key]):
            fail(f"theme.{key} must be a six-digit hex color")
    if book["status"] == "published":
        evidence = book.get("publicationEvidence")
        if not isinstance(evidence, dict) or not evidence.get("releaseUrl") or not evidence.get("siteVerification") or not evidence.get("chapterVerification") or not evidence.get("productionRevision"):
            fail("published status requires releaseUrl, productionRevision, siteVerification, and chapterVerification evidence")
        if not isinstance(evidence["productionRevision"], str) or not re.fullmatch(r"[0-9a-f]{40}", evidence["productionRevision"]):
            fail("publicationEvidence.productionRevision must be a full 40-character lowercase Git commit SHA")
        check_url(evidence["releaseUrl"], "publicationEvidence.releaseUrl")
        try:
            date.fromisoformat(evidence["releasePublishedAt"])
        except (ValueError, TypeError, KeyError):
            fail("publicationEvidence.releasePublishedAt must be an ISO date")
        if book["experiments"] and not evidence.get("experimentVerification"):
            fail("published manifests with experiments require experimentVerification evidence")
        for item in book["experiments"]:
            if item["verification"]["sourceRevision"] != evidence["productionRevision"]:
                fail(f"experiment {item['id']} evidence sourceRevision must match publicationEvidence.productionRevision")
    return book


def validate_reference_project(project_id):
    """Require a current, explicit differentiation decision before a new project is registered."""
    try:
        inventory = reference_gate.load_json(REFERENCE_INVENTORY)
        decisions = reference_gate.load_json(EDITORIAL_DECISIONS)
        return reference_gate.validate_project_gate(project_id, decisions, inventory)
    except (reference_gate.ReferenceError, OSError, json.JSONDecodeError) as exc:
        fail(f"reference/differentiation review gate: {exc}")


def validate_published_provenance(book):
    """Fail closed when a published catalog entry lacks reviewed rights/provenance records."""
    try:
        provenance = reference_gate.load_json(PROVENANCE_AUDIT)
        reference_gate.validate_provenance_records(provenance)
    except (reference_gate.ReferenceError, OSError, json.JSONDecodeError) as exc:
        fail(f"publication provenance gate: {exc}")
    record = next((work for work in provenance["works"] if work["workId"] == book["id"]), None)
    if record is None:
        fail(f"publication provenance gate: {book['id']} has no source/provenance audit record")
    if record["reviewStatus"] not in {"reviewed", "follow-up-required"}:
        fail(f"publication provenance gate: {book['id']} has unresolved review status")
    if any(str(finding.get("severity", "")).upper() in {"P0", "P1"} for finding in record["findings"]):
        fail(f"publication provenance gate: {book['id']} has an unresolved P0/P1 finding")
    if any(source.get("classification") == "license-uncertain" for source in record["reuseRecords"]):
        fail(f"publication provenance gate: {book['id']} has unresolved license uncertainty")


def all_books():
    books = []
    ids, slugs = set(), set()
    for path in sorted(MANIFESTS.glob("*.json")):
        book = validate_manifest(read_json(path))
        if book["id"] in ids:
            fail(f"duplicate book id: {book['id']}")
        if book["slug"] in slugs:
            fail(f"duplicate book slug: {book['slug']}")
        if path.stem != book["id"]:
            fail(f"manifest filename {path.name} must match id {book['id']}")
        ids.add(book["id"]); slugs.add(book["slug"]); books.append(book)
    by_id = {book["id"]: book for book in books}
    for book in books:
        references = set(book["relatedBooks"]) | set(book["prerequisites"])
        unknown = references - ids
        if unknown:
            fail(f"{book['id']} has unknown prerequisite/related book IDs: {', '.join(sorted(unknown))}")
        unpublished = sorted(book_id for book_id in references if by_id[book_id]["status"] != "published")
        if unpublished:
            fail(f"{book['id']} references books that are not published: {', '.join(unpublished)}")
        if book["status"] == "published":
            validate_published_provenance(book)
    return books


def validate_roadmap_group(items, group_name, registered_ids, minimum_fields=True):
    if not isinstance(items, list):
        fail(f"roadmap {group_name} must be a list")
    ids = set()
    for idea in items:
        if not isinstance(idea, dict) or not isinstance(idea.get("id"), str) or not idea["id"].strip() or idea["id"] in ids:
            fail(f"roadmap {group_name} IDs must be present and unique")
        if idea["id"] in registered_ids or idea.get("status") != "planned":
            fail(f"roadmap entry {idea['id']} must remain separate from registered books and marked planned")
        if not isinstance(idea.get("priority"), int) or isinstance(idea["priority"], bool) or idea["priority"] < 1:
            fail(f"roadmap entry {idea['id']} priority must be a positive integer")
        if idea.get("workState") not in (None, "active-project"):
            fail(f"roadmap entry {idea['id']} has an unsupported workState")
        for field in ("title", "subtitle", "audience", "relationships", "differentiation"):
            localized(idea.get(field), f"roadmap entry {idea['id']} {field}")
        for field in ("questions", "chapterGroups", "prerequisites", "simulatorIdeas"):
            localized_list(idea.get(field), f"roadmap entry {idea['id']} {field}")
        if minimum_fields:
            localized(idea.get("purpose"), f"roadmap entry {idea['id']} purpose")
        ids.add(idea["id"])
    return ids


def validate_math_prerequisite_graph(items):
    if not isinstance(items, list) or not items:
        fail("roadmap mathematicsBooks must be a non-empty list")
    ids = {item["id"] for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)}
    graph = {}
    for item in items:
        book_id = item.get("id")
        prerequisites = item.get("prerequisiteIds")
        if not isinstance(prerequisites, list) or any(not isinstance(value, str) or not value for value in prerequisites):
            fail(f"mathematics roadmap entry {book_id} requires a prerequisiteIds list of book IDs")
        if len(prerequisites) != len(set(prerequisites)):
            fail(f"mathematics roadmap entry {book_id} has duplicate prerequisite IDs")
        unknown = set(prerequisites) - ids
        if unknown:
            fail(f"mathematics roadmap entry {book_id} has unknown prerequisite IDs: {', '.join(sorted(unknown))}")
        if book_id in prerequisites:
            fail(f"mathematics roadmap entry {book_id} cannot depend on itself")
        graph[book_id] = prerequisites

    visiting, visited = set(), set()
    def visit(book_id):
        if book_id in visiting:
            fail(f"mathematics roadmap prerequisite cycle includes {book_id}")
        if book_id in visited:
            return
        visiting.add(book_id)
        for prerequisite_id in graph[book_id]:
            visit(prerequisite_id)
        visiting.remove(book_id)
        visited.add(book_id)
    for book_id in graph:
        visit(book_id)


def validate_learning_journey(books, roadmap, categories, journey):
    schema = read_json(ROOT / "schemas" / "learning-journey.schema.json")
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(journey))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "$"
        fail(f"learning journey schema validation at {location}: {first.message}")

    def unique_ids(items, label):
        ids = [item["id"] for item in items]
        if len(ids) != len(set(ids)):
            fail(f"learning journey {label} IDs must be unique")
        return set(ids)

    references = {item["id"]: item for item in journey["references"]}
    stages = {item["id"]: item for item in journey["stages"]}
    strands = {item["id"]: item for item in journey["strands"]}
    concepts = {item["id"]: item for item in journey["concepts"]}
    unique_ids(journey["references"], "reference")
    unique_ids(journey["stages"], "stage")
    unique_ids(journey["strands"], "strand")
    unique_ids(journey["concepts"], "concept")
    ordered_stages = sorted(journey["stages"], key=lambda item: item["order"])
    orders = [stage["order"] for stage in ordered_stages]
    if orders != list(range(1, len(orders) + 1)):
        fail("learning journey stage order must be unique and contiguous from 1")
    for stage in ordered_stages:
        age = stage["ageRange"]
        if age["max"] is not None and age["max"] < age["min"]:
            fail(f"learning journey stage {stage['id']} has an invalid age range")

    book_by_id = {book["id"]: book for book in books}
    chapter_ids = {book_id: {chapter["id"] for chapter in book["chapters"]} for book_id, book in book_by_id.items() if book["status"] == "published"}
    roadmap_ids = set()
    for group in ("books", "mathematicsBooks", "familyProjects"):
        group_ids = validate_roadmap_group(roadmap.get(group), group, set(book_by_id), minimum_fields=(group != "books"))
        duplicate = roadmap_ids & group_ids
        if duplicate:
            fail("roadmap IDs must be unique across sections: " + ", ".join(sorted(duplicate)))
        roadmap_ids.update(group_ids)
    if not any(item["id"] == "mathematics" for item in categories):
        fail("learning journey requires a Mathematics subject category")

    pair_keys = set()
    by_thread = {}
    for concept in journey["concepts"]:
        if concept["strandId"] not in strands:
            fail(f"concept {concept['id']} references unknown strand {concept['strandId']}")
        if concept["stageId"] not in stages:
            fail(f"concept {concept['id']} references unknown stage {concept['stageId']}")
        if concept["strandId"] == "mathematics" and concept["stageId"] == "university-advanced" and not concept["plannedBookIds"]:
            fail("advanced mathematics concept must link to a planned mathematics title")
        pair = (concept["stageId"], concept["strandId"])
        if pair in pair_keys:
            fail(f"duplicate stage/strand concept entry: {pair[0]}/{pair[1]}")
        pair_keys.add(pair)
        for source_id in concept["sourceIds"]:
            if source_id not in references:
                fail(f"concept {concept['id']} references unknown source {source_id}")
        for book_id in concept["plannedBookIds"]:
            if book_id not in roadmap_ids:
                fail(f"concept {concept['id']} references unknown planned title {book_id}")
        for material in concept["publishedMaterials"]:
            material_book = book_by_id.get(material["bookId"])
            if not material_book or material_book["status"] != "published" or material["chapterId"] not in chapter_ids.get(material["bookId"], set()):
                fail(f"concept {concept['id']} references an unpublished book or unknown chapter")
        thread = by_thread.setdefault(concept["threadId"], {"strandId": concept["strandId"], "title": concept["threadTitle"], "concepts": []})
        if thread["strandId"] != concept["strandId"] or thread["title"] != concept["threadTitle"]:
            fail(f"learning thread {concept['threadId']} must keep one strand and bilingual title")
        thread["concepts"].append(concept)

    expected_pairs = {(stage_id, strand_id) for stage_id in stages for strand_id in strands}
    if pair_keys != expected_pairs:
        missing = sorted(f"{stage}/{strand}" for stage, strand in expected_pairs - pair_keys)
        fail("learning journey needs one representative concept for every stage/strand pair; missing " + ", ".join(missing))

    graph = {concept_id: concept["prerequisites"] for concept_id, concept in concepts.items()}
    for concept in journey["concepts"]:
        earlier = stages[concept["stageId"]]["order"]
        for dependency_id in concept["prerequisites"]:
            if dependency_id not in concepts:
                fail(f"concept {concept['id']} has unknown prerequisite {dependency_id}")
            if dependency_id == concept["id"]:
                fail(f"concept {concept['id']} cannot depend on itself")
            if stages[concepts[dependency_id]["stageId"]]["order"] > earlier:
                fail(f"concept {concept['id']} cannot depend on a later stage")
        revisits = concept["revisits"]
        if revisits is not None:
            prior = concepts.get(revisits)
            if not prior:
                fail(f"concept {concept['id']} revisits must name an existing concept")
            if prior["threadId"] != concept["threadId"] or prior["depth"] >= concept["depth"] or stages[prior["stageId"]]["order"] >= earlier:
                fail(f"concept {concept['id']} revisits must point to an earlier depth in the same thread")
        if not isinstance(concept["depth"], int) or isinstance(concept["depth"], bool):
            fail(f"concept {concept['id']} depth must be an integer")

    visiting, visited = set(), set()
    def visit(concept_id):
        if concept_id in visiting:
            fail(f"learning journey prerequisite cycle includes {concept_id}")
        if concept_id in visited:
            return
        visiting.add(concept_id)
        for dependency_id in graph[concept_id]:
            visit(dependency_id)
        visiting.remove(concept_id)
        visited.add(concept_id)
    for concept_id in concepts:
        visit(concept_id)

    for thread_id, thread in by_thread.items():
        ordered = sorted(thread["concepts"], key=lambda item: stages[item["stageId"]]["order"])
        seen_depths = set()
        prior_order, prior_depth = 0, 0
        for concept in ordered:
            order = stages[concept["stageId"]]["order"]
            if order <= prior_order or concept["depth"] <= prior_depth or concept["depth"] in seen_depths:
                fail(f"learning thread {thread_id} must increase stage and depth without duplicates")
            seen_depths.add(concept["depth"])
            prior_order, prior_depth = order, concept["depth"]


def validate_kids_family(data, journey, books, roadmap):
    schema = read_json(ROOT / "schemas" / "kids-family.schema.json")
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "$"
        fail(f"Kids & Family schema validation at {location}: {first.message}")

    def unique_ids(items, label):
        ids = [item["id"] for item in items]
        if len(ids) != len(set(ids)):
            fail(f"Kids & Family {label} IDs must be unique")
        return set(ids)

    interest_ids = unique_ids(data["interests"], "interest")
    theme_ids = unique_ids(data["themes"], "theme")
    story_ids = unique_ids(data["stories"], "story")
    reference_ids = unique_ids(data["references"], "reference")
    proposal_ids = unique_ids(data["proposals"], "family proposal")
    registered_ids = {book["id"] for book in books}
    roadmap_ids = {item["id"] for group in ("books", "mathematicsBooks", "familyProjects") for item in roadmap[group]}
    if data["pilot"]["id"] in registered_ids or data["pilot"]["id"] in roadmap_ids:
        fail("Kids & Family editorial pilot must stay outside the book catalog and roadmap")
    expected_proposals = {"heavyvehiclebook", "carbook", "dinosaurbook", "animalbook", "robotbook"}
    if proposal_ids != expected_proposals:
        fail("Kids & Family must define the five scoped editorial proposals without expanding the published catalog")
    if any(proposal_id in registered_ids or proposal_id in roadmap_ids for proposal_id in proposal_ids):
        fail("Kids & Family proposals must stay outside the book catalog and roadmap")
    if not any(item["id"] == data["pilot"]["id"] and item["status"] == "editorial-pilot" for item in data["proposals"]):
        fail("Kids & Family pilot must appear as the HeavyVehicleBook editorial-pilot proposal")
    for proposal in data["proposals"]:
        if set(proposal["interestIds"]) - interest_ids:
            fail(f"Kids & Family proposal {proposal['id']} references an unknown interest")

    concepts = {item["id"]: item for item in journey["concepts"]}
    stages = {item["id"]: item for item in journey["stages"]}
    ordered_stages = sorted(journey["stages"], key=lambda item: item["order"])
    themes = {item["id"]: item for item in data["themes"]}
    stories = {item["id"]: item for item in data["stories"]}
    used_references = set()
    scene_ids = []

    for theme in data["themes"]:
        unknown_interests = set(theme["interestIds"]) - interest_ids
        if unknown_interests:
            fail(f"Kids & Family theme {theme['id']} references unknown interests: {', '.join(sorted(unknown_interests))}")
        story = stories.get(theme["storyId"])
        if not story or story["themeId"] != theme["id"]:
            fail(f"Kids & Family theme {theme['id']} must point to its matching story")
        seeds = [concepts.get(concept_id) for concept_id in theme["conceptIds"]]
        if any(concept is None for concept in seeds):
            fail(f"Kids & Family theme {theme['id']} references an unknown Learning Journey concept")
        if any(concept["stageId"] != "preschool" for concept in seeds):
            fail(f"Kids & Family theme {theme['id']} must start from relevant preschool concept IDs")
        strands = [concept["strandId"] for concept in seeds]
        if len(strands) != len(set(strands)):
            fail(f"Kids & Family theme {theme['id']} should map each starting concept to a distinct subject strand")

        # Stage navigation follows only the Learning Journey's existing explicit revisit links.
        for seed in seeds:
            current = seed
            for stage in ordered_stages:
                if current["stageId"] != stage["id"]:
                    successors = [item for item in journey["concepts"] if item["revisits"] == current["id"]]
                    if len(successors) != 1 or successors[0]["stageId"] != stage["id"]:
                        fail(f"Kids & Family concept {current['id']} has no unique explicit continuation to {stage['id']}")
                    current = successors[0]

    for story in data["stories"]:
        theme = themes.get(story["themeId"])
        if not theme or theme["storyId"] != story["id"]:
            fail(f"Kids & Family story {story['id']} must belong to its matching theme")
        for page in story["pages"]:
            scene_ids.append(page["sceneId"])
        unknown_references = set(story["referenceIds"]) - reference_ids
        if unknown_references:
            fail(f"Kids & Family story {story['id']} references unknown sources: {', '.join(sorted(unknown_references))}")
        used_references.update(story["referenceIds"])
    if len(scene_ids) != len(set(scene_ids)):
        fail("Kids & Family illustration scene IDs must be unique")
    if used_references != reference_ids:
        fail("Kids & Family references must be used by at least one story")


def validate_discovery_indexes(books, indexes):
    for name in ("categories", "learning-paths", "roadmap", "learning-journey", "kids-family"):
        if not isinstance(indexes.get(name), dict):
            fail(f"catalog/{name}.json must contain an object")
    published = {book["id"]: book for book in books if book["status"] == "published"}
    categories = indexes["categories"].get("categories")
    if not isinstance(categories, list):
        fail("catalog/categories.json must contain a categories list")
    category_ids = [category.get("id") for category in categories if isinstance(category, dict)]
    if len(category_ids) != len(categories) or len(set(category_ids)) != len(category_ids):
        fail("category IDs must be present and unique")
    for category in categories:
        if not isinstance(category.get("id"), str) or not category["id"].strip():
            fail("category IDs must be non-empty strings")
        localized(category.get("name"), f"category {category['id']} name")
        localized(category.get("description"), f"category {category['id']} description")
        if not isinstance(category.get("color"), str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", category["color"]):
            fail(f"category {category['id']} color must be a six-digit hex color")
        if not isinstance(category.get("map"), list):
            fail(f"category {category['id']} map must be a list")
        seen_nodes = set()
        for node in category.get("map", []):
            if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"].strip() or node["id"] in seen_nodes:
                fail(f"{category['id']} map nodes must have unique IDs")
            seen_nodes.add(node["id"])
            localized(node.get("label"), f"{category['id']}/{node['id']} label")
            if not isinstance(node.get("topics"), list) or any(not isinstance(topic, str) or not topic.strip() for topic in node["topics"]):
                fail(f"{category['id']}/{node['id']} topics must be a list of non-empty strings")
            if not isinstance(node.get("connections"), list):
                fail(f"{category['id']}/{node['id']} connections must be a list")
            for connection in node.get("connections", []):
                if not isinstance(connection, dict) or not all(isinstance(connection.get(key), str) and connection[key] for key in ("bookId", "chapterId")):
                    fail(f"{category['id']}/{node['id']} map connection requires bookId and chapterId")
                book = published.get(connection["bookId"])
                if not book or book["category"] != category["id"]:
                    fail(f"{category['id']}/{node['id']} connection must reference a published book in that category")
                if connection["chapterId"] not in {chapter["id"] for chapter in book["chapters"]}:
                    fail(f"{category['id']}/{node['id']} references unknown chapter {connection['chapterId']}")

    learning_paths = indexes["learning-paths"].get("paths")
    if not isinstance(learning_paths, list):
        fail("catalog/learning-paths.json must contain a paths list")
    path_ids = set()
    for path in learning_paths:
        if not isinstance(path, dict) or not isinstance(path.get("id"), str) or not path["id"].strip() or path["id"] in path_ids:
            fail("learning-path IDs must be present and unique")
        path_ids.add(path["id"])
        localized(path.get("title"), f"learning path {path['id']} title")
        localized(path.get("audience"), f"learning path {path['id']} audience")
        localized(path.get("outcome"), f"learning path {path['id']} outcome")
        if not isinstance(path.get("steps"), list) or not path["steps"]:
            fail(f"learning path {path['id']} must contain at least one step")
        for step in path.get("steps", []):
            if not isinstance(step, dict) or not all(isinstance(step.get(key), str) and step[key] for key in ("bookId", "chapterId")):
                fail(f"learning path {path['id']} step requires bookId and chapterId")
            localized(step.get("why"), f"learning path {path['id']} step rationale")
            book = published.get(step["bookId"])
            if not book or step["chapterId"] not in {chapter["id"] for chapter in book["chapters"]}:
                fail(f"learning path {path['id']} references an unpublished or unknown chapter")

    roadmap = indexes["roadmap"].get("books")
    if not isinstance(roadmap, list):
        fail("catalog/roadmap.json must contain a books list")
    validate_roadmap_group(roadmap, "books", {book["id"] for book in books}, minimum_fields=False)
    validate_roadmap_group(indexes["roadmap"].get("mathematicsBooks"), "mathematicsBooks", {book["id"] for book in books})
    validate_math_prerequisite_graph(indexes["roadmap"].get("mathematicsBooks"))
    validate_roadmap_group(indexes["roadmap"].get("familyProjects"), "familyProjects", {book["id"] for book in books})
    all_roadmap_ids = [idea["id"] for key in ("books", "mathematicsBooks", "familyProjects") for idea in indexes["roadmap"].get(key, [])]
    if len(all_roadmap_ids) != len(set(all_roadmap_ids)):
        fail("roadmap IDs must be unique across sections")
    validate_learning_journey(books, indexes["roadmap"], categories, indexes["learning-journey"])
    validate_kids_family(indexes["kids-family"], indexes["learning-journey"], books, indexes["roadmap"])
    product_specific = indexes["roadmap"].get("productSpecific")
    if not isinstance(product_specific, dict) or product_specific.get("status") != "editorial-space":
        fail("roadmap productSpecific must remain an editorial-space")
    localized(product_specific.get("title"), "roadmap productSpecific title")
    localized(product_specific.get("description"), "roadmap productSpecific description")


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        stream.write(content); temp = Path(stream.name)
    temp.replace(path)


def derived_indexes():
    books = all_books()
    indexes = {source: read_json(ROOT / "catalog" / f"{source}.json") for source in ("categories", "roadmap", "learning-paths", "learning-journey", "kids-family")}
    validate_discovery_indexes(books, indexes)
    return {"books": books, **indexes}


def index_content(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def check_indexes():
    expected = derived_indexes()
    stale = []
    for name, content in expected.items():
        path = DATA / f"{name}.json"
        if not path.is_file() or path.read_text(encoding="utf-8") != index_content(content):
            stale.append(display_path(path))
    unexpected = sorted(display_path(path) for path in DATA.glob("*.json") if path.stem not in expected)
    if stale or unexpected:
        pieces = []
        if stale:
            pieces.append("stale or missing generated indexes: " + ", ".join(stale))
        if unexpected:
            pieces.append("unexpected generated data files: " + ", ".join(unexpected))
        fail("; ".join(pieces) + "; run python3 tools/book_factory.py generate")
    print(f"Validated {len(expected['books'])} book manifest(s): {sum(b['status'] == 'published' for b in expected['books'])} published; generated indexes are current.")


def generate():
    expected = derived_indexes()
    DATA.mkdir(parents=True, exist_ok=True)
    for name, data in expected.items():
        atomic_json(DATA / f"{name}.json", data)
    print(f"Generated validated indexes for {len(expected['books'])} book manifest(s): {sum(b['status'] == 'published' for b in expected['books'])} published.")


def register(source: Path, update: bool):
    incoming = validate_manifest(read_json(source))
    target = MANIFESTS / f"{incoming['id']}.json"
    if target.exists() and not update:
        fail(f"{display_path(target)} already exists; use update explicitly")
    if update and not target.exists():
        fail(f"cannot update absent record: {display_path(target)}")
    current = read_json(target) if update else None
    if update:
        if current.get("id") != incoming["id"]:
            fail("update cannot change a record's id")
    needs_differentiation_review = (
        incoming["status"] == "in-progress" and (not update or current.get("status") in {"planned", "archived"})
    ) or (
        incoming["status"] == "published" and (not update or current.get("status") != "published")
    )
    if needs_differentiation_review:
        validate_reference_project(incoming["id"])
    if incoming["status"] == "published":
        validate_published_provenance(incoming)
    for other_path in MANIFESTS.glob("*.json"):
        if other_path == target:
            continue
        other = read_json(other_path)
        if other.get("id") == incoming["id"] or other.get("slug") == incoming["slug"]:
            fail(f"duplicate id or slug conflicts with {other_path.name}")
    if incoming["status"] == "published" and not incoming.get("publicationEvidence"):
        fail("registering a published book requires explicit publication evidence")
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    atomic_json(target, incoming)
    try:
        generate()
    except Exception:
        if update:
            atomic_json(target, current)
        else:
            target.unlink(missing_ok=True)
        generate()
        raise
    print(f"Registered {incoming['id']} at {display_path(target)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate manifests and confirm checked-in indexes are current without writing")
    sub.add_parser("check-indexes", help="validate manifests and compare derived indexes without writing")
    sub.add_parser("generate", help="validate manifests and write derived indexes")
    add = sub.add_parser("register", help="register a new validated manifest")
    add.add_argument("manifest", type=Path)
    update = sub.add_parser("update", help="replace one existing manifest by its stable id")
    update.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        if args.command in {"validate", "check-indexes"}: check_indexes()
        elif args.command == "generate": generate()
        else: register(args.manifest.resolve(), args.command == "update")
    except (ManifestError, OSError, json.JSONDecodeError) as exc:
        print(f"book_factory: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
