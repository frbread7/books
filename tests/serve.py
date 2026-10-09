#!/usr/bin/env python3
"""Serve the flat Pages artifact under its real /books/ project prefix."""
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
        return super().translate_path("/" + relative)

    def log_message(self, fmt, *args):
        if " 404 " in fmt:
            super().log_message(fmt, *args)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 4173), Handler).serve_forever()
