#!/usr/bin/env python3
"""Check published experiment URLs and anchors on their declared production site."""
from __future__ import annotations

import argparse
from datetime import date
from html.parser import HTMLParser
import hashlib
import ipaddress
import json
import re
import socket
import stat
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_factory

MAX_BYTES = 1_000_000
TIMEOUT = 8
MAX_REDIRECTS = 4
IMMUTABLE_REVISION = re.compile(r"^(?:v[0-9][0-9A-Za-z.+-]*|[0-9a-fA-F]{7,64})$")


class FragmentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.names = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.names.add(values["id"])
        if values.get("name"):
            self.names.add(values["name"])


def public_https_url(value, production_url):
    url = urlparse(value)
    root = urlparse(production_url)
    prefix = root.path.rstrip("/") + "/"
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError(f"URL must use HTTPS without credentials: {value}")
    if url.hostname.lower() != (root.hostname or "").lower() or url.port not in (None, 443):
        raise ValueError(f"URL host must match the declared production host: {value}")
    if not (url.path == root.path.rstrip("/") or url.path.startswith(prefix)):
        raise ValueError(f"URL path must remain under the declared production path: {value}")
    host = url.hostname.strip("[]")
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)]
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError(f"URL host must resolve only to public IP addresses: {host}")
    return url


class SafeRedirects(HTTPRedirectHandler):
    max_redirections = MAX_REDIRECTS

    def __init__(self, production_url):
        super().__init__()
        self.production_url = production_url

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_https_url(newurl, self.production_url)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def check_one(item, production_url, source_revision, opener=None):
    target = public_https_url(item["url"], production_url)
    if not target.fragment:
        raise ValueError(f"experiment {item['id']} has no fragment")
    if opener is None:
        opener = build_opener(SafeRedirects(production_url))
    request = Request(item["url"], headers={"User-Agent": "MyLibrary-ExperimentVerifier/1.0", "Accept": "text/html"})
    with opener.open(request, timeout=TIMEOUT) as response:
        status = response.getcode()
        if status != 200:
            raise ValueError(f"experiment {item['id']} returned HTTP {status}")
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError(f"experiment {item['id']} response exceeded {MAX_BYTES} bytes")
    parser = FragmentParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    fragment_found = target.fragment in parser.names
    if not fragment_found:
        raise ValueError(f"experiment {item['id']} fragment #{target.fragment} was not found in the returned HTML")
    return {
        "checkedAt": date.today().isoformat(),
        "checkedUrl": item["url"],
        "httpStatus": status,
        "fragmentFound": True,
        "contentSha256": hashlib.sha256(body).hexdigest(),
        "sourceRevision": source_revision,
        "evidence": f"Live HTTPS response; HTTP {status}; fragment #{target.fragment} present in HTML; SHA-256 recorded.",
    }


def atomic_write(path, data):
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        stream.write(content)
        temp_path = Path(stream.name)
    temp_path.chmod(mode)
    temp_path.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source-revision", required=True, help="release tag or immutable revision being verified")
    parser.add_argument("--write-back", action="store_true", help="atomically add successful live-check evidence to the manifest")
    args = parser.parse_args()
    try:
        path = args.manifest.resolve()
        book = book_factory.read_json(path)
        if not isinstance(book, dict) or not isinstance(book.get("experiments"), list):
            raise ValueError("manifest must contain an experiments list")
        if not isinstance(args.source_revision, str) or not IMMUTABLE_REVISION.fullmatch(args.source_revision):
            raise ValueError("source revision must be an immutable version tag (for example v1.0.0) or a Git commit ID")
        # Permit a draft with experiments to be checked before it is made publishable.
        preflight = json.loads(json.dumps(book))
        preflight["status"] = "in-progress"
        preflight.pop("publicationEvidence", None)
        book_factory.validate_manifest(preflight)
        evidence = [check_one(item, book["productionUrl"], args.source_revision) for item in book["experiments"]]
        candidate = json.loads(json.dumps(book))
        for item, checked in zip(candidate["experiments"], evidence):
            item["verification"] = checked
        if args.write_back:
            book_factory.validate_manifest(candidate)
            atomic_write(path, candidate)
        print(json.dumps({"book": book.get("id"), "sourceRevision": args.source_revision, "experiments": evidence}, ensure_ascii=False, indent=2))
    except (book_factory.ManifestError, OSError, ValueError, KeyError, TimeoutError) as exc:
        print(f"verify_experiments: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
