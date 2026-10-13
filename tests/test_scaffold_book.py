import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import scaffold_book


class ScaffoldBookTests(unittest.TestCase):
    def arguments(self, output, production_url="https://example.test/book/", book_id="fabcontrolbook"):
        return [
            "scaffold_book.py", "--id", book_id, "--title-en", "Sample Book", "--title-ko", "샘플 도서",
            "--subtitle-en", "Engineering", "--subtitle-ko", "공학", "--description-en", "A sample book.",
            "--description-ko", "샘플 도서입니다.", "--repository-url", "https://github.com/example/samplebook",
            "--production-url", production_url, "--out", str(output)
        ]

    def test_production_url_control_character_yaml_injection_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "samplebook"
            injected = "https://example.test/book/\npermissions: contents: write"
            with patch.object(sys, "argv", self.arguments(output, injected)):
                self.assertEqual(scaffold_book.main(), 1)
            self.assertFalse(output.exists())

    def test_generated_workflow_url_rejects_github_expression_syntax(self):
        injected_urls = [
            "https://example.test/book/${{ github.event.issue.title }}",
            "https://example.test/book/$REPOSITORY",
            "https://example.test/book/{template}",
        ]
        for injected in injected_urls:
            with self.subTest(url=injected), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "samplebook"
                with patch.object(sys, "argv", self.arguments(output, injected)):
                    self.assertEqual(scaffold_book.main(), 1)
                self.assertFalse(output.exists())

    def test_production_url_is_emitted_as_quoted_yaml_scalar(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "samplebook"
            with patch.object(sys, "argv", self.arguments(output)):
                self.assertEqual(scaffold_book.main(), 0)
            workflow = (output / ".github/workflows/pages.yml").read_text(encoding="utf-8")
            self.assertIn('url: "https://example.test/book/"', workflow)
            self.assertNotIn("permissions: contents: write", workflow)
            manifest = json.loads((output / "library-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "in-progress")
            self.assertTrue((output / "site/index.html").is_file())
            self.assertTrue((output / "site/assets/covers/fabcontrolbook.svg").is_file())
            site_notice = output / "site/LICENSE-AND-ATTRIBUTION.md"
            self.assertTrue(site_notice.is_file())
            self.assertEqual(site_notice.read_text(encoding="utf-8"), (output / "LICENSE-AND-ATTRIBUTION.md").read_text(encoding="utf-8"))
            self.assertIn('href="./LICENSE-AND-ATTRIBUTION.md"', (output / "site/index.html").read_text(encoding="utf-8"))
            self.assertIn("path: site", workflow)
            self.assertNotIn("path: .", workflow)
            self.assertEqual(workflow.count("pages: write"), 1)
            self.assertEqual(workflow.count("id-token: write"), 1)

    def test_scaffold_requires_reviewed_differentiation_before_creating_files(self):
        for book_id in ("unreviewedbook", "engineeringmathbook"):
            with self.subTest(book_id=book_id), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / book_id
                with patch.object(sys, "argv", self.arguments(output, book_id=book_id)):
                    self.assertEqual(scaffold_book.main(), 1)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
