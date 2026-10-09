import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import verify_experiments


class FakeResponse:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return self.status

    def read(self, count):
        return self.body[:count]


class FakeOpener:
    def __init__(self, body, status=200):
        self.response = FakeResponse(body, status)

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return self.response


class VerifyExperimentsTests(unittest.TestCase):
    def setUp(self):
        self.item = {"id": "sample/experiment", "url": "https://example.test/book/chapter.html#experiment"}
        self.production = "https://example.test/book/"
        self.revision = "a5290ff0ed0c785c6fc5bc0d7fa966b252710883"

    @patch("verify_experiments.socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))])
    def test_success_records_live_status_fragment_and_content_hash(self, _dns):
        body = b'<html><section id="experiment"></section></html>'
        evidence = verify_experiments.check_one(self.item, self.production, self.revision, FakeOpener(body))
        self.assertEqual(evidence["checkedUrl"], self.item["url"])
        self.assertEqual(evidence["httpStatus"], 200)
        self.assertTrue(evidence["fragmentFound"])
        self.assertEqual(evidence["contentSha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(evidence["sourceRevision"], self.revision)
        self.assertIn("Caller-attested", evidence["sourceRevisionAttestation"])

    @patch("verify_experiments.socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))])
    def test_missing_fragment_is_rejected(self, _dns):
        with self.assertRaisesRegex(ValueError, "fragment #experiment was not found"):
            verify_experiments.check_one(self.item, self.production, self.revision, FakeOpener(b"<html><p>no anchor</p></html>"))

    def test_redirect_target_cannot_leave_declared_host_or_path(self):
        with self.assertRaisesRegex(ValueError, "host must match"):
            verify_experiments.public_https_url("https://attacker.example/book/", self.production)
        with patch("verify_experiments.socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
            with self.assertRaisesRegex(ValueError, "path must remain"):
                verify_experiments.public_https_url("https://example.test/outside/page.html", self.production)

    def test_encoded_or_literal_dot_segments_cannot_escape_production_path(self):
        for path in ("/book/../admin", "/book/%2e%2e/admin", "/book/%252e%252e/admin", "/booksibling/admin"):
            with self.subTest(path=path), patch("verify_experiments.socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))]):
                with self.assertRaisesRegex(ValueError, "path must remain"):
                    verify_experiments.public_https_url("https://example.test" + path, self.production)

    def test_source_revision_requires_full_commit_sha_and_is_attested(self):
        for invalid in ("v1.0.0", "a5290ff", "z" * 40, "A" * 40):
            with self.subTest(revision=invalid), self.assertRaisesRegex(ValueError, "full 40-character lowercase Git commit SHA"):
                verify_experiments.checked_source_revision(invalid)
        self.assertEqual(verify_experiments.checked_source_revision(self.revision), self.revision)

    @patch("verify_experiments.socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))])
    def test_actual_redirect_handler_rejects_a_different_host(self, _dns):
        from urllib.request import Request
        handler = verify_experiments.SafeRedirects(self.production)
        request = Request(self.item["url"])
        with self.assertRaisesRegex(ValueError, "host must match"):
            handler.redirect_request(request, None, 302, "Found", {}, "https://attacker.example/book/experiment.html")

    @patch("verify_experiments.socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))])
    def test_response_size_is_bounded(self, _dns):
        with self.assertRaisesRegex(ValueError, "exceeded 1000000 bytes"):
            verify_experiments.check_one(self.item, self.production, self.revision, FakeOpener(b"x" * (verify_experiments.MAX_BYTES + 1)))


if __name__ == "__main__":
    unittest.main()
