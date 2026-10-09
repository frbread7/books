import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import book_factory

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "catalog" / "books" / "pmicbook.json"


class BookFactoryTests(unittest.TestCase):
    def setUp(self):
        self.book = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_published_pmic_manifest_has_verified_release_and_complete_index(self):
        result = book_factory.validate_manifest(self.book)
        self.assertEqual(result["id"], "pmicbook")
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["chapterCount"], 25)
        self.assertEqual(len(result["experiments"]), 4)

    def test_duplicate_chapter_is_rejected(self):
        self.book["chapters"].append(self.book["chapters"][0])
        self.book["chapterCount"] += 1
        with self.assertRaisesRegex(book_factory.ManifestError, "duplicate chapter id"):
            book_factory.validate_manifest(self.book)

    def test_published_without_evidence_is_rejected(self):
        self.book.pop("publicationEvidence")
        with self.assertRaisesRegex(book_factory.ManifestError, "schema validation.*publicationEvidence"):
            book_factory.validate_manifest(self.book)

    def test_experiment_requires_a_verified_anchor(self):
        self.book["experiments"][0]["url"] = self.book["productionUrl"]
        with self.assertRaisesRegex(book_factory.ManifestError, "verified anchor"):
            book_factory.validate_manifest(self.book)

    def test_duplicate_manifest_ids_and_slugs_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            manifests = Path(directory)
            (manifests / "pmicbook.json").write_text(json.dumps(self.book), encoding="utf-8")
            duplicate_id = dict(self.book)
            (manifests / "second.json").write_text(json.dumps(duplicate_id), encoding="utf-8")
            with patch.object(book_factory, "MANIFESTS", manifests):
                with self.assertRaisesRegex(book_factory.ManifestError, "duplicate book id"):
                    book_factory.all_books()
            duplicate_slug = dict(self.book)
            duplicate_slug["id"] = "otherbook"
            (manifests / "second.json").write_text(json.dumps(duplicate_slug), encoding="utf-8")
            with patch.object(book_factory, "MANIFESTS", manifests):
                with self.assertRaisesRegex(book_factory.ManifestError, "duplicate book slug"):
                    book_factory.all_books()

    def test_register_refuses_to_overwrite_existing_record(self):
        with tempfile.TemporaryDirectory() as directory:
            manifests = Path(directory) / "books"
            data = Path(directory) / "data"
            manifests.mkdir()
            original = manifests / "pmicbook.json"
            shutil.copyfile(MANIFEST, original)
            before = original.read_bytes()
            with patch.object(book_factory, "MANIFESTS", manifests), patch.object(book_factory, "DATA", data):
                with self.assertRaisesRegex(book_factory.ManifestError, "already exists"):
                    book_factory.register(MANIFEST, update=False)
            self.assertEqual(original.read_bytes(), before)
            self.assertFalse(data.exists())

    def test_register_and_update_write_only_validated_record_and_derived_indexes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifests = root / "catalog" / "books"
            data = root / "site" / "data"
            update_source = root / "updated.json"
            base_record = json.loads(MANIFEST.read_text(encoding="utf-8"))
            (manifests).mkdir(parents=True)
            (manifests / "pmicbook.json").write_text(json.dumps(base_record), encoding="utf-8")
            new_record = deepcopy(self.book)
            new_record["id"] = "samplebook"
            new_record["slug"] = "samplebook"
            new_record["status"] = "in-progress"
            new_record.pop("publicationEvidence")
            new_source = root / "samplebook.json"
            new_source.write_text(json.dumps(new_record), encoding="utf-8")
            with patch.object(book_factory, "MANIFESTS", manifests), patch.object(book_factory, "DATA", data):
                book_factory.register(new_source, update=False)
                registered = json.loads((manifests / "samplebook.json").read_text(encoding="utf-8"))
                self.assertEqual(registered["id"], "samplebook")
                generated = json.loads((data / "books.json").read_text(encoding="utf-8"))
                self.assertEqual([book["id"] for book in generated], ["pmicbook", "samplebook"])

                changed = deepcopy(new_record)
                changed["description"]["en"] = "Updated description for a safe metadata update."
                update_source.write_text(json.dumps(changed), encoding="utf-8")
                book_factory.register(update_source, update=True)
                updated = json.loads((manifests / "samplebook.json").read_text(encoding="utf-8"))
                self.assertEqual(updated["id"], "samplebook")
                self.assertEqual(updated["description"]["en"], changed["description"]["en"])
                generated = json.loads((data / "books.json").read_text(encoding="utf-8"))
                generated_update = next(book for book in generated if book["id"] == "samplebook")
                self.assertEqual(generated_update["description"]["en"], changed["description"]["en"])

    def test_discovery_validator_rejects_missing_map_connections(self):
        books = [self.book]
        indexes = {
            name: json.loads((ROOT / "catalog" / f"{filename}.json").read_text(encoding="utf-8"))
            for name, filename in (("categories", "categories"), ("roadmap", "roadmap"), ("learning-paths", "learning-paths"))
        }
        broken = deepcopy(indexes)
        broken["categories"]["categories"][0]["map"][0].pop("connections")
        with self.assertRaisesRegex(book_factory.ManifestError, "connections must be a list"):
            book_factory.validate_discovery_indexes(books, broken)


if __name__ == "__main__":
    unittest.main()
