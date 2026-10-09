import hashlib
from types import SimpleNamespace
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
        self.offset = 0
        self._library_socket = FakeSocket()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return self.status

    def read1(self, count):
        chunk = self.body[self.offset:self.offset + count]
        self.offset += len(chunk)
        return chunk


class FakeSocket:
    def __init__(self):
        self.timeouts = []
        self.closed = False

    def settimeout(self, value):
        self.timeouts.append(value)

    def close(self):
        self.closed = True


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
        for path in ("/book/../admin", "/book/%2e%2e/admin", "/book/%252e%252e/admin", "/book/%5c..%5cadmin", "/booksibling/admin"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, "path must remain"):
                    verify_experiments.public_https_url("https://example.test" + path, self.production)

    @patch("verify_experiments.socket.getaddrinfo", return_value=[(None, None, None, None, ("93.184.216.34", 443))])
    def test_https_handler_pins_proxy_tunnel_but_keeps_origin_host_and_ca_context(self, dns):
        class CapturingHandler(verify_experiments.PinnedHTTPSHandler):
            def do_open(self, connection, request, **kwargs):
                self.connection_factory = connection
                self.request = request
                self.open_kwargs = kwargs
                return "captured"

        handler = CapturingHandler()
        request = __import__("urllib.request", fromlist=["Request"]).Request(self.item["url"])
        request.set_proxy("proxy.example:8080", "https")
        self.assertEqual(handler.https_open(request), "captured")
        dns.assert_called_once_with("example.test", 443, type=verify_experiments.socket.SOCK_STREAM)
        self.assertEqual(request._tunnel_host, "93.184.216.34")
        self.assertEqual(request.get_header("Host"), "example.test")
        connection = handler.connection_factory(
            request.host,
            timeout=3,
            context=handler._context,
        )
        self.assertEqual(connection.host, "proxy.example")
        self.assertEqual(connection.port, 8080)
        self.assertEqual(connection._pinned_address, "93.184.216.34")
        self.assertEqual(connection._original_hostname, "example.test")
        self.assertIs(handler.open_kwargs["context"], handler._context)
        self.assertNotIn("check_hostname", handler.open_kwargs)

    @patch("verify_experiments.socket.create_connection")
    def test_direct_connection_uses_pinned_address_and_original_tls_name(self, create_connection):
        raw_socket = object()
        wrapped_socket = object()
        create_connection.return_value = raw_socket
        connection = verify_experiments.PinnedHTTPSConnection(
            "example.test", original_hostname="example.test", pinned_address="93.184.216.34", timeout=5
        )
        with patch.object(connection._context, "wrap_socket", return_value=wrapped_socket) as wrap_socket:
            connection.connect()
        create_connection.assert_called_once_with(("93.184.216.34", 443), timeout=5, source_address=None)
        wrap_socket.assert_called_once_with(raw_socket, server_hostname="example.test")
        self.assertIs(connection.sock, wrapped_socket)

    def test_proxy_connection_tunnels_to_pinned_ip_and_keeps_original_tls_name(self):
        connection = verify_experiments.PinnedHTTPSConnection(
            "proxy.example:8080", original_hostname="example.test", pinned_address="93.184.216.34", timeout=5
        )
        connection.set_tunnel("93.184.216.34", port=443)
        raw_socket = object()
        wrapped_socket = object()
        with patch("http.client.HTTPConnection.connect") as proxy_connect, patch.object(
            connection._context, "wrap_socket", return_value=wrapped_socket
        ) as wrap_socket:
            connection.sock = raw_socket
            connection.connect()
        proxy_connect.assert_called_once_with(connection)
        wrap_socket.assert_called_once_with(raw_socket, server_hostname="example.test")
        self.assertEqual(connection._tunnel_host, "93.184.216.34")
        self.assertIs(connection.sock, wrapped_socket)

    def test_response_handoff_keeps_socket_open_for_deadline_bounded_body_read(self):
        class TrackedSocket:
            closed = False

            def close(self):
                self.closed = True

        connection = verify_experiments.PinnedHTTPSConnection(
            "example.test", original_hostname="example.test", pinned_address="93.184.216.34"
        )
        raw_socket = TrackedSocket()
        connection.sock = raw_socket
        response = SimpleNamespace()
        with patch(
            "http.client.HTTPConnection.getresponse",
            autospec=True,
            side_effect=lambda instance: (instance.close(), response)[1],
        ):
            self.assertIs(connection.getresponse(), response)
        self.assertIsNone(connection.sock)
        self.assertFalse(raw_socket.closed)
        self.assertIs(response._library_socket, raw_socket)

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

    def test_body_read_uses_remaining_monotonic_deadline_as_socket_timeout(self):
        response = FakeResponse(b"abcdef")
        times = iter((1.0, 2.5, 3.0))
        with patch("verify_experiments.time.monotonic", side_effect=lambda: next(times)):
            body = verify_experiments.read_bounded_body(response, deadline=9.0)
        self.assertEqual(body, b"abcdef")
        self.assertEqual(response._library_socket.timeouts, [8.0, 6.5])

    def test_body_read_fails_when_whole_response_deadline_has_expired(self):
        response = FakeResponse(b"abcdef")
        with patch("verify_experiments.time.monotonic", side_effect=(0.0, 9.0)):
            with self.assertRaisesRegex(TimeoutError, "overall deadline"):
                verify_experiments.read_bounded_body(response, deadline=8.0)
        self.assertEqual(response._library_socket.timeouts, [8.0])

    @patch("verify_experiments.socket.getaddrinfo", return_value=[
        (None, None, None, None, ("93.184.216.34", 443)),
        (None, None, None, None, ("127.0.0.1", 443)),
    ])
    def test_any_non_public_dns_answer_rejects_the_request(self, _dns):
        with self.assertRaisesRegex(ValueError, "only to public IP addresses"):
            verify_experiments.public_addresses("example.test")


if __name__ == "__main__":
    unittest.main()
