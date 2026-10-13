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
        return [sys.executable, str(SCRIPT), "--id", "fabcontrolbook", "--title-en", "Fab Control", "--title-ko", "팹 제어", "--subtitle-en", "Manufacturing process control", "--subtitle-ko", "제조 공정 제어", "--description-en", "A manufacturing process control text.", "--description-ko", "제조 공정 제어 교재입니다.", "--repository-url", "https://github.com/frbread7/fabcontrolbook", "--production-url", "https://frbread7.github.io/fabcontrolbook/", "--out", str(out)]

    def test_scaffold_creates_in_progress_separate_book(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "newbook"
            result = subprocess.run(self.arguments(output), capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "library-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "in-progress")
            self.assertEqual(manifest["chapterCount"], 0)
            workflow = (output / ".github/workflows/pages.yml").read_text(encoding="utf-8")
            self.assertIn("runs-on: ubuntu-24.04", workflow)
            self.assertIn("actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0", workflow)
            self.assertNotIn("ubuntu-latest", workflow)
            self.assertNotIn("actions/checkout@v4", workflow)
            self.assertTrue((output / "site/index.html").is_file())
            self.assertTrue((output / "site/assets/covers/fabcontrolbook.svg").is_file())
            site_notice = output / "site/LICENSE-AND-ATTRIBUTION.md"
            self.assertTrue(site_notice.is_file())
            self.assertEqual(site_notice.read_text(encoding="utf-8"), (output / "LICENSE-AND-ATTRIBUTION.md").read_text(encoding="utf-8"))
            self.assertIn("grants no reuse rights", site_notice.read_text(encoding="utf-8"))
            self.assertIn('href="./LICENSE-AND-ATTRIBUTION.md"', (output / "site/index.html").read_text(encoding="utf-8"))
            self.assertFalse((output / "index.html").exists())
            self.assertIn("path: site", workflow)
            self.assertNotIn("path: .", workflow)
            self.assertIn("actions/configure-pages@983d7736d9b0ae728b81ab479565c72886d7745b # v5.0.0", workflow)
            self.assertIn("actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b # v4.0.0", workflow)
            self.assertIn("actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e # v4.0.5", workflow)
            self.assertLess(workflow.index("  deploy:"), workflow.index("      pages: write"))
            self.assertLess(workflow.index("  deploy:"), workflow.index("      id-token: write"))
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
