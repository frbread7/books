import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import scaffold_book


class ScaffoldBookTests(unittest.TestCase):
    def arguments(self, output, production_url="https://example.test/book/"):
        return [
            "scaffold_book.py", "--id", "samplebook", "--title-en", "Sample Book", "--title-ko", "샘플 도서",
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


if __name__ == "__main__":
    unittest.main()
