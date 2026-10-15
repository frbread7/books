import json
import re
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import book_factory


class LearningJourneyTests(unittest.TestCase):
    def setUp(self):
        self.books = book_factory.all_books()
        self.categories = json.loads((ROOT / "catalog/categories.json").read_text(encoding="utf-8"))["categories"]
        self.roadmap = json.loads((ROOT / "catalog/roadmap.json").read_text(encoding="utf-8"))
        self.learning_paths = json.loads((ROOT / "catalog/learning-paths.json").read_text(encoding="utf-8"))["paths"]
        self.journey = json.loads((ROOT / "catalog/learning-journey.json").read_text(encoding="utf-8"))

    def validate(self, journey=None, roadmap=None, categories=None):
        book_factory.validate_learning_journey(self.books, roadmap or self.roadmap, categories or self.categories, journey or self.journey)

    def test_complete_bilingual_stages_and_subject_strands_are_editorial_and_separate(self):
        self.validate()
        self.assertEqual(len(self.journey["stages"]), 6)
        self.assertEqual(len(self.journey["strands"]), 11)
        self.assertEqual(len(self.journey["concepts"]), 66)
        self.assertTrue(all(concept["revisits"] not in concept["prerequisites"] for concept in self.journey["concepts"] if concept["revisits"]))
        self.assertTrue(all(stage["guidanceOnly"] for stage in self.journey["stages"]))
        self.assertTrue(all(set(stage["label"]) == {"en", "ko"} and set(stage["description"]) == {"en", "ko"} for stage in self.journey["stages"]))
        self.assertTrue(all(set(strand["label"]) == {"en", "ko"} and set(strand["description"]) == {"en", "ko"} for strand in self.journey["strands"]))
        self.assertEqual(sum(book["status"] == "published" for book in self.books), 4)
        self.assertEqual(len(self.roadmap["mathematicsBooks"]), 7)
        self.assertEqual([project["id"] for project in self.roadmap["familyProjects"]], ["curiositybook"])
        self.assertTrue(all(book["status"] == "planned" for book in self.roadmap["mathematicsBooks"] + self.roadmap["familyProjects"]))
        self.assertNotIn("curiositybook", {book["id"] for book in self.books})
        self.assertNotIn("algebrabook", {book["id"] for book in self.books})

    def test_sources_are_versioned_and_authority_is_distinguished(self):
        self.assertEqual(self.journey["reviewDate"], "2026-10-12")
        self.assertTrue(all(source["reviewedOn"] == "2026-10-12" for source in self.journey["references"]))
        nuri = next(source for source in self.journey["references"] if source["id"] == "nuri-2019")
        self.assertIn("non-commercial", nuri["reuseLimit"]["en"])
        self.assertIn("no-derivatives", nuri["reuseLimit"]["en"])
        current = next(source for source in self.journey["references"] if source["id"] == "national-2026-amendment")
        self.assertIn("Appendix 8 not listed", current["version"])
        amendment_2024 = next(source for source in self.journey["references"] if source["id"] == "national-2024-amendment")
        self.assertIn("Appendix 8 not listed", amendment_2024["version"])
        nasem = next(source for source in self.journey["references"] if source["id"] == "nasem-preschool-curriculum")
        self.assertIn("(2024)", nasem["version"])
        self.assertEqual(nasem["kind"], "research-report")
        source_ids = {source["id"] for source in self.journey["references"]}
        cited_ids = {source_id for concept in self.journey["concepts"] for source_id in concept["sourceIds"]}
        self.assertEqual(source_ids, cited_ids, "every registered source must support at least one mapped concept")
        math = next(concept for concept in self.journey["concepts"] if concept["id"] == "math-preschool-quantity-and-pattern")
        self.assertIn("nrc-early-math", math["sourceIds"])
        self.assertIn("nasem-preschool-curriculum", math["sourceIds"])

    def test_math_titles_keep_three_algebra_disciplines_distinct(self):
        proposals = {item["id"]: item for item in self.roadmap["mathematicsBooks"]}
        algebra = proposals["algebrabook"]["differentiation"]["en"].lower()
        linear = proposals["linearalgebrabook"]["differentiation"]["en"].lower()
        self.assertIn("symbolic expressions", algebra)
        self.assertIn("vector spaces", algebra)
        self.assertIn("groups, rings, and fields", algebra)
        self.assertIn("vector spaces and linear maps", linear)
        self.assertIn("first advanced", proposals["calculusbook"]["purpose"]["en"].lower())

    def test_math_book_prerequisite_graph_is_explicit_and_acyclic(self):
        proposals = {item["id"]: item for item in self.roadmap["mathematicsBooks"]}
        self.assertEqual(proposals["calculusbook"]["prerequisiteIds"], ["algebrabook"])
        self.assertEqual(proposals["linearalgebrabook"]["prerequisiteIds"], ["algebrabook"])
        self.assertIn("calculusbook", proposals["differentialequationsbook"]["prerequisiteIds"])
        self.assertIn("linearalgebrabook", proposals["numericalmethodsbook"]["prerequisiteIds"])
        self.assertIn("numericalmethodsbook", proposals["engineeringmathbook"]["prerequisiteIds"])
        book_factory.validate_math_prerequisite_graph(self.roadmap["mathematicsBooks"])

        broken = deepcopy(self.roadmap["mathematicsBooks"])
        next(item for item in broken if item["id"] == "algebrabook")["prerequisiteIds"] = ["calculusbook"]
        with self.assertRaisesRegex(book_factory.ManifestError, "prerequisite cycle"):
            book_factory.validate_math_prerequisite_graph(broken)

        broken = deepcopy(self.roadmap["mathematicsBooks"])
        next(item for item in broken if item["id"] == "calculusbook")["prerequisiteIds"] = ["missingbook"]
        with self.assertRaisesRegex(book_factory.ManifestError, "unknown prerequisite IDs"):
            book_factory.validate_math_prerequisite_graph(broken)

    def test_curiositybook_is_a_planned_story_pilot_not_a_published_activity_product(self):
        proposal = next(item for item in self.roadmap["familyProjects"] if item["id"] == "curiositybook")
        self.assertEqual(proposal["status"], "planned")
        self.assertIn("illustrated read-aloud series", proposal["subtitle"]["en"])
        chapter_groups = " ".join(proposal["chapterGroups"]["en"])
        for title in ("Where Does Rain Come From?", "How Many Friends Came to Play?", "Meeting King Sejong"):
            self.assertIn(title, chapter_groups)
        self.assertIn("Parent Read-Aloud Mode", chapter_groups)
        self.assertIn("complete without tapping", proposal["differentiation"]["en"])
        self.assertIn("not a manuscript or published textbook", proposal["purpose"]["en"])
        self.assertNotIn("repositoryUrl", proposal)
        self.assertNotIn("curiositybook", {book["id"] for book in self.books})

        concepts = {concept["id"]: concept for concept in self.journey["concepts"]}
        for concept_id in (
            "korean-preschool-shared-stories",
            "english-preschool-optional-songs",
            "math-preschool-quantity-and-pattern",
            "science-preschool-noticing-and-wonder",
            "korean-history-preschool-family-and-community-stories",
        ):
            self.assertIn("curiositybook", concepts[concept_id]["plannedBookIds"])
        self.assertIn("King Sejong", concepts["korean-history-preschool-family-and-community-stories"]["description"]["en"])

    def test_unknown_sources_planned_titles_and_published_chapters_are_rejected(self):
        broken = deepcopy(self.journey)
        broken["concepts"][0]["sourceIds"] = ["missing-source"]
        with self.assertRaisesRegex(book_factory.ManifestError, "unknown source"):
            self.validate(journey=broken)

        broken = deepcopy(self.journey)
        broken["concepts"][0]["plannedBookIds"] = ["invented-book"]
        with self.assertRaisesRegex(book_factory.ManifestError, "unknown planned title"):
            self.validate(journey=broken)

        broken = deepcopy(self.journey)
        broken["concepts"][-1]["publishedMaterials"] = [{"bookId": "pmicbook", "chapterId": "not-a-chapter", "why": {"en": "Fixture", "ko": "테스트"}}]
        with self.assertRaisesRegex(book_factory.ManifestError, "unpublished book or unknown chapter"):
            self.validate(journey=broken)

    def test_prerequisites_are_acyclic_and_revisits_move_forward(self):
        broken = deepcopy(self.journey)
        broken["concepts"][1]["prerequisites"] = ["unknown-concept"]
        with self.assertRaisesRegex(book_factory.ManifestError, "unknown prerequisite"):
            self.validate(journey=broken)

        broken = deepcopy(self.journey)
        first, second = broken["concepts"][0], broken["concepts"][6]
        first["prerequisites"] = [second["id"]]
        second["prerequisites"] = [first["id"]]
        with self.assertRaisesRegex(book_factory.ManifestError, "prerequisite cycle"):
            self.validate(journey=broken)

        broken = deepcopy(self.journey)
        concept = next(item for item in broken["concepts"] if item["revisits"])
        concept["revisits"] = "nonexistent"
        with self.assertRaisesRegex(book_factory.ManifestError, "revisits must name an existing concept"):
            self.validate(journey=broken)

    def test_process_integration_publication_replaces_its_roadmap_proposal(self):
        integration = next(book for book in self.books if book["id"] == "processintegrationbook")
        self.assertEqual(integration["status"], "published")
        self.assertEqual(integration["version"], "1.0.0")
        self.assertEqual(integration["chapterCount"], 13)
        self.assertEqual(len(integration["chapters"]), 13)
        self.assertEqual(set(integration["languages"]), {"en", "ko"})
        self.assertEqual(set(integration["relatedBooks"]), {"pmicbook", "watbook"})
        self.assertEqual(integration["publicationEvidence"]["productionRevision"], "7c1fbd44e4993b61c6eeb3fe6e11eaec1c213577")
        self.assertTrue(integration["publicationEvidence"]["releaseUrl"].endswith("/v1.0.0"))
        for experiment in integration["experiments"]:
            self.assertEqual(experiment["verification"]["checkedUrl"], experiment["url"])
            self.assertEqual(experiment["verification"]["httpStatus"], 200)
            self.assertIs(experiment["verification"]["fragmentFound"], True)
            self.assertEqual(experiment["verification"]["sourceRevision"], integration["publicationEvidence"]["productionRevision"])
        self.assertNotIn("processintegrationbook", {book["id"] for book in self.roadmap["books"]})
        fabcontrol = next(book for book in self.books if book["id"] == "fabcontrolbook")
        self.assertEqual(fabcontrol["status"], "published")
        self.assertRegex(fabcontrol["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(fabcontrol["chapterCount"], 14)
        production_revision = fabcontrol["publicationEvidence"]["productionRevision"]
        self.assertRegex(production_revision, r"^[0-9a-f]{40}$")
        self.assertTrue(fabcontrol["publicationEvidence"]["releaseUrl"].endswith(f"/v{fabcontrol['version']}"))
        for experiment in fabcontrol["experiments"]:
            self.assertEqual(experiment["verification"]["sourceRevision"], fabcontrol["publicationEvidence"]["productionRevision"])
            self.assertEqual(experiment["verification"]["httpStatus"], 200)
            self.assertIs(experiment["verification"]["fragmentFound"], True)
        self.assertNotIn("fabcontrolbook", {book["id"] for book in self.roadmap["books"]})
        semiconductor = next(category for category in self.categories if category["id"] == "semiconductor")
        control_map = next(node for node in semiconductor["map"] if node["id"] == "manufacturing-control")
        self.assertEqual({item["chapterId"] for item in control_map["connections"]}, {
            "c01-control-architecture", "c04-spc-rational-subgroups", "c06-fdc-trace-segmentation",
            "c09-run-to-run-apc", "c12-alarm-management-disposition", "c14-verification-change-governance",
        })
        control_path = next(path for path in self.learning_paths if path["id"] == "measurement-to-manufacturing-control")
        self.assertEqual([step["bookId"] for step in control_path["steps"]], ["watbook"] + ["fabcontrolbook"] * 7)
        self.assertEqual(control_path["steps"][-1]["chapterId"], "c14-verification-change-governance")
        semiconductor_sequence = [
            (book["id"], book["priority"])
            for book in sorted(self.roadmap["books"], key=lambda item: item["priority"])
            if book["id"] in {
                "thinfilmbook",
                "reliabilityengineeringbook",
                "rficbook-or-memsbook",
            }
        ]
        self.assertEqual(
            semiconductor_sequence,
            [
                ("reliabilityengineeringbook", 2),
                ("rficbook-or-memsbook", 3),
            ],
        )


if __name__ == "__main__":
    unittest.main()
