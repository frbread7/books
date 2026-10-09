import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class StaticSiteContractTests(unittest.TestCase):
    def test_flat_routes_exist_and_load_shared_shell(self):
        expected = {"index.html", "library.html", "categories.html", "roadmap.html", "paths.html", "experiments.html", "book.html", "feedback.html", "404.html"}
        self.assertTrue(expected.issubset({p.name for p in SITE.glob("*.html")}))
        for route in expected:
            html = (SITE / route).read_text(encoding="utf-8")
            self.assertRegex(html, r'<html lang="en" data-page="')
            self.assertIn('<main id="main"', html)
            self.assertIn('class="skip-link" href="#main"', html)
            self.assertIn("./css/style.css", html)
            self.assertIn("./js/app.js", html)

    def test_static_local_assets_resolve(self):
        for html_file in SITE.glob("*.html"):
            content = html_file.read_text(encoding="utf-8")
            for ref in re.findall(r'(?:href|src)="(\./[^"?#]+)', content):
                target = SITE / ref.removeprefix("./")
                self.assertTrue(target.is_file(), f"{html_file.name} references missing {ref}")

    def test_base_path_is_centralized_and_not_root_relative(self):
        paths = (SITE / "js" / "paths.js").read_text(encoding="utf-8")
        self.assertIn('new URL("./", document.baseURI)', paths)
        self.assertIn("siteUrl", paths)
        for file in [*SITE.glob("*.html"), *SITE.glob("js/*.js"), *SITE.glob("css/*.css")]:
            content = file.read_text(encoding="utf-8")
            content = content.replace('<base href="/books/">', "")
            self.assertNotRegex(content, r'(?:href|src)="/(?!/)', f"root-relative link in {file}")
            self.assertNotIn("books.euiyun.com", content)
            self.assertNotIn("cloudflare", content.lower())

    def test_catalog_count_roadmap_separation_and_verified_experiments(self):
        books = json.loads((SITE / "data" / "books.json").read_text(encoding="utf-8"))
        roadmap = json.loads((SITE / "data" / "roadmap.json").read_text(encoding="utf-8"))
        pmicbook = next(book for book in books if book["id"] == "pmicbook")
        self.assertEqual(pmicbook["status"], "published")
        self.assertEqual(pmicbook["chapterCount"], 25)
        self.assertEqual(len(pmicbook["chapters"]), 25)
        self.assertEqual(len(pmicbook["experiments"]), 4)
        self.assertEqual(pmicbook["languageUrls"]["ko"], "https://frbread7.github.io/pmicbook/ko/")
        self.assertTrue(all(b["status"] == "planned" for b in roadmap["books"]))
        self.assertEqual(len({x["id"] for x in pmicbook["experiments"]}), 4)
        for item in pmicbook["experiments"]:
            self.assertTrue(item["url"].startswith("https://frbread7.github.io/pmicbook/"))
            self.assertIn("#", item["url"])
            self.assertEqual(item["verification"]["checkedUrl"], item["url"])
            self.assertEqual(item["verification"]["httpStatus"], 200)
            self.assertIs(item["verification"]["fragmentFound"], True)
        self.assertEqual(sum(b["chapterCount"] for b in books if b["status"] == "published"), sum(len(b["chapters"]) for b in books if b["status"] == "published"))

    def test_light_theme_muted_and_copper_tokens_meet_normal_text_contrast(self):
        css = (SITE / "css" / "style.css").read_text(encoding="utf-8")
        root = css.split("}", 1)[0]
        tokens = {name: value for name, value in re.findall(r"--(muted|copper):(#(?:[0-9a-fA-F]{6}))", root)}
        surfaces = ["#f4f3ef", "#fffefa", "#edf2ed", "#d9e5df", "#d9e4dc", "#e7e9e3", "#e8eae4", "#e7ece7", "#e8edf7", "#e9c8ad", "#e9e4d9", "#ecebea", "#edf0ed", "#f5eee0", "#f7f4ed", "#fff2e9"]

        def luminance(value):
            channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
            return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]

        for token in ("muted", "copper"):
            foreground = luminance(tokens[token])
            for background in surfaces:
                ratio = (max(foreground, luminance(background)) + .05) / (min(foreground, luminance(background)) + .05)
                self.assertGreaterEqual(ratio, 4.5, f"--{token} has {ratio:.2f}:1 contrast on {background}")

    def test_category_maps_and_learning_paths_reference_real_chapters(self):
        books = json.loads((SITE / "data" / "books.json").read_text(encoding="utf-8"))
        categories = json.loads((SITE / "data" / "categories.json").read_text(encoding="utf-8"))
        paths = json.loads((SITE / "data" / "learning-paths.json").read_text(encoding="utf-8"))
        chapters = {book["id"]: {chapter["id"] for chapter in book["chapters"]} for book in books if book["status"] == "published"}
        for category in categories["categories"]:
            for node in category["map"]:
                for connection in node["connections"]:
                    self.assertIn(connection["bookId"], chapters)
                    self.assertIn(connection["chapterId"], chapters[connection["bookId"]])
        for path in paths["paths"]:
            for step in path["steps"]:
                self.assertIn(step["bookId"], chapters)
                self.assertIn(step["chapterId"], chapters[step["bookId"]])

    def test_no_upstream_personal_or_infrastructure_identity_in_deployed_files(self):
        for path in [*SITE.rglob("*.html"), *SITE.rglob("*.js"), *SITE.rglob("*.css"), *SITE.rglob("*.json")]:
            content = path.read_text(encoding="utf-8").lower()
            for forbidden in ("books.euiyun.com", "geniuskey", "cloudflare", "google-client-id", "d1_database"):
                self.assertNotIn(forbidden, content, f"{forbidden} found in deployed file {path.relative_to(SITE)}")


if __name__ == "__main__":
    unittest.main()
