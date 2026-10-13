#!/usr/bin/env python3
"""Inventory upstream book metadata and report incremental source changes.

This tool reads public GitHub metadata only. It never executes files from a
reference repository, stores complete chapters, or makes editorial decisions.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import zlib
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "catalog" / "reference-intelligence"
INVENTORY_PATH = DATA_DIR / "inventory.json"
REVIEWS_PATH = DATA_DIR / "editorial-decisions.json"
PROVENANCE_PATH = DATA_DIR / "provenance-audit.json"
UPSTREAM_OWNER = "geniuskey"
UPSTREAM_REPO = "books"
API_ROOT = "https://api.github.com"
RAW_ROOT = "https://raw.githubusercontent.com"
API_VERSION = "2022-11-28"
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_RAW_BYTES = 65536
MAX_CATALOG_BYTES = 1024 * 1024
MAX_RETRIES = 3
TIMEOUT_SECONDS = 20
MAX_RATE_LIMIT_WAIT_SECONDS = 600
INTERESTING_EXTENSIONS = {".html", ".htm", ".md", ".mdx", ".json", ".js", ".mjs", ".py", ".svg"}
LICENSE_NAME = re.compile(r"(^|/)(license|licence)([-_.][^/]*)?$", re.IGNORECASE)
CHAPTER_DIR = re.compile(r"(^|/)(chapters?|lessons?)/", re.IGNORECASE)
SIMULATOR_PATH = re.compile(r"(^|/)(sims?|simulators?|experiments?|labs?)(/|\.|$)|(^|/)(sims?|experiments?)\.[^.]+$", re.IGNORECASE)
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
HEX_SHA = re.compile(r"^[0-9a-f]{40}$")
ISSUE_MARKER = "<!-- my-library-reference-intelligence-state-v1 -->"
DELTA_MARKER_RE = re.compile(r"<!-- MY_LIBRARY_REFERENCE_DELTA_V1:([0-9a-f]{64}) -->")
STATE_MARKER_RE = re.compile(r"<!-- MY_LIBRARY_REFERENCE_CHECKPOINT_V1:([0-9a-f]{64}):(\d+):(\d+) -->")
CHECKPOINT_CHUNK_CHARS = 45000
MAX_CHECKPOINT_CHUNKS = 12
MAX_CHECKPOINT_JSON_BYTES = 4 * 1024 * 1024
MAX_TRACKER_BODY_CHARS = 40000
MAX_REPORTED_CHANGES = 60
DECISIONS = {
    "reference-only", "companion-book", "adapt-and-extend",
    "original-deeper-treatment", "defer-or-cancel",
}
REUSE_CLASSES = {
    "original", "reference-only", "cc-by-4.0-adaptation", "mit-code-reuse",
    "third-party-material", "license-uncertain",
}


def rate_limit_wait_seconds(status: int, headers, body: str, attempt: int) -> int | None:
    """Return a bounded GitHub rate-limit delay; None means this is not a limit response."""
    remaining = headers.get("X-RateLimit-Remaining")
    retry_after = headers.get("Retry-After")
    message = body.casefold()
    primary = status == 403 and remaining == "0"
    secondary = status == 429 or (status == 403 and (retry_after is not None or "secondary rate limit" in message or "abuse detection" in message))
    if not primary and not secondary:
        return None
    delay = None
    if primary:
        reset = headers.get("X-RateLimit-Reset")
        if reset:
            try:
                delay = max(1, int(reset) - int(time.time()))
            except (TypeError, ValueError):
                delay = None
    if delay is None and retry_after is not None:
        try:
            delay = max(1, int(retry_after))
        except (TypeError, ValueError):
            delay = None
    if delay is None:
        # GitHub advises at least one minute for secondary limits when no
        # Retry-After header is supplied; increase the wait across retries.
        delay = 60 * (2 ** attempt)
    if delay > MAX_RATE_LIMIT_WAIT_SECONDS:
        raise ReferenceError(f"GitHub rate limit requires waiting {delay}s, beyond this workflow's {MAX_RATE_LIMIT_WAIT_SECONDS}s retry bound; rerun after the indicated reset")
    return delay


class ReferenceError(ValueError):
    """A validation, upstream-data, or bounded-fetch error."""


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if self.token is None:
            try:
                result = subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True, timeout=5)
                self.token = result.stdout.strip() or None
            except (OSError, subprocess.SubprocessError):
                self.token = None

    def get(self, url: str, *, raw: bool = False, max_bytes: int = MAX_JSON_BYTES):
        parsed = urlparse(url)
        allowed = {"api.github.com"} if not raw else {"raw.githubusercontent.com"}
        try:
            port = parsed.port
        except ValueError as exc:
            raise ReferenceError(f"refusing malformed GitHub source URL: {url}") from exc
        if parsed.scheme != "https" or parsed.hostname not in allowed or parsed.username or parsed.password or port not in (None, 443) or parsed.fragment:
            raise ReferenceError(f"refusing non-GitHub source URL: {url}")
        headers = {"User-Agent": "My-Library-Reference-Intelligence/1.0"}
        if raw:
            headers["Range"] = f"bytes=0-{max_bytes - 1}"
            headers["Accept"] = "text/plain, text/html, application/json;q=0.9, */*;q=0.5"
        else:
            headers["Accept"] = "application/vnd.github+json"
            headers["X-GitHub-Api-Version"] = API_VERSION
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
        for attempt in range(MAX_RETRIES):
            try:
                with urlopen(Request(url, headers=headers), timeout=TIMEOUT_SECONDS) as response:
                    data = response.read(max_bytes + 1)
                    if len(data) > max_bytes:
                        raise ReferenceError(f"response exceeds {max_bytes} byte limit: {url}")
                    return response.status, data, dict(response.headers)
            except HTTPError as exc:
                if exc.code == 404:
                    return 404, b"", dict(exc.headers)
                if exc.code == 304:
                    return 304, b"", dict(exc.headers)
                detail = exc.read(2048).decode("utf-8", "replace")
                rate_wait = rate_limit_wait_seconds(exc.code, exc.headers, detail, attempt)
                retryable = rate_wait is not None or exc.code >= 500
                if not retryable or attempt == MAX_RETRIES - 1:
                    raise ReferenceError(f"GitHub HTTP {exc.code} for {url}: {detail[:400]}") from exc
                delay = rate_wait if rate_wait is not None else 2 ** attempt
                time.sleep(delay)
            except (TimeoutError, URLError) as exc:
                if attempt == MAX_RETRIES - 1:
                    raise ReferenceError(f"GitHub request failed for {url}: {exc}") from exc
                time.sleep(2 ** attempt)
        raise ReferenceError(f"unreachable retry state for {url}")

    def json(self, url: str, *, max_bytes: int = MAX_JSON_BYTES):
        status, body, _ = self.get(url, max_bytes=max_bytes)
        if status != 200:
            return status, None
        try:
            return status, json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReferenceError(f"invalid JSON from {url}: {exc}") from exc

    def raw(self, url: str, *, max_bytes: int = MAX_RAW_BYTES):
        status, body, _ = self.get(url, raw=True, max_bytes=max_bytes)
        if status == 404:
            return None
        if status not in (200, 206):
            raise ReferenceError(f"unexpected HTTP {status} fetching {url}")
        return body.decode("utf-8", "replace")


class ChapterTitleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.in_h1 = False
        self.title_parts: list[str] = []
        self.h1_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "h1":
            self.in_h1 = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False
        elif tag.lower() == "h1":
            self.in_h1 = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        if self.in_h1:
            self.h1_parts.append(data)


def clean_text(value: str, limit: int = 300) -> str:
    value = html.unescape(re.sub(r"\s+", " ", value)).strip()
    return value[:limit]


def _plain_markdown_text(value) -> str:
    """Escape upstream-controlled plain text before placing it in Markdown."""
    value = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    value = re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", value)
    return value


def _inline_code(value) -> str:
    """Use a code span delimiter longer than any upstream backtick run."""
    value = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    runs = [len(match.group(0)) for match in re.finditer(r"`+", value)]
    fence = "`" * (max(runs, default=0) + 1)
    padding = " " if value.startswith(("`", " ")) or value.endswith(("`", " ")) else ""
    return f"{fence}{padding}{value}{padding}{fence}"


def _bounded_report_text(value: str, limit: int, message: str) -> str:
    if len(value) <= limit:
        return value
    suffix = "\n\n" + message + "\n"
    visible = value[:max(0, limit - len(suffix))].rsplit("\n", 1)[0]
    return visible + suffix


def chapter_title(client: GitHubClient, raw_url: str, fallback: str) -> tuple[str, str]:
    page = client.raw(raw_url, max_bytes=MAX_RAW_BYTES)
    if page:
        parser = ChapterTitleParser()
        try:
            parser.feed(page)
        except (ValueError, AssertionError):
            return fallback, "path-derived-fallback-parse-error"
        title = clean_text(" ".join(parser.h1_parts) or " ".join(parser.title_parts), 180)
        if title:
            return title, "html-heading-or-title"
    return fallback, "path-derived-fallback"


def api_url(path: str) -> str:
    return API_ROOT + path


def raw_url(repo: str, revision: str, path: str) -> str:
    encoded_path = "/".join(quote(segment, safe="@-._~") for segment in path.split("/"))
    return f"{RAW_ROOT}/{repo}/{revision}/{encoded_path}"


def git_blob_sha(data: bytes) -> str:
    """Return the Git object SHA for raw file bytes without storing the file."""
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def parse_json_bytes(data: bytes, source: str):
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReferenceError(f"{source} JSON is malformed: {exc}") from exc


def validate_upstream_catalog(value) -> list[dict]:
    """Validate untrusted central-catalog structure before any row is accessed."""
    if not isinstance(value, dict):
        raise ReferenceError("central catalog root must be a JSON object")
    records = value.get("books")
    if not isinstance(records, list) or len(records) > 1000:
        raise ReferenceError("central catalog book list is missing or exceeds the 1000-entry limit")
    seen = set()
    optional_strings = ("subtitle", "status", "field", "level")
    for index, row in enumerate(records):
        if not isinstance(row, dict):
            raise ReferenceError(f"central catalog book at index {index} must be an object")
        book_id = row.get("id")
        if not isinstance(book_id, str) or not SAFE_ID.fullmatch(book_id) or book_id in seen:
            raise ReferenceError(f"central catalog book at index {index} has an invalid or duplicate ID")
        seen.add(book_id)
        if not isinstance(row.get("title"), str) or not row["title"].strip():
            raise ReferenceError(f"central catalog book {book_id} requires a non-empty string title")
        for field in optional_strings:
            if field in row and not isinstance(row[field], str):
                raise ReferenceError(f"central catalog book {book_id} field {field} must be a string")
        for field in ("repo", "url"):
            if field in row and row[field] is not None and not isinstance(row[field], str):
                raise ReferenceError(f"central catalog book {book_id} field {field} must be a string or null")
        if row.get("status") == "published" and repository_from_url(row.get("repo")) is None:
            raise ReferenceError(f"published catalog book {book_id} requires a supported HTTPS repository URL under {UPSTREAM_OWNER}")
        topics = row.get("topics", [])
        if not isinstance(topics, list) or len(topics) > 80 or any(not isinstance(item, str) for item in topics):
            raise ReferenceError(f"central catalog book {book_id} topics must be a bounded list of strings")
        featured = row.get("featured", [])
        if not isinstance(featured, list) or len(featured) > 100:
            raise ReferenceError(f"central catalog book {book_id} featured entries must be a bounded list")
        for featured_index, item in enumerate(featured):
            if not isinstance(item, dict):
                raise ReferenceError(f"central catalog book {book_id} featured entry {featured_index} must be an object")
            if not isinstance(item.get("link"), str) or not item["link"].strip():
                raise ReferenceError(f"central catalog book {book_id} featured entry {featured_index} requires a link string")
            if "title" in item and not isinstance(item["title"], str):
                raise ReferenceError(f"central catalog book {book_id} featured entry {featured_index} title must be a string")
        for field in ("chapters", "simulators"):
            count = row.get(field)
            if count is not None and (not isinstance(count, int) or isinstance(count, bool) or count < 0):
                raise ReferenceError(f"central catalog book {book_id} field {field} must be a non-negative integer or null")
    return records


def repository_from_url(value: str | None) -> tuple[str, str] | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    try:
        port = parsed.port
    except ValueError:
        return None
    if (parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username
            or parsed.password or port not in (None, 443) or parsed.query or parsed.fragment):
        return None
    pieces = [piece for piece in parsed.path.strip("/").split("/") if piece]
    if len(pieces) != 2 or pieces[0].casefold() != UPSTREAM_OWNER or not SAFE_ID.fullmatch(pieces[1].casefold()):
        return None
    return pieces[0], pieces[1]


def compact_topics(record: dict) -> list[str]:
    values = record.get("topics", [])
    if not isinstance(values, list):
        return []
    return [clean_text(str(value), 180) for value in values[:80] if str(value).strip()]


def list_commit(client: GitHubClient, repo: str) -> dict:
    status, data = client.json(api_url(f"/repos/{repo}/commits?per_page=1"), max_bytes=512 * 1024)
    if status == 404:
        return {"available": False, "reason": "not-found-or-no-public-access"}
    if not isinstance(data, list) or not data:
        raise ReferenceError(f"missing head commit list for {repo}")
    commit = data[0]
    sha = commit.get("sha")
    if not isinstance(sha, str) or not HEX_SHA.fullmatch(sha):
        raise ReferenceError(f"invalid head commit SHA for {repo}")
    commit_data = commit.get("commit", {})
    author = commit_data.get("author", {})
    committer = commit_data.get("committer", {})
    return {
        "available": True,
        "headSha": sha,
        "headCommittedAt": committer.get("date") or author.get("date"),
        "headCommitMessage": clean_text(commit_data.get("message", "").splitlines()[0], 180),
        "commitUrl": commit.get("html_url"),
    }


def decode_license(client: GitHubClient, repo: str, revision: str, paths: list[str], repo_metadata: dict, source_map: dict[str, dict]) -> dict:
    matches = sorted(path for path in paths if LICENSE_NAME.search(path.rsplit("/", 1)[-1]))
    notices = sorted(path for path in paths if file_kind(path) == "rights-notice")
    files = []
    snippets: list[dict] = []
    for path in matches:
        text = client.raw(raw_url(repo, revision, path), max_bytes=MAX_RAW_BYTES)
        if text is None:
            continue
        file_item = {
            "path": path,
            "url": f"https://github.com/{repo}/blob/{revision}/{path}",
            "blobSha": source_map.get(path, {}).get("blobSha"),
            "sha256OfReadPrefix": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "readBytesCapped": len(text.encode("utf-8")) >= MAX_RAW_BYTES,
        }
        files.append(file_item)
        terms = []
        for pattern in (r"MIT", r"CC[- ]BY(?:[- ]4\.0)?", r"Creative Commons Attribution 4\.0", r"third.party", r"external material", r"외부 자료", r"교육 콘텐츠", r"실행 코드"):
            terms.extend(clean_text(match, 100) for match in re.findall(pattern, text, re.IGNORECASE)[:5])
        if terms:
            snippets.append({"path": path, "observedTerms": terms[:8]})
    github_license = (repo_metadata.get("license") or {}).get("spdx_id") or "NOASSERTION"
    content_names = {Path(path).name.casefold() for path in matches}
    if "license.md" in content_names and {"license-mit", "license-cc-by-4.0"} <= content_names:
        observed_summary = "LICENSE.md and separate MIT/CC BY 4.0 files are present; file-purpose scope and third-party exclusions require reading the source notice."
    elif matches:
        observed_summary = "One or more license/notice files are present; scope is file-specific and requires human review."
    else:
        observed_summary = "No root or nested license-named file was discoverable in the repository tree; do not assume permission."
    return {
        "githubApiLicenseSpdx": github_license,
        "githubApiLicenseUrl": (repo_metadata.get("license") or {}).get("url"),
        "declaredFiles": files,
        "observedTermsOnly": snippets,
        "noticePaths": notices,
        "automatedSummary": observed_summary,
        "rightsDetermination": "not-automatically-determined",
        "sourceCommitSha": revision,
    }


def file_kind(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if LICENSE_NAME.search(name):
        return "license"
    if re.fullmatch(r"(?:notice|third[-_. ]party(?:[-_. ]notices)?)(?:[-_.][^/]*)?", name, re.IGNORECASE):
        return "rights-notice"
    if CHAPTER_DIR.search(path) and Path(path).suffix.casefold() in INTERESTING_EXTENSIONS:
        return "chapter"
    if SIMULATOR_PATH.search(path):
        return "simulator-source"
    if path.casefold() in {"book.json", "index.html", "readme.md", "readme.rst"} or path.casefold().endswith("/readme.md"):
        return "book-metadata"
    if Path(path).suffix.casefold() in {".md", ".mdx", ".html", ".json"} and (path.startswith("docs/") or path.startswith("data/")):
        return "supporting-content"
    if Path(path).suffix.casefold() in {".js", ".mjs", ".css", ".py", ".c", ".h", ".ts"} and path.split("/", 1)[0] in {"js", "css", "tools", "src"}:
        return "shared-runtime"
    if Path(path).suffix.casefold() in {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif"} and path.split("/", 1)[0] in {"img", "images", "assets", "figures"}:
        return "educational-asset"
    return "other"


def relevant_source_files(tree: list[dict]) -> dict[str, dict]:
    found = {}
    for item in tree:
        path = item.get("path")
        sha = item.get("sha")
        if not isinstance(path, str) or not isinstance(sha, str):
            continue
        kind = file_kind(path)
        if kind != "other" and item.get("type") == "blob":
            found[path] = {"blobSha": sha, "kind": kind, "size": item.get("size")}
    return found


def featured_experiments(book: dict) -> list[dict]:
    out = []
    for item in book.get("featured", []) if isinstance(book.get("featured"), list) else []:
        link = item.get("link")
        if not isinstance(link, str):
            continue
        path, _, fragment = link.partition("#")
        out.append({
            "title": clean_text(str(item.get("title", "")), 180),
            "sourcePath": path,
            "fragment": fragment or None,
            "sourceUrl": book.get("url"),
        })
    return out


def inventory_one(client: GitHubClient, record: dict, checked_at: str, previous: dict | None = None) -> dict:
    book_id = record.get("id")
    if not isinstance(book_id, str) or not SAFE_ID.fullmatch(book_id):
        raise ReferenceError("catalog contains invalid book ID")
    repo_pair = repository_from_url(record.get("repo"))
    status = record.get("status") if record.get("status") in {"published", "planned", "writing"} else "unknown"
    facts = {
        "id": book_id,
        "title": clean_text(str(record.get("title", "")), 160),
        "subtitle": clean_text(str(record.get("subtitle", "")), 240),
        "topicBasedSummary": "Topics listed in the upstream catalog: " + "; ".join(compact_topics(record)[:8]),
        "status": status,
        "subject": clean_text(str(record.get("field", "")), 100),
        "audience": clean_text(str(record.get("level", "")), 160) or None,
        "topics": compact_topics(record),
        "catalogChapterCount": record.get("chapters") if isinstance(record.get("chapters"), int) else None,
        "catalogSimulatorCount": record.get("simulators") if isinstance(record.get("simulators"), int) else None,
        "repositoryUrl": record.get("repo") if isinstance(record.get("repo"), str) else None,
        "websiteUrl": record.get("url") if isinstance(record.get("url"), str) else None,
        "catalogFeaturedExperiments": featured_experiments(record),
        "catalogSourceUrl": f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/blob/main/data/books.json",
        "catalogObservedAt": checked_at,
        "originalAuthorPublisher": "geniuskey (GitHub account/repository publisher; individual authorship is not inferred)",
        "observedFactsOnly": True,
    }
    if status != "published" or repo_pair is None:
        facts.update({
            "repository": None,
            "chapters": [],
            "simulatorSourcePaths": [],
            "distinctiveContributionSummary": facts["topicBasedSummary"],
        })
        return facts

    owner, name = repo_pair
    full_name = f"{owner}/{name}"
    old = previous if previous and previous.get("id") == book_id else None
    head = list_commit(client, full_name)
    if not head["available"]:
        facts.update({"repository": None, "repositoryAvailability": {"fullName": full_name, **head, "checkedAt": checked_at}, "chapters": [], "simulatorSourcePaths": []})
        return facts
    sha = head["headSha"]
    if previous_repo := (old or {}).get("repository"):
        has_truncated_title = any("\ufffd" in chapter.get("title", "") for chapter in (old or {}).get("chapters", []))
        if previous_repo.get("headSha") == sha and previous_repo.get("fullName") == full_name and not has_truncated_title:
            # Preserve the previously observed source index on an unchanged head.
            for field in ("repository", "repositoryAvailability", "chapters", "simulatorSourcePaths", "license", "bookMetadata", "distinctiveContributionSummary"):
                if field in old:
                    facts[field] = old[field]
            facts["repository"] = dict(facts.get("repository", {}), checkedAt=checked_at)
            return facts

    metadata_status, metadata = client.json(api_url(f"/repos/{full_name}"), max_bytes=512 * 1024)
    if metadata_status != 200 or not isinstance(metadata, dict):
        raise ReferenceError(f"repository metadata unavailable for {full_name}")

    status, tree_data = client.json(api_url(f"/repos/{full_name}/git/trees/{sha}?recursive=1"), max_bytes=MAX_JSON_BYTES)
    if status != 200 or not isinstance(tree_data, dict):
        raise ReferenceError(f"git tree unavailable for {full_name}@{sha}")
    if tree_data.get("truncated"):
        raise ReferenceError(f"recursive Git tree was truncated for {full_name}@{sha}; refusing an incomplete source inventory")
    tree = tree_data.get("tree", [])
    source_map = relevant_source_files(tree)
    paths = [item.get("path") for item in tree if isinstance(item.get("path"), str) and item.get("type") == "blob"]
    old_source_map = previous_repo.get("relevantSourceFiles", {}) if previous_repo else {}
    old_license_info = (old or {}).get("license")
    license_names = {path for path in source_map if file_kind(path) == "license"}
    old_license_names = {path for path in old_source_map if file_kind(path) == "license"}
    if old_license_info and license_names == old_license_names and all(source_map[path]["blobSha"] == old_source_map[path]["blobSha"] for path in license_names):
        license_info = json.loads(json.dumps(old_license_info))
        license_info["sourceCommitSha"] = sha
    else:
        license_info = decode_license(client, full_name, sha, paths, metadata, source_map)
    book_json = None
    old_book_file = old_source_map.get("book.json")
    new_book_file = source_map.get("book.json")
    if old and old.get("bookMetadata") is not None and old_book_file == new_book_file:
        book_json = old["bookMetadata"]
    elif "book.json" in source_map:
        raw_metadata = client.raw(raw_url(full_name, sha, "book.json"), max_bytes=MAX_RAW_BYTES)
        if raw_metadata:
            try:
                observed_book_metadata = json.loads(raw_metadata)
                book_json = {key: observed_book_metadata[key] for key in ("id", "title", "url", "repo", "field", "status", "domain") if key in observed_book_metadata}
            except json.JSONDecodeError:
                book_json = {"parseError": "malformed-json"}
    chapters = []
    previous_chapters = {item.get("path"): item for item in (old or {}).get("chapters", []) if isinstance(item, dict)}
    for path, info in sorted(source_map.items()):
        if info["kind"] != "chapter":
            continue
        existing = previous_chapters.get(path)
        if existing and existing.get("blobSha") == info["blobSha"] and "\ufffd" not in existing.get("title", ""):
            chapters.append(existing)
            continue
        fallback = Path(path).stem.replace("-", " ").replace("_", " ").strip().title()
        title, title_source = chapter_title(client, raw_url(full_name, sha, path), fallback)
        chapters.append({
            "path": path,
            "title": title,
            "titleSource": title_source,
            "blobSha": info["blobSha"],
            "sourceUrl": f"https://github.com/{full_name}/blob/{sha}/{path}",
        })
    sim_paths = sorted(path for path, info in source_map.items() if info["kind"] == "simulator-source")
    contribution = {
        "summary": facts["topicBasedSummary"],
        "topicsFromCatalog": facts["topics"],
        "centralCatalogChapterCount": facts["catalogChapterCount"],
        "indexedChapterPathCount": len(chapters),
        "centralCatalogSimulatorCount": facts["catalogSimulatorCount"],
        "featuredActivities": facts["catalogFeaturedExperiments"],
        "evidenceSource": "upstream central metadata and repository chapter/source path index; editorial synthesis not performed automatically",
    }
    facts.update({
        "repository": {
            "fullName": full_name,
            "repositoryUrl": f"https://github.com/{full_name}",
            "defaultBranch": metadata.get("default_branch"),
            "githubApiLicenseSpdx": (metadata.get("license") or {}).get("spdx_id") or "NOASSERTION",
            "headSha": sha,
            "headCommittedAt": head.get("headCommittedAt"),
            "headCommitMessage": head.get("headCommitMessage"),
            "commitUrl": head.get("commitUrl"),
            "checkedAt": checked_at,
            "treeTruncated": bool(tree_data.get("truncated")),
            "relevantSourceFiles": source_map,
        },
        "repositoryAvailability": {"fullName": full_name, "available": True, "checkedAt": checked_at},
        "chapters": chapters,
        "simulatorSourcePaths": sim_paths,
        "license": license_info,
        "bookMetadata": book_json,
        "distinctiveContributionSummary": contribution,
    })
    return facts


def current_inventory(client: GitHubClient, previous: dict | None = None, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    checked_at = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    central_commit = list_commit(client, f"{UPSTREAM_OWNER}/{UPSTREAM_REPO}")
    if not central_commit.get("available"):
        raise ReferenceError("central upstream catalog repository is unavailable")
    revision = central_commit["headSha"]
    central_repo_status, central_repo_metadata = client.json(api_url(f"/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}"), max_bytes=512 * 1024)
    if central_repo_status != 200 or not isinstance(central_repo_metadata, dict):
        raise ReferenceError("central upstream repository metadata is unavailable")
    tree_status, central_tree_data = client.json(api_url(f"/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/git/trees/{revision}?recursive=1"), max_bytes=MAX_JSON_BYTES)
    if tree_status != 200 or not isinstance(central_tree_data, dict):
        raise ReferenceError(f"central repository tree is unavailable at {revision}")
    if central_tree_data.get("truncated"):
        raise ReferenceError(f"central repository tree was truncated at {revision}; refusing an incomplete license/source inventory")
    central_tree = {item.get("path"): item for item in central_tree_data.get("tree", []) if isinstance(item, dict) and isinstance(item.get("path"), str) and item.get("type") == "blob"}
    central_path = raw_url(f"{UPSTREAM_OWNER}/{UPSTREAM_REPO}", revision, "data/books.json")
    catalog_status, catalog_bytes, _ = client.get(central_path, raw=True, max_bytes=MAX_CATALOG_BYTES)
    if catalog_status == 404:
        raise ReferenceError("central catalog data/books.json was not found")
    central = parse_json_bytes(catalog_bytes, "central catalog")
    records = validate_upstream_catalog(central)
    old_by_id = {item["id"]: item for item in (previous or {}).get("books", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
    # Eight concurrent public-API reads remain comfortably below the authenticated rate limit.
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(inventory_one, client, row, checked_at, old_by_id.get(row["id"])) for row in records]
        items = [future.result() for future in futures]
    items.sort(key=lambda item: item["id"])
    old_central_sources = (previous or {}).get("upstream", {}).get("centralSourceFiles", {})
    tracked_rights = {
        path for path in central_tree
        if file_kind(path) in {"license", "rights-notice"}
    }
    central_paths = tracked_rights | {"data/books.json", "data/editorial-backlog.json"} | set(old_central_sources)
    central_sources = {}
    for path in sorted(central_paths):
        tree_item = central_tree.get(path)
        if tree_item is None:
            central_sources[path] = {
                "available": False,
                "kind": old_central_sources.get(path, {}).get("kind", "editorial-backlog" if path.endswith("editorial-backlog.json") else "catalog" if path == "data/books.json" else file_kind(path)),
                "blobSha": None,
                "size": None,
                "sourceUrl": None,
            }
        else:
            kind = "catalog" if path == "data/books.json" else "editorial-backlog" if path == "data/editorial-backlog.json" else file_kind(path)
            central_sources[path] = {
                "available": True,
                "kind": kind,
                "blobSha": tree_item.get("sha"),
                "size": tree_item.get("size"),
                "sourceUrl": f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/blob/{revision}/{path}",
            }
    if not central_sources.get("data/books.json", {}).get("available"):
        raise ReferenceError("central catalog data/books.json was not present in the repository tree")
    if central_sources["data/books.json"]["blobSha"] != git_blob_sha(catalog_bytes):
        raise ReferenceError("central catalog bytes do not match the repository tree blob SHA")
    backlog_path = "data/editorial-backlog.json"
    if not central_sources[backlog_path]["available"]:
        backlog = None
    else:
        backlog_status, backlog_bytes, _ = client.get(
            raw_url(f"{UPSTREAM_OWNER}/{UPSTREAM_REPO}", revision, backlog_path),
            raw=True,
            max_bytes=MAX_CATALOG_BYTES,
        )
        if backlog_status == 404:
            raise ReferenceError("central editorial backlog disappeared between tree and raw reads")
        if central_sources[backlog_path]["blobSha"] != git_blob_sha(backlog_bytes):
            raise ReferenceError("central editorial backlog bytes do not match the repository tree blob SHA")
        backlog = parse_json_bytes(backlog_bytes, "central editorial backlog")
        raw_items = backlog.get("items", []) if isinstance(backlog, dict) else None
        if not isinstance(raw_items, list) or len(raw_items) > 1000:
            raise ReferenceError("central editorial backlog items are missing or exceed the 1000-entry limit")
        backlog_entries = []
        for row in raw_items:
            book = row.get("book", {}) if isinstance(row, dict) else {}
            if not isinstance(book, dict) or not isinstance(book.get("id"), str):
                continue
            backlog_entries.append({
                "id": clean_text(book["id"], 100),
                "title": clean_text(str(book.get("title", book["id"])), 160),
                "subject": clean_text(str(book.get("field", "")), 100),
                "status": clean_text(str(book.get("status", "unknown")), 40),
                "disposition": clean_text(str(row.get("disposition", "unspecified")), 80),
                "targets": [clean_text(str(value), 100) for value in row.get("targets", [])[:40] if isinstance(value, str)],
                "entrySha256": hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
            })
        for row in backlog.get("scopeDecisions", []) if isinstance(backlog, dict) and isinstance(backlog.get("scopeDecisions"), list) else []:
            if not isinstance(row, dict):
                continue
            source_id = row.get("source")
            if not isinstance(source_id, str):
                continue
            backlog_entries.append({
                "id": clean_text(source_id, 100),
                "title": clean_text(str(row.get("section", source_id)), 160),
                "subject": "scope-decision",
                "status": "editorial",
                "disposition": "scope-decision",
                "targets": [clean_text(str(row[key]), 100) for key in ("replacement", "sectionTarget") if isinstance(row.get(key), str)],
                "entrySha256": hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
            })
        backlog_entries.sort(key=lambda entry: (entry["id"], entry["title"]))
        central_sources[backlog_path].update({
            "reviewedOn": backlog.get("reviewedOn") if isinstance(backlog, dict) else None,
            "entryCount": len(backlog_entries),
            "entries": backlog_entries,
        })
    result = {
        "schemaVersion": 1,
        "upstream": {
            "repository": f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}",
            "website": "https://books.euiyun.com/",
            "catalogPath": "data/books.json",
            "catalogHeadSha": revision,
            "catalogCommitUrl": central_commit.get("commitUrl"),
            "catalogCommittedAt": central_commit.get("headCommittedAt"),
            "lastSuccessfulInspectionAt": checked_at,
            "entryCount": len(items),
            "publishedRepositoryCount": sum(1 for item in items if item.get("repository")),
            "observedFactsOnly": True,
            "centralSourceFiles": central_sources,
            "githubApiLicenseSpdx": (central_repo_metadata.get("license") or {}).get("spdx_id") or "NOASSERTION",
        },
        "books": items,
    }
    validate_inventory(result)
    return result


def validate_inventory(inventory: dict) -> None:
    _validate_schema(inventory, "reference-inventory.schema.json")
    if not isinstance(inventory, dict) or inventory.get("schemaVersion") != 1:
        raise ReferenceError("inventory must be an object with schemaVersion 1")
    upstream = inventory.get("upstream")
    books = inventory.get("books")
    if not isinstance(upstream, dict) or not HEX_SHA.fullmatch(str(upstream.get("catalogHeadSha", ""))):
        raise ReferenceError("inventory requires an upstream catalog commit SHA")
    if not isinstance(books, list) or len(books) > 1000:
        raise ReferenceError("inventory books must be a bounded list")
    if upstream.get("entryCount") != len(books):
        raise ReferenceError("upstream entryCount must match the indexed catalog records")
    if upstream.get("publishedRepositoryCount") != sum(bool(item.get("repository")) for item in books if isinstance(item, dict)):
        raise ReferenceError("publishedRepositoryCount must match repositories with recorded source revisions")
    central_sources = upstream.get("centralSourceFiles")
    if not isinstance(central_sources, dict):
        raise ReferenceError("inventory must index central catalog and editorial-backlog files")
    for central_path in ("data/books.json", "data/editorial-backlog.json"):
        item = central_sources.get(central_path)
        if not isinstance(item, dict) or not isinstance(item.get("available"), bool):
            raise ReferenceError(f"central source index missing availability state for {central_path}")
        if item["available"] and not HEX_SHA.fullmatch(str(item.get("blobSha", ""))):
            raise ReferenceError(f"central source index has invalid git blob SHA for {central_path}")
        if item["available"] and (not isinstance(item.get("sourceUrl"), str) or not item["sourceUrl"].startswith("https://github.com/geniuskey/books/blob/")):
            raise ReferenceError(f"central source index has invalid pinned source URL for {central_path}")
    ids = set()
    for book in books:
        if not isinstance(book, dict) or not SAFE_ID.fullmatch(str(book.get("id", ""))):
            raise ReferenceError("inventory contains an invalid book ID")
        if book["id"] in ids:
            raise ReferenceError(f"duplicate upstream book ID: {book['id']}")
        ids.add(book["id"])
        if book.get("status") not in {"published", "planned", "writing", "unknown"}:
            raise ReferenceError(f"invalid upstream status for {book['id']}")
        repo = book.get("repository")
        if repo:
            if not isinstance(repo, dict) or not HEX_SHA.fullmatch(str(repo.get("headSha", ""))):
                raise ReferenceError(f"invalid repository revision for {book['id']}")
            if repo.get("fullName", "").split("/", 1)[0].casefold() != UPSTREAM_OWNER:
                raise ReferenceError(f"repository owner is outside the monitored upstream for {book['id']}")
            if book.get("repositoryUrl") != f"https://github.com/{repo['fullName']}":
                raise ReferenceError(f"repository URL does not match indexed GitHub repository for {book['id']}")
            sources = repo.get("relevantSourceFiles")
            if not isinstance(sources, dict):
                raise ReferenceError(f"source index missing for {book['id']}")
            for path, item in sources.items():
                if (not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts
                        or not isinstance(item, dict) or not HEX_SHA.fullmatch(str(item.get("blobSha", "")))
                        or item.get("kind") not in {"chapter", "simulator-source", "license", "rights-notice", "book-metadata", "supporting-content", "shared-runtime", "educational-asset"}):
                    raise ReferenceError(f"unsafe source path/hash for {book['id']}")


def compare_inventories(previous: dict, current: dict, reviews: dict | None = None) -> list[dict]:
    validate_inventory(previous)
    validate_inventory(current)
    old = {item["id"]: item for item in previous["books"]}
    new = {item["id"]: item for item in current["books"]}
    decisions = [item for item in (reviews or {}).get("decisions", []) if isinstance(item, dict)]
    changes = []
    old_central_sources = previous["upstream"].get("centralSourceFiles", {})
    new_central_sources = current["upstream"].get("centralSourceFiles", {})
    if previous["upstream"].get("githubApiLicenseSpdx") != current["upstream"].get("githubApiLicenseSpdx"):
        changes.append({"kind": "central-github-license-metadata-changed", "before": previous["upstream"].get("githubApiLicenseSpdx"), "after": current["upstream"].get("githubApiLicenseSpdx")})
    for path in sorted(set(old_central_sources) | set(new_central_sources)):
        before, after = old_central_sources.get(path), new_central_sources.get(path)
        if before == after:
            continue
        kind = (after or before or {}).get("kind", "central-source")
        if kind == "editorial-backlog" and before and after and before.get("available") and after.get("available"):
            before_entries = {entry["id"]: entry for entry in before.get("entries", [])}
            after_entries = {entry["id"]: entry for entry in after.get("entries", [])}
            for book_id in sorted(set(before_entries) | set(after_entries)):
                old_entry, new_entry = before_entries.get(book_id), after_entries.get(book_id)
                if old_entry != new_entry:
                    event = "added" if old_entry is None else "removed" if new_entry is None else "changed"
                    changes.append({"kind": f"central-editorial-backlog-{event}", "bookId": book_id, "title": (new_entry or old_entry)["title"], "before": old_entry, "after": new_entry, "path": path, "beforeBlob": before.get("blobSha"), "afterBlob": after.get("blobSha"), "compareUrl": f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/compare/{previous['upstream']['catalogHeadSha']}...{current['upstream']['catalogHeadSha']}"})
            if before.get("blobSha") != after.get("blobSha") and before.get("entries") == after.get("entries") and before.get("reviewedOn") != after.get("reviewedOn"):
                changes.append({"kind": "central-editorial-backlog-review-metadata-changed", "path": path, "before": before.get("reviewedOn"), "after": after.get("reviewedOn"), "beforeBlob": before.get("blobSha"), "afterBlob": after.get("blobSha"), "compareUrl": f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/compare/{previous['upstream']['catalogHeadSha']}...{current['upstream']['catalogHeadSha']}"})
        elif before is None or after is None or before.get("available") != after.get("available") or before.get("blobSha") != after.get("blobSha"):
            event = "added" if before is None or not before.get("available") else "removed" if after is None or not after.get("available") else "changed"
            changes.append({"kind": f"central-{kind}-{event}", "path": path, "beforeBlob": (before or {}).get("blobSha"), "afterBlob": (after or {}).get("blobSha"), "compareUrl": f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/compare/{previous['upstream']['catalogHeadSha']}...{current['upstream']['catalogHeadSha']}"})
    if previous["upstream"]["catalogHeadSha"] != current["upstream"]["catalogHeadSha"]:
        old_ids, new_ids = set(old), set(new)
        for book_id in sorted(new_ids - old_ids):
            changes.append({"kind": "catalog-book-added", "bookId": book_id, "title": new[book_id]["title"], "status": new[book_id]["status"]})
        for book_id in sorted(old_ids - new_ids):
            changes.append({"kind": "catalog-book-removed", "bookId": book_id, "title": old[book_id]["title"], "status": old[book_id]["status"]})
        for book_id in sorted(old_ids & new_ids):
            before, after = old[book_id], new[book_id]
            for field in ("status", "title", "subtitle", "subject", "topics", "repositoryUrl", "websiteUrl", "catalogChapterCount", "catalogSimulatorCount"):
                if before.get(field) != after.get(field):
                    changes.append({"kind": "catalog-metadata-changed", "bookId": book_id, "field": field, "before": before.get(field), "after": after.get(field)})
    for book_id in sorted(set(old) & set(new)):
        before, after = old[book_id], new[book_id]
        old_repo, new_repo = before.get("repository") or {}, after.get("repository") or {}
        if not new_repo:
            if old_repo or before.get("status") != after.get("status"):
                changes.append({"kind": "repository-unavailable", "bookId": book_id, "title": after["title"], "repositoryAvailability": after.get("repositoryAvailability")})
            continue
        if not old_repo:
            changes.append({"kind": "repository-added", "bookId": book_id, "title": after["title"], "headSha": new_repo.get("headSha")})
            continue
        if old_repo.get("headSha") == new_repo.get("headSha"):
            continue
        old_files = old_repo.get("relevantSourceFiles", {})
        new_files = new_repo.get("relevantSourceFiles", {})
        path_changes = []
        for path in sorted(set(old_files) | set(new_files)):
            was, now = old_files.get(path), new_files.get(path)
            if was == now:
                continue
            kind = (now or was or {}).get("kind", "other")
            if kind == "other":
                continue
            event = "added" if was is None else "deleted" if now is None else "changed"
            path_changes.append({"kind": kind, "event": event, "path": path, "before": was, "after": now})
        added_by_blob = {}
        for item in path_changes:
            if item["event"] == "added":
                added_by_blob.setdefault((item["kind"], item["after"].get("blobSha")), []).append(item)
        moved_paths = set()
        for item in path_changes:
            if item["event"] != "deleted":
                continue
            candidates = added_by_blob.get((item["kind"], item["before"].get("blobSha")), [])
            candidate = next((value for value in candidates if value["path"] not in moved_paths), None)
            if candidate:
                moved_paths.add(item["path"]); moved_paths.add(candidate["path"])
                changes.append({"kind": f"source-{item['kind']}-moved", "bookId": book_id, "title": after["title"], "fromPath": item["path"], "toPath": candidate["path"], "blobSha": item["before"].get("blobSha"), "compareUrl": f"https://github.com/{new_repo['fullName']}/compare/{old_repo.get('headSha')}...{new_repo.get('headSha')}"})
        for item in path_changes:
            if item["path"] in moved_paths:
                continue
            path, kind = item["path"], item["kind"]
            changes.append({"kind": f"source-{kind}-{item['event']}", "bookId": book_id, "title": after["title"], "path": path, "beforeBlob": (item["before"] or {}).get("blobSha"), "afterBlob": (item["after"] or {}).get("blobSha"), "compareUrl": f"https://github.com/{new_repo['fullName']}/compare/{old_repo.get('headSha')}...{new_repo.get('headSha')}"})
        if old_repo.get("githubApiLicenseSpdx") != new_repo.get("githubApiLicenseSpdx"):
            changes.append({"kind": "github-license-metadata-changed", "bookId": book_id, "before": old_repo.get("githubApiLicenseSpdx"), "after": new_repo.get("githubApiLicenseSpdx")})
        old_licenses = {item["path"]: item.get("blobSha") for item in (before.get("license") or {}).get("declaredFiles", [])}
        new_licenses = {item["path"]: item.get("blobSha") for item in (after.get("license") or {}).get("declaredFiles", [])}
        for path in sorted(set(old_licenses) | set(new_licenses)):
            if old_licenses.get(path) != new_licenses.get(path):
                changes.append({"kind": "license-file-changed", "bookId": book_id, "title": after["title"], "path": path, "before": old_licenses.get(path), "after": new_licenses.get(path)})
    for change in changes:
        matches = []
        for decision in decisions:
            for source in decision.get("sourceRevisions", []):
                if isinstance(source, dict) and source.get("bookId") == change.get("bookId"):
                    matches.append({
                        "projectId": decision["projectId"],
                        "outcome": decision.get("outcome"),
                        "lastReviewedSha": source.get("observedSha"),
                        "reviewedAt": decision.get("reviewedAt"),
                        "reviewedAgainstCatalogSha": decision.get("reviewedAgainstCatalogSha"),
                    })
            if decision.get("projectId") == change.get("bookId") and not any(item["projectId"] == decision["projectId"] for item in matches):
                matches.append({"projectId": decision["projectId"], "outcome": decision.get("outcome"), "lastReviewedSha": None, "reviewedSources": [{"bookId": source.get("bookId"), "observedSha": source.get("observedSha")} for source in decision.get("sourceRevisions", []) if isinstance(source, dict)], "reviewedAt": decision.get("reviewedAt"), "reviewedAgainstCatalogSha": decision.get("reviewedAgainstCatalogSha")})
        change["affectedProjects"] = matches
    return changes


def summarize_changes(changes: list[dict], current: dict) -> str:
    timestamp = current["upstream"]["lastSuccessfulInspectionAt"]
    lines = ["# Upstream reference intelligence", "", f"Inspection completed: {_inline_code(timestamp)}", f"Central catalog: [{_inline_code(current['upstream']['catalogHeadSha'][:12])}]({current['upstream'].get('catalogCommitUrl')})", f"Catalog entries: {current['upstream']['entryCount']} ({current['upstream']['publishedRepositoryCount']} published public repositories).", ""]
    if not changes:
        lines += ["No catalog, chapter, simulator-source, or rights-file changes were detected since the last reviewed inventory snapshot.", "", "No editorial decisions or publication records were changed."]
        return "\n".join(lines) + "\n"
    counts: dict[str, int] = {}
    for change in changes:
        counts[change["kind"]] = counts.get(change["kind"], 0) + 1
    lines += [f"Detected **{len(changes)} material source/catalog change(s)** since the last reviewed inventory snapshot: " + ", ".join(f"`{key}` {value}" for key, value in sorted(counts.items())) + ".", "", "The tool reports observed paths and revisions only. It does not accept reuse rights, approve editorial outcomes, or alter publication status.", "", "## Changes"]
    for item in changes[:MAX_REPORTED_CHANGES]:
        label = _plain_markdown_text(item.get("title") or item.get("bookId") or "catalog")
        details = item.get("path") or item.get("field") or item.get("kind")
        if item.get("compareUrl"):
            details = f"[{_inline_code(details)}]({item['compareUrl']})"
        elif item.get("path"):
            repo = next((b.get("repository", {}).get("fullName") for b in current["books"] if b["id"] == item.get("bookId") and b.get("repository")), None)
            if repo:
                safe_path = quote(str(item["path"]), safe="/")
                details = f"[{_inline_code(details)}](https://github.com/{repo}/blob/{item.get('afterBlob') or item.get('beforeBlob')}/{safe_path})"
            else:
                details = _inline_code(details)
        else:
            details = _inline_code(details)
        line = f"- **{label}** — {_inline_code(item['kind'])}: {details}"
        if item.get("affectedProjects"):
            decisions_text = ", ".join(
                "`{}` ({}; reviewed source revision(s) {}; reviewed {})".format(
                    entry["projectId"],
                    entry.get("outcome"),
                    ", ".join("{}@{}".format(source["bookId"], source["observedSha"][:12]) for source in entry.get("reviewedSources", []))
                    or str(entry.get("lastReviewedSha") or "not recorded")[:12],
                    entry.get("reviewedAt") or "date not recorded",
                )
                for entry in item["affectedProjects"]
            )
            line += f"; potentially relevant to {decisions_text}."
        lines.append(line)
    if len(changes) > MAX_REPORTED_CHANGES:
        lines += ["", f"_Showing {MAX_REPORTED_CHANGES} of {len(changes)} changes. The complete machine-readable change list is attached to the workflow run as `reference-intelligence-report`._"]
    lines += ["", "## Review reminder", "Inspect affected source paths and file-level rights before adapting. Matching subject matter alone does not show copying or infringement. No upstream material was imported by this monitor."]
    return _bounded_report_text("\n".join(lines) + "\n", MAX_TRACKER_BODY_CHARS - 2000, "_Report excerpt capped for issue-size safety. See the `reference-intelligence-report` workflow artifact for the complete change list._")


def validate_review_records(reviews: dict, inventory: dict) -> None:
    validate_inventory(inventory)
    _validate_schema(reviews, "editorial-decisions.schema.json")
    if not isinstance(reviews, dict) or reviews.get("schemaVersion") != 1 or not isinstance(reviews.get("decisions"), list):
        raise ReferenceError("editorial-decisions.json must have schemaVersion 1 and a decisions list")
    seen = set()
    known_books = {item["id"]: item for item in inventory["books"]}
    for record in reviews["decisions"]:
        if not isinstance(record, dict):
            raise ReferenceError("editorial project records must be objects")
        project_id = record.get("projectId")
        if not isinstance(project_id, str) or not SAFE_ID.fullmatch(project_id) or project_id in seen:
            raise ReferenceError(f"invalid or duplicate editorial project id: {project_id!r}")
        seen.add(project_id)
        if record.get("outcome") not in DECISIONS:
            raise ReferenceError(f"{project_id}: invalid editorial outcome")
        for field in ("targetAudience", "overlapEvidence", "uniqueValue", "developmentStrategy", "reusePlan", "confidence", "unresolvedQuestions", "sourceRevisions", "reviewedAt", "reviewedAgainstCatalogSha"):
            if field not in record:
                raise ReferenceError(f"{project_id}: missing {field}")
        if not isinstance(record["sourceRevisions"], list) or not record["sourceRevisions"]:
            raise ReferenceError(f"{project_id}: at least one source revision is required")
        for source in record["sourceRevisions"]:
            if not isinstance(source, dict) or source.get("bookId") not in known_books:
                raise ReferenceError(f"{project_id}: source revision must reference an inventoried upstream book")
            if not HEX_SHA.fullmatch(str(source.get("observedSha", ""))):
                raise ReferenceError(f"{project_id}: source revision for {source['bookId']} must use a full commit SHA")
            upstream_book = known_books[source["bookId"]]
            repository = upstream_book.get("repository")
            if not isinstance(repository, dict) or not isinstance(repository.get("fullName"), str):
                raise ReferenceError(f"{project_id}: source revision {source['bookId']} has no indexed repository")
            expected_url = f"https://github.com/{repository['fullName']}/tree/{source['observedSha']}"
            if source.get("sourceUrl") != expected_url:
                raise ReferenceError(f"{project_id}: sourceUrl for {source['bookId']} must pin its repository and observed SHA")
            source_paths = source.get("sourcePaths")
            if not isinstance(source_paths, list) or not source_paths:
                raise ReferenceError(f"{project_id}: sourcePaths for {source['bookId']} must be a non-empty list")
            if any(not _is_safe_source_path(path) for path in source_paths) or len(source_paths) != len(set(source_paths)):
                raise ReferenceError(f"{project_id}: sourcePaths for {source['bookId']} must be unique safe relative paths")
        if not isinstance(record["unresolvedQuestions"], list) or not isinstance(record["reusePlan"], list):
            raise ReferenceError(f"{project_id}: unresolvedQuestions and reusePlan must be lists")
        reviewed_sha = record.get("reviewedAgainstCatalogSha")
        if not HEX_SHA.fullmatch(str(reviewed_sha)):
            raise ReferenceError(f"{project_id}: reviewedAgainstCatalogSha must be a full SHA")


def validate_project_gate(project_id: str, reviews: dict, inventory: dict) -> dict:
    validate_review_records(reviews, inventory)
    decision = next((item for item in reviews["decisions"] if item["projectId"] == project_id), None)
    if decision is None:
        raise ReferenceError(f"{project_id}: add a reviewed editorial differentiation record before starting this book")
    if decision["reviewedAgainstCatalogSha"] != inventory["upstream"]["catalogHeadSha"]:
        raise ReferenceError(f"{project_id}: refresh the editorial review against the current central catalog SHA")
    for source in decision["sourceRevisions"]:
        upstream_book = next(item for item in inventory["books"] if item["id"] == source["bookId"])
        repository = upstream_book.get("repository") or {}
        if source["observedSha"] != repository.get("headSha"):
            raise ReferenceError(f"{project_id}: refresh the reviewed source revision for {source['bookId']}")
        expected_url = f"https://github.com/{repository.get('fullName')}/tree/{repository.get('headSha')}"
        if source["sourceUrl"] != expected_url:
            raise ReferenceError(f"{project_id}: sourceUrl for {source['bookId']} does not pin its current indexed revision")
        indexed_paths = repository.get("relevantSourceFiles", {})
        missing_paths = sorted(set(source["sourcePaths"]) - set(indexed_paths))
        if missing_paths:
            raise ReferenceError(f"{project_id}: sourcePaths for {source['bookId']} are not in the current indexed inventory: {', '.join(missing_paths)}")
    if decision["outcome"] in {"reference-only", "defer-or-cancel"}:
        raise ReferenceError(f"{project_id}: editorial outcome {decision['outcome']} does not authorize a separate book project")
    return decision


def _is_safe_source_path(path) -> bool:
    return (isinstance(path, str) and bool(path.strip()) and "\\" not in path
            and not path.startswith("/") and all(part not in {"", ".", ".."} for part in path.split("/")))


def validate_provenance_records(provenance: dict) -> None:
    _validate_schema(provenance, "provenance-audit.schema.json")
    if not isinstance(provenance, dict) or provenance.get("schemaVersion") != 1 or not isinstance(provenance.get("works"), list):
        raise ReferenceError("provenance-audit.json must have schemaVersion 1 and a works list")
    seen = set()
    required = {"workId", "workName", "workUrl", "auditScope", "reuseRecords", "findings", "reviewedAt", "reviewStatus"}
    for work in provenance["works"]:
        if not isinstance(work, dict) or required - set(work):
            raise ReferenceError("each provenance work requires " + ", ".join(sorted(required)))
        if work["workId"] in seen or not SAFE_ID.fullmatch(str(work["workId"])):
            raise ReferenceError(f"invalid or duplicate provenance work id: {work['workId']!r}")
        seen.add(work["workId"])
        if work["reviewStatus"] not in {"reviewed", "follow-up-required", "unresolved"}:
            raise ReferenceError(f"{work['workId']}: invalid review status")
        if not isinstance(work["reuseRecords"], list) or not isinstance(work["findings"], list):
            raise ReferenceError(f"{work['workId']}: reuseRecords/findings must be arrays")
        if not work["reuseRecords"]:
            raise ReferenceError(f"{work['workId']}: at least one explicit rights/provenance assessment is required")
        if work["reviewStatus"] == "follow-up-required":
            actionable = [finding for finding in work["findings"] if isinstance(finding, dict)
                          and finding.get("severity") in {"P0", "P1", "P2"}
                          and isinstance(finding.get("recommendedAction"), str)
                          and finding["recommendedAction"].strip()]
            if not actionable:
                raise ReferenceError(f"{work['workId']}: follow-up-required needs a concrete recommendedAction for a P0/P1/P2 finding")
        for finding in work["findings"]:
            if not isinstance(finding, dict):
                raise ReferenceError(f"{work['workId']}: findings must contain objects")
            action = finding.get("recommendedAction")
            if finding.get("severity") in {"P0", "P1", "P2"} and (not isinstance(action, str) or not action.strip()):
                raise ReferenceError(f"{work['workId']}: {finding.get('severity')} finding requires a non-empty recommendedAction")
        for source in work["reuseRecords"]:
            if not isinstance(source, dict) or source.get("classification") not in REUSE_CLASSES:
                raise ReferenceError(f"{work['workId']}: invalid source classification")
            classification = source["classification"]
            if classification == "original":
                for field in ("sourcePath", "destinationPath", "rightsStatus"):
                    if not source.get(field):
                        raise ReferenceError(f"{work['workId']}: original assessment requires {field}")
            elif classification == "third-party-material":
                for field in ("sourceTitle", "sourceAuthor", "sourcePath", "destinationPath", "licenseName", "licenseUrl", "rightsStatus", "restrictions", "noticeLocation"):
                    if not source.get(field):
                        raise ReferenceError(f"{work['workId']}: third-party material assessment requires {field}")
                notices = source.get("requiredNotices")
                if (not isinstance(notices, list) or not notices
                        or any(not isinstance(notice, str) or not notice.strip() for notice in notices)):
                    raise ReferenceError(f"{work['workId']}: third-party material assessment requires verified requiredNotices")
                if not source.get("sourceUrl") and not source.get("sourceRepository"):
                    raise ReferenceError(f"{work['workId']}: third-party material assessment requires sourceUrl or sourceRepository")
                _validate_provenance_urls(work["workId"], source)
                if _is_github_source(source) and not HEX_SHA.fullmatch(str(source.get("sourceCommitSha", ""))):
                    raise ReferenceError(f"{work['workId']}: GitHub third-party sourceCommitSha must be a full SHA")
            if source["classification"] in {"cc-by-4.0-adaptation", "mit-code-reuse"}:
                for field in ("sourceTitle", "sourceAuthor", "sourcePath", "licenseName", "licenseUrl", "changesMade", "destinationPath", "translationStatus"):
                    if not source.get(field):
                        raise ReferenceError(f"{work['workId']}: adaptation/code record requires {field}")
                notices = source.get("requiredNotices")
                if (not isinstance(notices, list) or not notices
                        or any(not isinstance(notice, str) or not notice.strip() for notice in notices)):
                    raise ReferenceError(f"{work['workId']}: adaptation/code record requires verified requiredNotices (use an explicit none-supplied statement when appropriate)")
                if not source.get("sourceUrl") and not source.get("sourceRepository"):
                    raise ReferenceError(f"{work['workId']}: adaptation/code record requires sourceUrl or sourceRepository")
                _validate_provenance_urls(work["workId"], source)
                if _is_github_source(source) and not HEX_SHA.fullmatch(str(source.get("sourceCommitSha", ""))):
                    raise ReferenceError(f"{work['workId']}: GitHub adaptation/code sourceCommitSha must be a full SHA")
            elif source["classification"] == "license-uncertain" and not source.get("followUpRequired"):
                raise ReferenceError(f"{work['workId']}: uncertain material requires followUpRequired")
            elif source["classification"] == "reference-only":
                if not all(source.get(field) for field in ("sourceTitle", "sourceAuthor", "sourcePath", "destinationPath", "licenseObservation")):
                    raise ReferenceError(f"{work['workId']}: reference-only source needs identifiable source/revision/rights evidence")
                if not source.get("sourceUrl") and not source.get("sourceRepository"):
                    raise ReferenceError(f"{work['workId']}: reference-only source requires sourceUrl or sourceRepository")
                _validate_provenance_urls(work["workId"], source)
                if _is_github_source(source) and not HEX_SHA.fullmatch(str(source.get("sourceCommitSha", ""))):
                    raise ReferenceError(f"{work['workId']}: GitHub reference sourceCommitSha must be a full SHA")
            elif classification == "license-uncertain":
                if not source.get("sourcePath") or not source.get("destinationPath"):
                    raise ReferenceError(f"{work['workId']}: uncertain material requires sourcePath and destinationPath")
                if not source.get("sourceUrl") and not source.get("sourceRepository"):
                    raise ReferenceError(f"{work['workId']}: uncertain material requires sourceUrl or sourceRepository")
                _validate_provenance_urls(work["workId"], source)


def _validate_provenance_urls(work_id: str, source: dict) -> None:
    for field in ("sourceUrl", "sourceRepository", "licenseUrl"):
        value = source.get(field)
        if value:
            parsed = urlparse(value)
            try:
                port = parsed.port
            except ValueError as exc:
                raise ReferenceError(f"{work_id}: {field} is not a valid HTTPS URL") from exc
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or port not in (None, 443):
                raise ReferenceError(f"{work_id}: {field} must be a valid HTTPS URL")
    source_url = source.get("sourceUrl")
    if source_url and _normalized_hostname(urlparse(source_url)) in {"github.com", "raw.githubusercontent.com"}:
        _validate_pinned_github_source_url(work_id, source, source_url, source.get("sourcePath"))
    mappings = source.get("sourceMappings", [])
    if not isinstance(mappings, list) or len(mappings) > 500:
        raise ReferenceError(f"{work_id}: sourceMappings must be a bounded list")
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict) or not isinstance(mapping.get("sourcePath"), str) or not mapping["sourcePath"].strip():
            raise ReferenceError(f"{work_id}: sourceMappings[{index}] requires a sourcePath")
        url = mapping.get("url")
        if url is None:
            continue
        if not isinstance(url, str):
            raise ReferenceError(f"{work_id}: sourceMappings[{index}].url must be a string")
        parsed = urlparse(url)
        try:
            port = parsed.port
        except ValueError as exc:
            raise ReferenceError(f"{work_id}: sourceMappings[{index}].url is not a valid HTTPS URL") from exc
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or port not in (None, 443):
            raise ReferenceError(f"{work_id}: sourceMappings[{index}].url must be a valid HTTPS URL")
        if _normalized_hostname(parsed) in {"github.com", "raw.githubusercontent.com"}:
            _validate_pinned_github_source_url(work_id, source, url, mapping["sourcePath"])


def _validate_pinned_github_source_url(work_id: str, source: dict, url: str, source_path: str | None) -> None:
    """Bind a GitHub file link to the declared repository, full revision, and path."""
    parsed = urlparse(url)
    repository_url = source.get("sourceRepository")
    repository = urlparse(repository_url) if isinstance(repository_url, str) else None
    if (repository is None or repository.scheme != "https" or _normalized_hostname(repository) != "github.com"
            or repository.username or repository.password or repository.query or repository.fragment
            or repository.path.strip("/").count("/") != 1):
        raise ReferenceError(f"{work_id}: GitHub source URL requires a sourceRepository in https://github.com/owner/repo form")
    owner, repo = repository.path.strip("/").split("/", 1)
    parts = [unquote(part) for part in parsed.path.split("/")]
    hostname = _normalized_hostname(parsed)
    if hostname == "github.com":
        valid_shape = len(parts) >= 6 and parts[3] in {"blob", "tree"}
        url_owner, url_repo = (parts[1], parts[2]) if len(parts) >= 3 else ("", "")
        url_sha = parts[4] if len(parts) >= 5 else ""
        url_path = "/".join(parts[5:]) if len(parts) >= 6 else ""
    elif hostname == "raw.githubusercontent.com":
        valid_shape = len(parts) >= 5
        url_owner, url_repo = (parts[1], parts[2]) if len(parts) >= 3 else ("", "")
        url_sha = parts[3] if len(parts) >= 4 else ""
        url_path = "/".join(parts[4:]) if len(parts) >= 5 else ""
    else:
        return
    if (parsed.query or parsed.fragment or not valid_shape
            or url_owner.casefold() != owner.casefold() or url_repo.casefold() != repo.casefold()
            or not HEX_SHA.fullmatch(url_sha) or url_sha != source.get("sourceCommitSha")
            or not isinstance(source_path, str) or url_path != source_path):
        raise ReferenceError(f"{work_id}: GitHub source URL must pin the declared repository, full sourceCommitSha, and exact sourcePath")


def _is_github_source(source: dict) -> bool:
    return any(_normalized_hostname(urlparse(source.get(field, ""))) in {"github.com", "raw.githubusercontent.com"} for field in ("sourceRepository", "sourceUrl") if source.get(field))


def _normalized_hostname(parsed) -> str:
    """Normalize DNS aliases before deciding whether a source is hosted on GitHub."""
    hostname = (parsed.hostname or "").rstrip(".").casefold()
    return "github.com" if hostname == "www.github.com" else hostname


def change_fingerprint(changes: list[dict]) -> str:
    stable = json.dumps(changes, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def _encode_checkpoint(inventory: dict) -> list[tuple[str, str]]:
    payload = json.dumps(inventory, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_CHECKPOINT_JSON_BYTES:
        raise ReferenceError("monitor checkpoint exceeds the 4 MB expanded-size limit")
    packed = zlib.compress(payload, level=9)
    encoded = base64.b64encode(packed).decode("ascii")
    chunks = [encoded[offset:offset + CHECKPOINT_CHUNK_CHARS] for offset in range(0, len(encoded), CHECKPOINT_CHUNK_CHARS)]
    if not chunks or len(chunks) > MAX_CHECKPOINT_CHUNKS:
        raise ReferenceError(f"compressed monitor checkpoint requires more than {MAX_CHECKPOINT_CHUNKS} issue comments")
    state_sha = hashlib.sha256(packed).hexdigest()
    return [f"<!-- MY_LIBRARY_REFERENCE_CHECKPOINT_V1:{state_sha}:{index}:{len(chunks)} -->\n{chunk}" for index, chunk in enumerate(chunks, 1)]


def _decode_checkpoint(comments: list[dict]) -> dict | None:
    groups: dict[str, dict] = {}
    for comment in comments:
        if (comment.get("user") or {}).get("login") not in {"frbread7", "github-actions[bot]"}:
            continue
        body = comment.get("body") or ""
        match = STATE_MARKER_RE.search(body)
        if not match:
            continue
        state_sha, index_text, total_text = match.groups()
        index, total = int(index_text), int(total_text)
        if total < 1 or total > MAX_CHECKPOINT_CHUNKS or index < 1 or index > total:
            continue
        encoded = body[match.end():].strip()
        group = groups.setdefault(state_sha, {"total": total, "chunks": {}, "updatedAt": comment.get("updated_at", "")})
        if group["total"] != total:
            continue
        group["chunks"][index] = encoded
        group["updatedAt"] = max(group["updatedAt"], comment.get("updated_at", ""))
    complete = [group for group in groups.values() if len(group["chunks"]) == group["total"] and set(group["chunks"]) == set(range(1, group["total"] + 1))]
    if not complete:
        return None
    complete_sha = {sha for sha, group in groups.items() if len(group["chunks"]) == group["total"] and set(group["chunks"]) == set(range(1, group["total"] + 1))}
    state_sha, group = max(((key, value) for key, value in groups.items() if key in complete_sha), key=lambda entry: entry[1]["updatedAt"])
    encoded = "".join(group["chunks"][index] for index in range(1, group["total"] + 1))
    if len(encoded) > CHECKPOINT_CHUNK_CHARS * MAX_CHECKPOINT_CHUNKS:
        raise ReferenceError("monitor checkpoint exceeds the encoded-size limit")
    try:
        packed = base64.b64decode(encoded, validate=True)
        inflater = zlib.decompressobj()
        payload = inflater.decompress(packed, MAX_CHECKPOINT_JSON_BYTES + 1)
        if len(payload) > MAX_CHECKPOINT_JSON_BYTES or inflater.unconsumed_tail or not inflater.eof or inflater.unused_data:
            raise ReferenceError("monitor checkpoint is oversized or malformed")
        if hashlib.sha256(packed).hexdigest() != state_sha:
            raise ReferenceError("monitor checkpoint hash is invalid")
        inventory = json.loads(payload.decode("utf-8"))
    except (ValueError, zlib.error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReferenceError(f"tracking issue checkpoint is invalid: {exc}") from exc
    validate_inventory(inventory)
    return inventory


def _validate_schema(value: dict, filename: str) -> None:
    schema_path = ROOT / "schemas" / filename
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceError(f"cannot read schema {schema_path}: {exc}") from exc
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value), key=lambda error: list(map(str, error.absolute_path)))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise ReferenceError(f"{filename} validation at {location}: {error.message}")


def find_tracking_issue(client: GitHubClient, owner: str, repo: str):
    if not client.token:
        raise ReferenceError("GITHUB_TOKEN is required to persist the deduplicated tracker checkpoint")
    # Sort by most recently updated and bound pagination. A found tracker is
    # refreshed only when the delta fingerprint changes, keeping it near page 1.
    for page in range(1, 11):
        url = api_url(f"/repos/{owner}/{repo}/issues?state=all&sort=updated&direction=desc&per_page=30&page={page}")
        status, issues = client.json(url, max_bytes=4 * 1024 * 1024)
        if status != 200 or not isinstance(issues, list):
            raise ReferenceError("could not list My Library issues for the deduplicated change report")
        issue = next((item for item in issues if not item.get("pull_request") and item.get("title") == "Upstream reference intelligence — review tracker" and ISSUE_MARKER in (item.get("body") or "") and (item.get("user") or {}).get("login") in {"frbread7", "github-actions[bot]"}), None)
        if issue:
            return issue
        if len(issues) < 30:
            return None
    raise ReferenceError("tracking issue was not found in the bounded 300-issue scan; refusing to create a possible duplicate")


def issue_comments(client: GitHubClient, owner: str, repo: str, issue_number: int) -> list[dict]:
    comments = []
    for page in range(1, 11):
        status, batch = client.json(api_url(f"/repos/{owner}/{repo}/issues/{issue_number}/comments?per_page=30&page={page}"), max_bytes=4 * 1024 * 1024)
        if status != 200 or not isinstance(batch, list):
            raise ReferenceError(f"could not read reference tracker comments for issue #{issue_number}")
        comments.extend(batch)
        if len(batch) < 30:
            return comments
    raise ReferenceError(f"reference tracker issue #{issue_number} exceeds the bounded 300-comment scan")


def issue_write(client: GitHubClient, url: str, method: str, payload: dict) -> dict:
    if not client.token:
        raise ReferenceError("GITHUB_TOKEN is required to persist the deduplicated tracker checkpoint")
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "User-Agent": "My-Library-Reference-Intelligence/1.0",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "Authorization": f"Bearer {client.token}",
        "Content-Type": "application/json",
    }
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(Request(url, data=data, headers=headers, method=method), timeout=TIMEOUT_SECONDS) as response:
                result = json.loads(response.read(512 * 1024))
                if not isinstance(result, dict):
                    raise ReferenceError("GitHub write API returned an unexpected JSON shape")
                return result
        except HTTPError as exc:
            detail = exc.read(2048).decode("utf-8", "replace")
            rate_wait = rate_limit_wait_seconds(exc.code, exc.headers, detail, attempt)
            retryable = rate_wait is not None or exc.code >= 500
            if method.upper() == "POST" and rate_wait is None and exc.code >= 500:
                raise ReferenceError(f"GitHub POST outcome is ambiguous after HTTP {exc.code}; not retrying to avoid duplicate issues/comments. Rerun the monitor to rediscover any committed marker/checkpoint. {detail[:300]}") from exc
            if retryable and attempt < MAX_RETRIES - 1:
                time.sleep(rate_wait if rate_wait is not None else 2 ** attempt)
                continue
            raise ReferenceError(f"GitHub write API returned HTTP {exc.code}: {detail[:400]}") from exc
        except (TimeoutError, URLError) as exc:
            if method.upper() == "POST":
                raise ReferenceError(f"GitHub POST outcome is ambiguous after a transport failure; not retrying to avoid duplicate issues/comments. Rerun the monitor to rediscover any committed marker/checkpoint. {exc}") from exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            raise ReferenceError(f"GitHub write API failed after retries: {exc}") from exc
    raise ReferenceError("GitHub write API retry limit reached")


def persist_checkpoint_comments(client: GitHubClient, owner: str, repo: str, issue_number: int, current: dict) -> int:
    comments = issue_comments(client, owner, repo, issue_number)
    existing_by_index = {}
    for comment in comments:
        if (comment.get("user") or {}).get("login") not in {"frbread7", "github-actions[bot]"}:
            continue
        match = STATE_MARKER_RE.search(comment.get("body", ""))
        if match:
            existing_by_index[int(match.group(2))] = comment
    chunks = _encode_checkpoint(current)
    for index, body in enumerate(chunks, 1):
        if index in existing_by_index:
            issue_write(client, api_url(f"/repos/{owner}/{repo}/issues/comments/{existing_by_index[index]['id']}"), "PATCH", {"body": body})
        else:
            issue_write(client, api_url(f"/repos/{owner}/{repo}/issues/{issue_number}/comments"), "POST", {"body": body})
    return len(chunks)


def update_tracking_issue(client: GitHubClient, owner: str, repo: str, current: dict, new_changes: list[dict], report: str, issue=None) -> str:
    if not client.token:
        raise ReferenceError("GITHUB_TOKEN is required to persist the deduplicated tracker checkpoint")
    issue_number = issue["number"] if issue else None
    fingerprint = change_fingerprint(new_changes)
    issue_result = ""
    if issue and DELTA_MARKER_RE.search(issue.get("body", "")):
        if DELTA_MARKER_RE.search(issue.get("body", "")).group(1) == fingerprint:
            issue_result = f"report already recorded in issue #{issue['number']}"
    if not issue_result:
        concise_report = report.rstrip()
        if len(concise_report) > MAX_TRACKER_BODY_CHARS:
            concise_report = concise_report[:MAX_TRACKER_BODY_CHARS].rsplit("\n", 1)[0]
            concise_report += "\n\n_The report was capped for issue-size safety. See the Actions summary and `reference-intelligence-report` artifact for the complete change list._"
        visible = f"{ISSUE_MARKER}\n\n{concise_report}\n\n---\n\nThis single issue reports newly observed upstream revisions. Its comments retain the last observed source inventory so weekly runs compare incrementally. The checked-in inventory remains the last reviewed baseline. Roadmaps, book records, and editorial decisions require explicit repository review.\n\n<!-- MY_LIBRARY_REFERENCE_DELTA_V1:{fingerprint} -->"
        body = {"title": "Upstream reference intelligence — review tracker", "body": visible}
        if issue and issue.get("state") == "closed":
            body["state"] = "open"
        if issue_number is None:
            request_url = api_url(f"/repos/{owner}/{repo}/issues")
            method = "POST"
        else:
            request_url = api_url(f"/repos/{owner}/{repo}/issues/{issue_number}")
            method = "PATCH"
        result = issue_write(client, request_url, method, body)
        issue_number = result["number"]
        issue_result = ("created" if method == "POST" else "updated") + f" issue #{issue_number}"
    chunk_count = persist_checkpoint_comments(client, owner, repo, issue_number, current)
    return f"{issue_result}; persisted current observation checkpoint in {chunk_count} comment(s)"


def observation_revision_changed(previous: dict, current: dict) -> bool:
    if previous.get("upstream", {}).get("catalogHeadSha") != current.get("upstream", {}).get("catalogHeadSha"):
        return True
    old = {item.get("id"): item for item in previous.get("books", []) if isinstance(item, dict)}
    new = {item.get("id"): item for item in current.get("books", []) if isinstance(item, dict)}
    if set(old) != set(new):
        return True
    for book_id in old:
        before, after = old[book_id], new[book_id]
        if before.get("status") != after.get("status") or (before.get("repository") or {}).get("headSha") != (after.get("repository") or {}).get("headSha"):
            return True
    return False


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ReferenceError(f"{path} must contain a JSON object")
    return data


def inventory_command(args) -> int:
    previous = load_json(Path(args.previous)) if args.previous and Path(args.previous).exists() else None
    inventory = current_inventory(GitHubClient(args.token), previous=previous)
    write_json(Path(args.output), inventory)
    print(f"Inspected {inventory['upstream']['entryCount']} catalog entries and {inventory['upstream']['publishedRepositoryCount']} published repositories at {inventory['upstream']['catalogHeadSha']}.")
    return 0


def validate_command(args) -> int:
    inventory = load_json(Path(args.inventory))
    validate_inventory(inventory)
    reviews = load_json(Path(args.decisions))
    validate_review_records(reviews, inventory)
    provenance = load_json(Path(args.provenance))
    validate_provenance_records(provenance)
    print(f"Validated {len(inventory['books'])} upstream references, {len(reviews['decisions'])} editorial assessments, and {len(provenance['works'])} provenance audits.")
    return 0


def project_review_command(args) -> int:
    inventory = load_json(Path(args.inventory))
    validate_inventory(inventory)
    reviews = load_json(Path(args.decisions))
    decision = validate_project_gate(args.project_id, reviews, inventory)
    print(f"Editorial outcome: {decision['outcome']} ({decision['confidence']} confidence)")
    print(f"Project: {decision['title']} [{decision['branch']}]")
    print(f"Target audience: {decision['targetAudience']}")
    print(f"Differentiated value: {decision['uniqueValue']}")
    print(f"Development strategy: {decision['developmentStrategy']}")
    print("Reference revisions:")
    for source in decision["sourceRevisions"]:
        print(f"- {source['bookId']}@{source['observedSha']} ({source['sourceUrl']})")
    print("Reuse plan:")
    for item in decision["reusePlan"]:
        print(f"- {item}")
    if decision["unresolvedQuestions"]:
        print("Unresolved questions:")
        for item in decision["unresolvedQuestions"]:
            print(f"- {item}")
    print("This is an internal editorial record, not legal advice or a rights certification.")
    return 0


def monitor_command(args) -> int:
    client = GitHubClient(args.token)
    baseline = load_json(Path(args.baseline))
    validate_inventory(baseline)
    issue = None
    issue_state = None
    if args.persist_issue:
        issue = find_tracking_issue(client, args.owner, args.repo)
        if issue:
            issue_state = _decode_checkpoint(issue_comments(client, args.owner, args.repo, issue["number"]))
    elif args.checkpoint_input and Path(args.checkpoint_input).exists():
        issue_state = load_json(Path(args.checkpoint_input))
        validate_inventory(issue_state)
    previous_scan = issue_state or baseline
    current = current_inventory(client, previous=previous_scan)
    reviews = load_json(Path(args.decisions))
    new_changes = compare_inventories(previous_scan, current, reviews)
    all_unreviewed_changes = compare_inventories(baseline, current, reviews)
    report = summarize_changes(all_unreviewed_changes, current)
    if args.persist_issue:
        report += f"\n\nNewly detected since the previous successful monitor checkpoint: **{len(new_changes)} change(s)**. The full list above is measured against the last checked-in review baseline.\n"
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "observed-inventory.json", current)
    write_json(output / "changes.json", {
        "schemaVersion": 1,
        "generatedAt": current["upstream"]["lastSuccessfulInspectionAt"],
        "newChangeCount": len(new_changes),
        "newChanges": new_changes,
        "unreviewedChangeCount": len(all_unreviewed_changes),
        "unreviewedChanges": all_unreviewed_changes,
    })
    (output / "report.md").write_text(report, encoding="utf-8")
    issue_result = "not requested"
    if args.persist_issue:
        if new_changes:
            issue_result = update_tracking_issue(client, args.owner, args.repo, current, new_changes, report, issue)
        elif issue and observation_revision_changed(previous_scan, current):
            chunks = persist_checkpoint_comments(client, args.owner, args.repo, issue["number"], current)
            issue_result = f"checkpoint advanced in issue #{issue['number']} ({chunks} comment(s)); no material content or rights changes to report"
        else:
            issue_result = "no new changes since the monitor checkpoint; tracker left untouched"
    print(report, end="")
    print(f"Tracking issue: {issue_result}")
    print(f"Detected {len(new_changes)} new and {len(all_unreviewed_changes)} total unreviewed change(s); wrote report artifacts under {output}.")
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as stream:
            stream.write(f"new_change_count={len(new_changes)}\n")
            stream.write(f"unreviewed_change_count={len(all_unreviewed_changes)}\n")
            stream.write(f"inspection_time={current['upstream']['lastSuccessfulInspectionAt']}\n")
            stream.write(f"tracking_issue={issue_result}\n")
            stream.write(f"report_path={output / 'report.md'}\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inventory_parser = sub.add_parser("inventory", help="create/update a source-fact inventory from live public repositories")
    inventory_parser.add_argument("--output", required=True)
    inventory_parser.add_argument("--previous")
    inventory_parser.add_argument("--token", default=None)
    inventory_parser.set_defaults(func=inventory_command)

    validate_parser = sub.add_parser("validate", help="validate inventory, editorial decisions, and provenance audit locally")
    validate_parser.add_argument("--inventory", default=str(INVENTORY_PATH))
    validate_parser.add_argument("--decisions", default=str(REVIEWS_PATH))
    validate_parser.add_argument("--provenance", default=str(PROVENANCE_PATH))
    validate_parser.set_defaults(func=validate_command)

    review_parser = sub.add_parser("review-project", help="show and validate the recorded reference/differentiation gate before starting a book")
    review_parser.add_argument("--project-id", required=True)
    review_parser.add_argument("--inventory", default=str(INVENTORY_PATH))
    review_parser.add_argument("--decisions", default=str(REVIEWS_PATH))
    review_parser.set_defaults(func=project_review_command)

    monitor_parser = sub.add_parser("monitor", help="incrementally compare upstream revisions and produce a concise review report")
    monitor_parser.add_argument("--baseline", default=str(INVENTORY_PATH))
    monitor_parser.add_argument("--decisions", default=str(REVIEWS_PATH))
    monitor_parser.add_argument("--output-dir", default="reference-report")
    monitor_parser.add_argument("--checkpoint-input", help="optional inventory JSON from a prior tracker checkpoint")
    monitor_parser.add_argument("--token", default=None)
    monitor_parser.add_argument("--persist-issue", action="store_true")
    monitor_parser.add_argument("--owner", default="frbread7")
    monitor_parser.add_argument("--repo", default="books")
    monitor_parser.add_argument("--github-output")
    monitor_parser.set_defaults(func=monitor_command)

    args = parser.parse_args()
    try:
        return args.func(args)
    except (ReferenceError, OSError, json.JSONDecodeError) as exc:
        print(f"reference_intelligence: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
