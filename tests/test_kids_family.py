import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import book_factory


class KidsFamilyTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "catalog" / "kids-family.json").read_text(encoding="utf-8"))
        self.journey = json.loads((ROOT / "catalog" / "learning-journey.json").read_text(encoding="utf-8"))
        self.books = book_factory.all_books()
        self.roadmap = json.loads((ROOT / "catalog" / "roadmap.json").read_text(encoding="utf-8"))

    def validate(self, data=None, journey=None, books=None, roadmap=None):
        book_factory.validate_kids_family(
            data or self.data,
            journey or self.journey,
            self.books if books is None else books,
            roadmap or self.roadmap,
        )

    def test_generated_family_index_matches_its_separate_canonical_source(self):
        generated = json.loads((ROOT / "site" / "data" / "kids-family.json").read_text(encoding="utf-8"))
        self.assertEqual(generated, self.data)
        self.validate()

    def test_heavy_vehicle_pilot_stays_unpublished_and_outside_all_catalogs(self):
        self.assertEqual(self.data["pilot"]["id"], "heavyvehiclebook")
        self.assertEqual(self.data["pilot"]["status"], "editorial-pilot")
        self.assertEqual(self.data["pilot"]["publicationStatus"], "unpublished")
        self.assertNotIn("heavyvehiclebook", {book["id"] for book in self.books})
        self.assertFalse(any(item["id"] == "heavyvehiclebook" for group in ("books", "mathematicsBooks", "familyProjects") for item in self.roadmap[group]))
        self.assertEqual([book["id"] for book in self.books if book["status"] == "published"], ["pmicbook", "processintegrationbook", "watbook"])
        self.assertEqual(len(self.roadmap["mathematicsBooks"]), 7)
        self.assertEqual([item["id"] for item in self.roadmap["familyProjects"]], ["curiositybook"])
        self.assertEqual(len(self.journey["concepts"]), 66)
        self.assertEqual((ROOT / "docs" / "CURIOSITYBOOK_SPEC.md").exists(), True)

    def test_three_complete_bilingual_stories_link_to_few_preschool_subject_concepts(self):
        self.assertEqual(len(self.data["stories"]), 3)
        interest_ids = {interest["id"] for interest in self.data["interests"]}
        self.assertTrue({
            "cars-and-transport", "heavy-vehicles", "trains-planes-ships", "robots-machines",
            "animals-wildlife", "dinosaurs-prehistory", "ocean", "insects-nature", "space",
            "weather-earth", "human-body-health", "stories-cultures-history",
        }.issubset(interest_ids))
        stories = {story["id"]: story for story in self.data["stories"]}
        concepts = {concept["id"]: concept for concept in self.journey["concepts"]}
        for theme in self.data["themes"]:
            story = stories[theme["storyId"]]
            self.assertEqual(story["themeId"], theme["id"])
            self.assertEqual(story["status"], "editorial-draft")
            self.assertEqual(len(story["pages"]), 6)
            self.assertTrue(all(len(page["text"]["en"].split()) >= 10 and len(page["text"]["ko"]) >= 20 for page in story["pages"]))
            self.assertEqual(len(theme["conceptIds"]), 3)
            seed_concepts = [concepts[item] for item in theme["conceptIds"]]
            self.assertTrue(all(concept["stageId"] == "preschool" for concept in seed_concepts))
            self.assertEqual(len({concept["strandId"] for concept in seed_concepts}), len(seed_concepts))
            self.assertEqual(set(story["caregiverNotes"]), {"en", "ko"})
            self.assertEqual(set(story["factualNotes"]), {"en", "ko"})
            self.assertTrue(story["referenceIds"])

    def test_concept_continuations_use_existing_unique_revisit_edges_only(self):
        journey = self.journey
        ordered_stages = sorted(journey["stages"], key=lambda stage: stage["order"])
        concepts_by_id = {concept["id"]: concept for concept in journey["concepts"]}
        for theme in self.data["themes"]:
            for seed_id in theme["conceptIds"]:
                current = concepts_by_id[seed_id]
                chain = [current["id"]]
                for stage in ordered_stages[1:]:
                    next_concepts = [concept for concept in journey["concepts"] if concept["revisits"] == current["id"]]
                    self.assertEqual(len(next_concepts), 1)
                    current = next_concepts[0]
                    self.assertEqual(current["stageId"], stage["id"])
                    chain.append(current["id"])
                self.assertEqual(len(chain), len(set(chain)))

    def test_schema_and_semantic_checks_reject_unknown_learning_concept(self):
        broken = deepcopy(self.data)
        broken["themes"][0]["conceptIds"][0] = "invented-preschool-concept"
        with self.assertRaisesRegex(book_factory.ManifestError, "unknown Learning Journey concept"):
            self.validate(data=broken)

    def test_schema_requires_complete_bilingual_story_spreads(self):
        broken = deepcopy(self.data)
        del broken["stories"][0]["pages"][0]["text"]["ko"]
        with self.assertRaisesRegex(book_factory.ManifestError, "Kids & Family schema validation"):
            self.validate(data=broken)


if __name__ == "__main__":
    unittest.main()
