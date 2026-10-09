#!/usr/bin/env python3
"""Validate and safely register independently published textbook manifests."""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "catalog" / "books"
DATA = ROOT / "site" / "data"
SCHEMA = ROOT / "schemas" / "book.schema.json"
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
    try:
        date.fromisoformat(book["lastUpdated"])
    except (ValueError, TypeError):
        fail("lastUpdated must be an ISO date")
    if not isinstance(book["chapters"], list):
        fail("chapters must be a list")
    if not isinstance(book["chapterCount"], int) or isinstance(book["chapterCount"], bool) or book["chapterCount"] != len(book["chapters"]):
        fail("chapterCount must equal the length of chapters")
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
            production_path = urlparse(book["productionUrl"]).path.rstrip("/") + "/"
            if not urlparse(url).path.startswith(production_path):
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
            fail(f"experiment {item['id']} must use the book host and include a verified anchor")
        production_path = urlparse(book["productionUrl"]).path.rstrip("/") + "/"
        if not urlparse(item["url"]).path.startswith(production_path):
            fail(f"experiment {item['id']} URL must remain under the production path")
    for field in ("prerequisites", "relatedBooks", "tags"):
        if not isinstance(book[field], list) or any(not isinstance(v, str) for v in book[field]):
            fail(f"{field} must be a string list")
    for rel in book["relatedBooks"]:
        if rel == book["id"]:
            fail("a book cannot relate to itself")
    if not isinstance(book["cover"], str) or not book["cover"].startswith("assets/"):
        fail("cover must be a site-relative path under assets/")
    if not (ROOT / "site" / book["cover"]).is_file():
        fail(f"cover asset does not exist: site/{book['cover']}")
    if not isinstance(book["attribution"], dict) or not all(isinstance(book["attribution"].get(k), str) and book["attribution"][k].strip() for k in ("license", "repositoryUrl", "notes")):
        fail("attribution requires non-empty license, repositoryUrl, and notes")
    check_url(book["attribution"]["repositoryUrl"], "attribution.repositoryUrl")
    if not isinstance(book["theme"], dict) or not all(isinstance(book["theme"].get(k), str) for k in ("accent", "accentSoft", "motif")):
        fail("theme requires accent, accentSoft, and motif strings")
    for key in ("accent", "accentSoft"):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", book["theme"][key]):
            fail(f"theme.{key} must be a six-digit hex color")
    if book["status"] == "published":
        evidence = book.get("publicationEvidence")
        if not isinstance(evidence, dict) or not evidence.get("releaseUrl") or not evidence.get("siteVerification") or not evidence.get("chapterVerification"):
            fail("published status requires releaseUrl, siteVerification, and chapterVerification evidence")
        check_url(evidence["releaseUrl"], "publicationEvidence.releaseUrl")
        try:
            date.fromisoformat(evidence["releasePublishedAt"])
        except (ValueError, TypeError, KeyError):
            fail("publicationEvidence.releasePublishedAt must be an ISO date")
        if book["experiments"] and not evidence.get("experimentVerification"):
            fail("published manifests with experiments require experimentVerification evidence")
    return book


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
    return books


def validate_discovery_indexes(books, indexes):
    for name in ("categories", "learning-paths", "roadmap"):
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
    roadmap_ids = set()
    for idea in roadmap:
        if not isinstance(idea, dict) or not isinstance(idea.get("id"), str) or not idea["id"].strip() or idea["id"] in roadmap_ids:
            fail("roadmap IDs must be present and unique")
        if idea["id"] in {book["id"] for book in books} or idea.get("status") != "planned":
            fail(f"roadmap entry {idea['id']} must remain separate from registered books and marked planned")
        if not isinstance(idea.get("priority"), int) or isinstance(idea["priority"], bool) or idea["priority"] < 1:
            fail(f"roadmap entry {idea['id']} priority must be a positive integer")
        for field in ("title", "subtitle", "audience", "relationships", "differentiation"):
            localized(idea.get(field), f"roadmap entry {idea['id']} {field}")
        for field in ("questions", "chapterGroups", "prerequisites", "simulatorIdeas"):
            localized_list(idea.get(field), f"roadmap entry {idea['id']} {field}")
        roadmap_ids.add(idea["id"])
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


def generate():
    books = all_books()
    indexes = {source: read_json(ROOT / "catalog" / f"{source}.json") for source in ("categories", "roadmap", "learning-paths")}
    validate_discovery_indexes(books, indexes)
    DATA.mkdir(parents=True, exist_ok=True)
    atomic_json(DATA / "books.json", books)
    for source, index in indexes.items():
        atomic_json(DATA / f"{source}.json", index)
    print(f"Validated {len(books)} book manifest(s): {sum(b['status'] == 'published' for b in books)} published; wrote site/data indexes.")


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
    validate = sub.add_parser("validate", help="validate every manifest and regenerate derived indexes")
    add = sub.add_parser("register", help="register a new validated manifest")
    add.add_argument("manifest", type=Path)
    update = sub.add_parser("update", help="replace one existing manifest by its stable id")
    update.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "validate": generate()
        else: register(args.manifest.resolve(), args.command == "update")
    except (ManifestError, OSError, json.JSONDecodeError) as exc:
        print(f"book_factory: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
