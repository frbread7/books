#!/usr/bin/env python3
"""Check published experiment URLs and anchors on their declared production site."""
from __future__ import annotations

import argparse
from datetime import date
from html.parser import HTMLParser
import functools
import http.client
import hashlib
import ipaddress
import json
import re
import socket
import stat
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parent))
import book_factory

MAX_BYTES = 1_000_000
TIMEOUT = 8
MAX_REDIRECTS = 4
IMMUTABLE_REVISION = re.compile(r"^[0-9a-f]{40}$")


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
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError(f"URL must use HTTPS without credentials: {value}")
    try:
        port = url.port
    except ValueError as exc:
        raise ValueError(f"URL has an invalid port: {value}") from exc
    if url.hostname.lower() != (root.hostname or "").lower() or port not in (None, 443):
        raise ValueError(f"URL host must match the declared production host: {value}")
    if not book_factory.path_is_within_production(url.path, root.path):
        raise ValueError(f"URL path must remain under the declared production path: {value}")
    return url


def public_addresses(host):
    """Resolve once per request and reject the whole result if any address is non-public."""
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)]
        except (OSError, ValueError) as exc:
            raise ValueError(f"URL host could not be resolved safely: {host}") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError(f"URL host must resolve only to public IP addresses: {host}")
    return [str(address) for address in dict.fromkeys(addresses)]


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to a validated IP while preserving the original TLS hostname."""

    def __init__(self, host, *, original_hostname, pinned_address, **kwargs):
        self._original_hostname = original_hostname
        self._pinned_address = pinned_address
        super().__init__(host, **kwargs)

    def connect(self):
        if self._tunnel_host:
            # HTTPConnection connects to the configured proxy and CONNECTs to the
            # numeric pinned IP set on the request by PinnedHTTPSHandler.
            http.client.HTTPConnection.connect(self)
        else:
            self.sock = socket.create_connection(
                (self._pinned_address, self.port),
                timeout=self.timeout,
                source_address=self.source_address,
            )
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self._original_hostname)

    def getresponse(self):
        # urllib always sends Connection: close. Let HTTPResponse's makefile own
        # the socket until the bounded body is read instead of closing it in
        # HTTPConnection.getresponse before our deadline loop can set timeouts.
        self._handoff_to_response = True
        try:
            response = super().getresponse()
            response._library_socket = getattr(self, "_response_socket", None) or self.sock
            return response
        finally:
            self._handoff_to_response = False

    def close(self):
        if getattr(self, "_handoff_to_response", False):
            self._response_socket = self.sock
            self.sock = None
            return
        super().close()


class PinnedHTTPSHandler(HTTPSHandler):
    def https_open(self, req):
        target = urlparse(req.full_url)
        original_hostname = target.hostname
        if not original_hostname:
            raise ValueError("HTTPS request has no hostname")
        deadline = getattr(req, "_library_deadline", None)
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("experiment verification exceeded its 8-second deadline")
            req.timeout = min(req.timeout or TIMEOUT, remaining)
        address = public_addresses(original_hostname)[0]
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("experiment verification exceeded its 8-second deadline")
            req.timeout = min(req.timeout or TIMEOUT, remaining)
        # ProxyHandler still decides whether to use the configured proxy and
        # still connects to it normally. Only the CONNECT destination is pinned.
        if getattr(req, "_tunnel_host", None):
            req._tunnel_host = address
        req.add_unredirected_header("Host", original_hostname)
        connection = functools.partial(
            PinnedHTTPSConnection,
            original_hostname=original_hostname,
            pinned_address=address,
        )
        return self.do_open(connection, req, context=self._context)


def response_socket(response):
    """Return the socket explicitly handed off by PinnedHTTPSConnection."""
    return getattr(response, "_library_socket", None)


def read_bounded_body(response, deadline):
    body = bytearray()
    sock = response_socket(response)
    if sock is None:
        raise ValueError("cannot enforce the response deadline because urllib exposed no response socket")
    while len(body) <= MAX_BYTES:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("experiment response exceeded its 8-second overall deadline")
        sock.settimeout(remaining)
        size = min(64 * 1024, MAX_BYTES + 1 - len(body))
        try:
            chunk = response.read1(size)
        except (TimeoutError, socket.timeout) as exc:
            raise TimeoutError("experiment response exceeded its 8-second overall deadline") from exc
        if not chunk:
            break
        body.extend(chunk)
    if len(body) > MAX_BYTES:
        raise ValueError(f"experiment response exceeded {MAX_BYTES} bytes")
    return bytes(body)


def checked_source_revision(value):
    if not isinstance(value, str) or not IMMUTABLE_REVISION.fullmatch(value):
        raise ValueError("source revision must be a full 40-character lowercase Git commit SHA; repository provenance is caller-attested")
    return value


class SafeRedirects(HTTPRedirectHandler):
    max_redirections = MAX_REDIRECTS

    def __init__(self, production_url):
        super().__init__()
        self.production_url = production_url

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_https_url(newurl, self.production_url)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and hasattr(req, "_library_deadline"):
            redirected._library_deadline = req._library_deadline
        return redirected


def check_one(item, production_url, source_revision, opener=None):
    source_revision = checked_source_revision(source_revision)
    target = public_https_url(item["url"], production_url)
    if not target.fragment:
        raise ValueError(f"experiment {item['id']} has no fragment")
    if opener is None:
        opener = build_opener(SafeRedirects(production_url), PinnedHTTPSHandler())
    request = Request(item["url"], headers={"User-Agent": "MyLibrary-ExperimentVerifier/1.0", "Accept": "text/html"})
    deadline = time.monotonic() + TIMEOUT
    request._library_deadline = deadline
    with opener.open(request, timeout=TIMEOUT) as response:
        try:
            status = response.getcode()
            if status != 200:
                raise ValueError(f"experiment {item['id']} returned HTTP {status}")
            body = read_bounded_body(response, deadline)
        finally:
            response_sock = response_socket(response)
            if response_sock is not None:
                response_sock.close()
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
        "sourceRevisionAttestation": "Caller-attested deployment source revision; this verifier checks SHA format, not repository membership.",
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
    parser.add_argument("--source-revision", required=True, help="full 40-character deployment commit SHA (caller-attested from deployment metadata)")
    parser.add_argument("--write-back", action="store_true", help="atomically add successful live-check evidence to the manifest")
    args = parser.parse_args()
    try:
        path = args.manifest.resolve()
        book = book_factory.read_json(path)
        if not isinstance(book, dict) or not isinstance(book.get("experiments"), list):
            raise ValueError("manifest must contain an experiments list")
        source_revision = checked_source_revision(args.source_revision)
        # Permit a draft with experiments to be checked before it is made publishable.
        preflight = json.loads(json.dumps(book))
        preflight["status"] = "in-progress"
        preflight.pop("publicationEvidence", None)
        for item in preflight["experiments"]:
            if isinstance(item, dict):
                item.pop("verification", None)
        book_factory.validate_manifest(preflight)
        evidence = [check_one(item, book["productionUrl"], source_revision) for item in book["experiments"]]
        candidate = json.loads(json.dumps(book))
        for item, checked in zip(candidate["experiments"], evidence):
            item["verification"] = checked
        if candidate.get("status") == "published":
            candidate.setdefault("publicationEvidence", {})["productionRevision"] = source_revision
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
