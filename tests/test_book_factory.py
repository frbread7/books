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

    def test_experiment_requires_a_fragment_anchor(self):
        self.book["experiments"][0]["url"] = self.book["productionUrl"]
        with self.assertRaisesRegex(book_factory.ManifestError, "include an anchor"):
            book_factory.validate_manifest(self.book)

    def test_published_experiments_require_live_fragment_evidence(self):
        self.book["experiments"][0].pop("verification")
        with self.assertRaisesRegex(book_factory.ManifestError, "verification"):
            book_factory.validate_manifest(self.book)

    def test_published_production_revision_must_match_experiment_evidence(self):
        self.book["publicationEvidence"]["productionRevision"] = "b" * 40
        with self.assertRaisesRegex(book_factory.ManifestError, "sourceRevision must match publicationEvidence.productionRevision"):
            book_factory.validate_manifest(self.book)

    def test_a_book_cannot_list_itself_as_a_prerequisite(self):
        self.book["prerequisites"] = ["pmicbook"]
        with self.assertRaisesRegex(book_factory.ManifestError, "cannot list itself in prerequisites"):
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

    def test_check_indexes_detects_catalog_drift_without_mutating_generated_data(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "data"
            with patch.object(book_factory, "DATA", data), patch.object(book_factory, "all_books", return_value=[deepcopy(self.book)]):
                book_factory.generate()
                before = (data / "books.json").read_bytes()
                changed = deepcopy(self.book)
                changed["description"]["en"] += " Changed in canonical input."
                with patch.object(book_factory, "all_books", return_value=[changed]):
                    with self.assertRaisesRegex(book_factory.ManifestError, "stale or missing generated indexes.*books.json"):
                        book_factory.check_indexes()
                self.assertEqual((data / "books.json").read_bytes(), before)

    def test_second_published_book_propagates_to_generated_catalog_aggregates(self):
        second = deepcopy(self.book)
        second.update({
            "id": "fixturebook", "slug": "fixturebook", "title": {"en": "FixtureBook", "ko": "FixtureBook"},
            "subtitle": {"en": "A second-book test fixture", "ko": "두 번째 책 테스트 픽스처"},
            "description": {"en": "A synthetic record used only to verify catalog expansion.", "ko": "카탈로그 확장 검증에만 사용하는 테스트용 가상 레코드입니다."},
            "repositoryUrl": "https://github.com/example/fixturebook", "productionUrl": "https://example.test/fixturebook/",
            "languages": ["en"], "languageUrls": {"en": "https://example.test/fixturebook/"}, "chapterCount": 1,
            "chapters": [{"id": "intro", "number": 1, "title": {"en": "Introduction", "ko": "소개"}, "urls": {"en": "https://example.test/fixturebook/chapters/intro.html"}, "topics": ["fixture"]}],
            "experiments": [], "prerequisites": [], "relatedBooks": [], "status": "published",
            "attribution": {"license": "CC BY 4.0", "repositoryUrl": "https://github.com/example/fixturebook", "notes": "Synthetic test-only record."},
            "publicationEvidence": {"releaseUrl": "https://github.com/example/fixturebook/releases/tag/v1.0.0", "releasePublishedAt": "2026-01-01", "productionRevision": "a" * 40, "contentReview": "Fixture", "siteVerification": "Fixture", "chapterVerification": "Fixture"}
        })
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "data"
            with patch.object(book_factory, "DATA", data), patch.object(book_factory, "all_books", return_value=[self.book, second]):
                book_factory.generate()
            indexed = json.loads((data / "books.json").read_text(encoding="utf-8"))
        published = [book for book in indexed if book["status"] == "published"]
        self.assertEqual({book["id"] for book in published}, {"pmicbook", "fixturebook"})
        self.assertEqual(sum(book["chapterCount"] for book in published), 26)
        self.assertEqual(sum(len(book["experiments"]) for book in published), 4)
        self.assertEqual(next(book for book in published if book["id"] == "pmicbook")["chapterCount"], 25)


if __name__ == "__main__":
    unittest.main()
