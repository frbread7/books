import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "scaffold_book.py"


class ScaffoldTests(unittest.TestCase):
    def arguments(self, out):
        return [sys.executable, str(SCRIPT), "--id", "devicephysicsbook", "--title-en", "Device Physics", "--title-ko", "소자 물리", "--subtitle-en", "Semiconductor physics", "--subtitle-ko", "반도체 물리", "--description-en", "A foundations text.", "--description-ko", "기초 교재입니다.", "--repository-url", "https://github.com/frbread7/devicephysicsbook", "--production-url", "https://frbread7.github.io/devicephysicsbook/", "--out", str(out)]

    def test_scaffold_creates_in_progress_separate_book(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "newbook"
            result = subprocess.run(self.arguments(output), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "library-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "in-progress")
            self.assertEqual(manifest["chapterCount"], 0)
            self.assertTrue((output / ".github/workflows/pages.yml").is_file())
            self.assertIn("No book is registered", result.stdout)

    def test_scaffold_refuses_to_overwrite_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            result = subprocess.run(self.arguments(output), capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
