#!/usr/bin/env python3
"""Serve the flat Pages artifact under its real /books/ project prefix."""
from io import BytesIO
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

SITE = Path(__file__).resolve().parents[1] / "site"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def translate_path(self, path):
        url_path = urlsplit(path).path
        if not url_path.startswith("/books/"):
            return str(SITE / "404.html")
        relative = url_path[len("/books/"):]
        candidate = super().translate_path("/" + relative)
        if Path(candidate).is_dir():
            index = Path(candidate) / "index.html"
            if index.is_file():
                return str(index)
        return candidate if Path(candidate).is_file() else str(SITE / "404.html")

    def send_head(self):
        url_path = urlsplit(self.path).path
        translated = Path(self.translate_path(url_path))
        if translated == SITE / "404.html" and url_path != "/books/404.html":
            body = (SITE / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return BytesIO(body)
        return super().send_head()

    def log_message(self, fmt, *args):
        if " 404 " in fmt:
            super().log_message(fmt, *args)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 4173), Handler).serve_forever()
