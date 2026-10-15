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
WAT_MANIFEST = ROOT / "catalog" / "books" / "watbook.json"
PI_MANIFEST = ROOT / "catalog" / "books" / "processintegrationbook.json"
FAB_MANIFEST = ROOT / "catalog" / "books" / "fabcontrolbook.json"


class BookFactoryTests(unittest.TestCase):
    def setUp(self):
        self.book = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.wat_book = json.loads(WAT_MANIFEST.read_text(encoding="utf-8"))
        self.pi_book = json.loads(PI_MANIFEST.read_text(encoding="utf-8"))
        self.fab_book = json.loads(FAB_MANIFEST.read_text(encoding="utf-8"))

    def test_published_pmic_manifest_has_verified_release_and_complete_index(self):
        result = book_factory.validate_manifest(self.book)
        self.assertEqual(result["id"], "pmicbook")
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["chapterCount"], 25)
        self.assertEqual(len(result["experiments"]), 4)

    def test_reference_review_gate_requires_differentiation_before_project_start(self):
        decision = book_factory.validate_reference_project("fabcontrolbook")
        self.assertEqual(decision["outcome"], "original-deeper-treatment")
        with self.assertRaisesRegex(book_factory.ManifestError, "does not authorize a separate book project"):
            book_factory.validate_reference_project("engineeringmathbook")
        with self.assertRaisesRegex(book_factory.ManifestError, "add a reviewed editorial differentiation record"):
            book_factory.validate_reference_project("unreviewedbook")

    def test_planned_to_active_update_requires_differentiation_review(self):
        with tempfile.TemporaryDirectory() as directory:
            manifests = Path(directory) / "catalog" / "books"
            manifests.mkdir(parents=True)
            current = deepcopy(self.book)
            current.update({"id": "samplebook", "slug": "samplebook", "status": "planned"})
            current.pop("publicationEvidence")
            target = manifests / "samplebook.json"
            target.write_text(json.dumps(current), encoding="utf-8")
            incoming_path = Path(directory) / "incoming.json"
            incoming = deepcopy(current)
            incoming["status"] = "in-progress"
            incoming_path.write_text(json.dumps(incoming), encoding="utf-8")
            with patch.object(book_factory, "MANIFESTS", manifests), patch.object(book_factory, "validate_reference_project", side_effect=book_factory.ManifestError("review required")) as gate:
                with self.assertRaisesRegex(book_factory.ManifestError, "review required"):
                    book_factory.register(incoming_path, update=True)
                gate.assert_called_once_with("samplebook")

    def test_published_provenance_gate_requires_review_and_cleared_rights(self):
        book_factory.validate_published_provenance(self.book)
        provenance = json.loads(book_factory.PROVENANCE_AUDIT.read_text(encoding="utf-8"))
        pmic = next(work for work in provenance["works"] if work["workId"] == "pmicbook")
        pmic["reuseRecords"][0]["classification"] = "license-uncertain"
        pmic["reuseRecords"][0]["followUpRequired"] = "Verify the exact source file rights before release."
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "provenance.json"
            path.write_text(json.dumps(provenance), encoding="utf-8")
            with patch.object(book_factory, "PROVENANCE_AUDIT", path):
                with self.assertRaisesRegex(book_factory.ManifestError, "unresolved license uncertainty"):
                    book_factory.validate_published_provenance(self.book)

    def test_published_provenance_gate_rejects_empty_assessment_list(self):
        provenance = json.loads(book_factory.PROVENANCE_AUDIT.read_text(encoding="utf-8"))
        pmic = next(work for work in provenance["works"] if work["workId"] == "pmicbook")
        pmic["reuseRecords"] = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "provenance.json"
            path.write_text(json.dumps(provenance), encoding="utf-8")
            with patch.object(book_factory, "PROVENANCE_AUDIT", path):
                with self.assertRaisesRegex(book_factory.ManifestError, "reuseRecords.*too short"):
                    book_factory.validate_published_provenance(self.book)

    def test_published_provenance_gate_rejects_incomplete_adaptation_and_follow_up_action(self):
        for change, expected in (("notice", "requiredNotices"), ("action", "recommendedAction")):
            provenance = json.loads(book_factory.PROVENANCE_AUDIT.read_text(encoding="utf-8"))
            pmic = next(work for work in provenance["works"] if work["workId"] == "pmicbook")
            if change == "notice":
                pmic["reuseRecords"][0].pop("requiredNotices")
            else:
                next(finding for finding in pmic["findings"] if finding["severity"] == "P2")["recommendedAction"] = "   "
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "provenance.json"
                path.write_text(json.dumps(provenance), encoding="utf-8")
                with patch.object(book_factory, "PROVENANCE_AUDIT", path):
                    with self.assertRaisesRegex(book_factory.ManifestError, expected):
                        book_factory.validate_published_provenance(self.book)

    def test_duplicate_chapter_is_rejected(self):
        self.book["chapters"].append(self.book["chapters"][0])
        self.book["chapterCount"] += 1
        with self.assertRaisesRegex(book_factory.ManifestError, "duplicate chapter id"):
            book_factory.validate_manifest(self.book)

    def test_published_without_evidence_is_rejected(self):
        self.book.pop("publicationEvidence")
        with self.assertRaisesRegex(book_factory.ManifestError, "schema validation.*publicationEvidence"):
            book_factory.validate_manifest(self.book)

    def test_published_with_empty_content_review_is_rejected(self):
        for review in ("", "   "):
            with self.subTest(review=repr(review)):
                published = deepcopy(self.book)
                published["publicationEvidence"]["contentReview"] = review
                with self.assertRaisesRegex(book_factory.ManifestError, "schema validation.*contentReview"):
                    book_factory.validate_manifest(published)

    def test_in_progress_with_empty_content_review_evidence_is_allowed(self):
        for review in ("", "   "):
            with self.subTest(review=repr(review)):
                draft = deepcopy(self.book)
                draft["status"] = "in-progress"
                draft["publicationEvidence"]["contentReview"] = review
                self.assertEqual(book_factory.validate_manifest(draft)["status"], "in-progress")

    def test_empty_in_progress_book_is_allowed_but_empty_published_book_is_rejected(self):
        draft = deepcopy(self.book)
        draft.update({"status": "in-progress", "chapterCount": 0, "chapters": [], "experiments": []})
        draft.pop("publicationEvidence")
        self.assertEqual(book_factory.validate_manifest(draft)["status"], "in-progress")

        published = deepcopy(draft)
        published["status"] = "published"
        published["publicationEvidence"] = self.book["publicationEvidence"]
        with self.assertRaisesRegex(book_factory.ManifestError, "schema validation at (chapterCount|chapters)"):
            book_factory.validate_manifest(published)

    def test_only_in_progress_manifests_may_omit_public_destination_urls(self):
        draft = deepcopy(self.book)
        draft.update({"status": "in-progress"})
        draft.pop("publicationEvidence")
        draft.pop("repositoryUrl")
        draft.pop("productionUrl")
        draft.pop("languageUrls")
        for experiment in draft["experiments"]:
            experiment.pop("verification", None)
        self.assertEqual(book_factory.validate_manifest(draft)["status"], "in-progress")

        for status in ("planned", "archived", "published"):
            for field in ("repositoryUrl", "productionUrl"):
                with self.subTest(status=status, missing=field):
                    missing_urls = deepcopy(self.book)
                    missing_urls["status"] = status
                    if status != "published":
                        missing_urls.pop("publicationEvidence")
                    missing_urls.pop(field)
                    with self.assertRaisesRegex(book_factory.ManifestError, field):
                        book_factory.validate_manifest(missing_urls)

        draft_with_language_urls = deepcopy(draft)
        draft_with_language_urls["languageUrls"] = {"en": "https://example.test/draft/"}
        with self.assertRaisesRegex(book_factory.ManifestError, "productionUrl"):
            book_factory.validate_manifest(draft_with_language_urls)

    def test_published_book_rejects_unselected_license_but_draft_may_keep_placeholder(self):
        draft = deepcopy(self.book)
        draft.update({"status": "in-progress"})
        draft.pop("publicationEvidence")
        draft["attribution"]["license"] = "CHOOSE-AND-RECORD"
        self.assertEqual(book_factory.validate_manifest(draft)["status"], "in-progress")

        for license_name in ("CHOOSE-AND-RECORD", "TBD", "no license", "unlicensed", "All rights reserved"):
            with self.subTest(license_name=license_name):
                published = deepcopy(self.book)
                published["attribution"]["license"] = license_name
                with self.assertRaisesRegex(book_factory.ManifestError, "published books require a selected license"):
                    book_factory.validate_manifest(published)

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

    def test_production_path_boundary_rejects_decoded_traversal_and_sibling_prefixes(self):
        for path in (
            "/pmicbook/../admin",
            "/pmicbook/%2e%2e/admin",
            "/pmicbook/%252e%252e/admin",
            "/pmicbook/%5c..%5cadmin",
            "/pmicbook2/chapters/intro.html",
        ):
            with self.subTest(path=path):
                self.assertFalse(book_factory.path_is_within_production(path, "/pmicbook/"))
        self.assertTrue(book_factory.path_is_within_production("/pmicbook/chapters/intro.html", "/pmicbook/"))

    def test_manifest_chapter_experiment_and_checked_url_paths_cannot_escape(self):
        self.book["chapters"][0]["urls"]["en"] = "https://frbread7.github.io/pmicbook2/admin"
        with self.assertRaisesRegex(book_factory.ManifestError, "chapter .* production path"):
            book_factory.validate_manifest(self.book)

        self.book = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.book["experiments"][0]["url"] = "https://frbread7.github.io/pmicbook2/experiment.html#run"
        with self.assertRaisesRegex(book_factory.ManifestError, "experiment .* production path"):
            book_factory.validate_manifest(self.book)

        self.book = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.book["experiments"][0]["verification"]["checkedUrl"] = "https://frbread7.github.io/pmicbook2/experiment.html#run"
        with self.assertRaisesRegex(book_factory.ManifestError, "verification.checkedUrl must remain under the production host and path"):
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
            shutil.copyfile(WAT_MANIFEST, manifests / "watbook.json")
            shutil.copyfile(PI_MANIFEST, manifests / "processintegrationbook.json")
            shutil.copyfile(FAB_MANIFEST, manifests / "fabcontrolbook.json")
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
            (manifests / "watbook.json").write_text(json.dumps(self.wat_book), encoding="utf-8")
            (manifests / "processintegrationbook.json").write_text(json.dumps(self.pi_book), encoding="utf-8")
            (manifests / "fabcontrolbook.json").write_text(json.dumps(self.fab_book), encoding="utf-8")
            new_record = deepcopy(self.book)
            new_record["id"] = "samplebook"
            new_record["slug"] = "samplebook"
            new_record["status"] = "in-progress"
            new_record.pop("publicationEvidence")
            new_source = root / "samplebook.json"
            new_source.write_text(json.dumps(new_record), encoding="utf-8")
            with patch.object(book_factory, "MANIFESTS", manifests), patch.object(book_factory, "DATA", data), patch.object(book_factory, "validate_reference_project"):
                book_factory.register(new_source, update=False)
                registered = json.loads((manifests / "samplebook.json").read_text(encoding="utf-8"))
                self.assertEqual(registered["id"], "samplebook")
                generated = json.loads((data / "books.json").read_text(encoding="utf-8"))
                self.assertEqual([book["id"] for book in generated], ["fabcontrolbook", "pmicbook", "processintegrationbook", "samplebook", "watbook"])

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
            for name, filename in (("categories", "categories"), ("roadmap", "roadmap"), ("learning-paths", "learning-paths"), ("learning-journey", "learning-journey"), ("kids-family", "kids-family"))
        }
        broken = deepcopy(indexes)
        broken["categories"]["categories"][0]["map"][0].pop("connections")
        with self.assertRaisesRegex(book_factory.ManifestError, "connections must be a list"):
            book_factory.validate_discovery_indexes(books, broken)

    def test_discovery_validator_accepts_and_requires_bilingual_map_topics(self):
        books = [self.book, self.wat_book, self.pi_book, self.fab_book]
        indexes = {
            name: json.loads((ROOT / "catalog" / f"{filename}.json").read_text(encoding="utf-8"))
            for name, filename in (("categories", "categories"), ("roadmap", "roadmap"), ("learning-paths", "learning-paths"), ("learning-journey", "learning-journey"), ("kids-family", "kids-family"))
        }
        book_factory.validate_discovery_indexes(books, indexes)

        broken = deepcopy(indexes)
        control = next(node for node in broken["categories"]["categories"][0]["map"] if node["id"] == "manufacturing-control")
        control["topics"][0] = {"en": "SPC"}
        with self.assertRaisesRegex(book_factory.ManifestError, "topic must provide both en and ko values"):
            book_factory.validate_discovery_indexes(books, broken)

    def test_check_indexes_detects_catalog_drift_without_mutating_generated_data(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "data"
            with patch.object(book_factory, "DATA", data), patch.object(book_factory, "all_books", return_value=[deepcopy(self.book), deepcopy(self.pi_book), deepcopy(self.wat_book), deepcopy(self.fab_book)]):
                book_factory.generate()
                before = (data / "books.json").read_bytes()
                changed = deepcopy(self.book)
                changed["description"]["en"] += " Changed in canonical input."
                with patch.object(book_factory, "all_books", return_value=[changed, deepcopy(self.pi_book), deepcopy(self.wat_book), deepcopy(self.fab_book)]):
                    with self.assertRaisesRegex(book_factory.ManifestError, "stale or missing generated indexes.*books.json"):
                        book_factory.check_indexes()
                self.assertEqual((data / "books.json").read_bytes(), before)

    def test_additional_published_book_propagates_to_generated_catalog_aggregates(self):
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
            expected_books = [self.book, self.pi_book, self.wat_book, self.fab_book, second]
            with patch.object(book_factory, "DATA", data), patch.object(book_factory, "all_books", return_value=expected_books):
                book_factory.generate()
                indexed = json.loads((data / "books.json").read_text(encoding="utf-8"))
        published = [book for book in indexed if book["status"] == "published"]
        self.assertEqual({book["id"] for book in published}, {"pmicbook", "watbook", "processintegrationbook", "fabcontrolbook", "fixturebook"})
        self.assertEqual(sum(book["chapterCount"] for book in published), sum(book["chapterCount"] for book in expected_books))
        self.assertEqual(sum(len(book["experiments"]) for book in published), sum(len(book["experiments"]) for book in expected_books))
        self.assertEqual(next(book for book in published if book["id"] == "pmicbook")["chapterCount"], 25)


if __name__ == "__main__":
    unittest.main()
