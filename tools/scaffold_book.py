#!/usr/bin/env python3
"""Create a small independent book repository scaffold without overwriting files."""
import argparse
from html import escape
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def checked_url(value, field):
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(f"{field} must be an HTTPS URL without embedded credentials")


def cover_svg(book_id, title):
    safe_title = escape(title[:30])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 640" role="img" aria-labelledby="title description">
  <title id="title">{safe_title} cover</title>
  <desc id="description">Starter cover artwork. Replace it with original illustrations before publication.</desc>
  <rect width="480" height="640" fill="#193648"/>
  <circle cx="360" cy="145" r="115" fill="#315d6d"/>
  <path d="M68 140h300M68 156h220M68 172h260" stroke="#df8c67" stroke-width="4" opacity=".8"/>
  <rect x="75" y="235" width="330" height="270" rx="10" fill="#f2eee6"/>
  <text x="105" y="295" fill="#bf5836" font-family="monospace" font-size="18">{book_id.upper()}</text>
  <text x="105" y="360" fill="#193648" font-family="Georgia,serif" font-size="34" font-weight="bold">{safe_title}</text>
  <text x="105" y="420" fill="#53616a" font-family="Arial,sans-serif" font-size="16">Replace this starter artwork</text>
  <text x="105" y="452" fill="#53616a" font-family="Arial,sans-serif" font-size="16">with an original cover design.</text>
</svg>
'''


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--slug")
    parser.add_argument("--title-en", required=True)
    parser.add_argument("--title-ko", required=True)
    parser.add_argument("--subtitle-en", required=True)
    parser.add_argument("--subtitle-ko", required=True)
    parser.add_argument("--description-en", required=True)
    parser.add_argument("--description-ko", required=True)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--production-url", required=True)
    parser.add_argument("--category", default="semiconductor")
    parser.add_argument("--languages", default="en", help="comma-separated deployed book languages (en,ko); default en")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        slug = args.slug or args.id
        if not SLUG.fullmatch(args.id) or not SLUG.fullmatch(slug):
            raise ValueError("id and slug must be lowercase URL-safe values using letters, digits, and hyphens")
        for field in ("title_en", "title_ko", "subtitle_en", "subtitle_ko", "description_en", "description_ko", "category"):
            if not getattr(args, field).strip():
                raise ValueError(f"{field.replace('_', '-')} must not be empty")
        checked_url(args.repository_url, "repository URL")
        checked_url(args.production_url, "production URL")
        languages = [item.strip() for item in args.languages.split(",") if item.strip()]
        if not languages or len(set(languages)) != len(languages) or set(languages) - {"en", "ko"}:
            raise ValueError("languages must be a comma-separated unique subset of en,ko")
        output = args.out.resolve()
        if output.exists() and any(output.iterdir()):
            raise ValueError(f"refusing to overwrite non-empty output directory: {output}")
        output.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schemaVersion": 1,
            "id": args.id,
            "slug": slug,
            "title": {"en": args.title_en, "ko": args.title_ko},
            "subtitle": {"en": args.subtitle_en, "ko": args.subtitle_ko},
            "description": {"en": args.description_en, "ko": args.description_ko},
            "category": args.category,
            "tags": [],
            "status": "in-progress",
            "repositoryUrl": args.repository_url,
            "productionUrl": args.production_url,
            "languageUrls": {"en": args.production_url} if languages == ["en"] else {lang: args.production_url.rstrip("/") + ("/ko/" if lang == "ko" else "/") for lang in languages},
            "languages": languages,
            "version": "0.1.0",
            "lastUpdated": date.today().isoformat(),
            "chapterCount": 0,
            "chapters": [],
            "experiments": [],
            "prerequisites": [],
            "relatedBooks": [],
            "attribution": {
                "license": "CHOOSE-AND-RECORD",
                "repositoryUrl": args.repository_url,
                "notes": "Choose appropriate content and code licenses and record all third-party attributions before publication."
            },
            "cover": f"assets/covers/{args.id}.svg",
            "theme": {"accent": "#bf5836", "accentSoft": "#f5e3d8", "motif": "replace-with-original"}
        }
        write(output / "library-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        write(output / f"assets/covers/{args.id}.svg", cover_svg(args.id, args.title_en))
        title_html = escape(args.title_en)
        description_html = escape(args.description_en)
        write(output / "index.html", f'''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{description_html}"><title>{title_html}</title><style>body{{margin:0;background:#f4f3ef;color:#1e2a32;font:16px/1.7 system-ui,sans-serif}}main{{max-width:850px;margin:8vh auto;padding:24px}}img{{float:right;width:min(38vw,220px);margin:0 0 24px 30px;box-shadow:12px 12px #e4d5c9}}h1{{font:500 clamp(38px,7vw,64px)/1.1 Georgia,serif}}p{{max-width:570px;color:#53616a}}.note{{clear:both;padding:14px;border:1px solid #deded7;font-size:13px}}</style></head>
<body><main><img src="./assets/covers/{args.id}.svg" alt="{title_html} starter cover"><p>INDEPENDENT ENGINEERING TEXTBOOK · STARTER</p><h1>{title_html}</h1><p>{description_html}</p><p class="note">This repository is a scaffold, not a finished textbook. Replace this page and cover, author reviewed content, test every experiment, and choose licenses before publication.</p></main></body>
</html>
''')
        write(output / "README.md", f'''# {title_html}

Independent textbook repository scaffold.

This starter is not a finished or reviewed book. Complete the content, tests, original artwork, references, license choice, and attribution before release. The library manifest remains status=in-progress until a production release and checks exist.

Production candidate: {args.production_url}
''')
        write(output / ".github/workflows/pages.yml", f'''name: Deploy textbook
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  deploy:
    environment:
      name: github-pages
      url: {args.production_url}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v4
        with:
          path: .
      - uses: actions/deploy-pages@v4
''')
        write(output / "LICENSE-AND-ATTRIBUTION.md", "# License and attribution\n\nChoose and add a license for the original book text and code before publishing. Record third-party licenses and retain required notices. The portal manifest must describe the resulting license accurately.\n")
    except (OSError, ValueError) as exc:
        print(f"scaffold_book: error: {exc}", file=sys.stderr)
        return 1
    print(f"Created independent in-progress book scaffold at {output}")
    print("No book is registered or published by this command.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
