import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import reference_intelligence as ri


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = json.loads((ROOT / "catalog/reference-intelligence/inventory.json").read_text(encoding="utf-8"))
DECISIONS = json.loads((ROOT / "catalog/reference-intelligence/editorial-decisions.json").read_text(encoding="utf-8"))
PROVENANCE = json.loads((ROOT / "catalog/reference-intelligence/provenance-audit.json").read_text(encoding="utf-8"))


class ReferenceInventoryTests(unittest.TestCase):
    def test_checked_in_source_inventory_is_complete_and_bounded(self):
        ri.validate_inventory(INVENTORY)
        self.assertEqual(INVENTORY["upstream"]["entryCount"], 49)
        self.assertEqual(INVENTORY["upstream"]["publishedRepositoryCount"], 39)
        self.assertEqual(sum(len(book["chapters"]) for book in INVENTORY["books"]), 758)
        self.assertEqual(sum(book["status"] == "planned" for book in INVENTORY["books"]), 10)
        self.assertEqual(sum(bool(book.get("repository")) for book in INVENTORY["books"]), 39)
        self.assertFalse(any("description" in book for book in INVENTORY["books"]))
        self.assertTrue(all(book["observedFactsOnly"] is True for book in INVENTORY["books"]))
        self.assertTrue(all(len(book["repository"]["headSha"]) == 40 for book in INVENTORY["books"] if book["repository"]))
        self.assertFalse(any(book["repository"]["treeTruncated"] for book in INVENTORY["books"] if book["repository"]))

    def test_editorial_assessments_and_provenance_records_validate(self):
        ri.validate_review_records(DECISIONS, INVENTORY)
        ri.validate_provenance_records(PROVENANCE)
        ids = {item["projectId"] for item in DECISIONS["decisions"]}
        self.assertEqual(ids, {"fabcontrolbook", "thinfilmbook", "reliabilityengineeringbook", "algebrabook", "calculusbook", "engineeringmathbook", "heavyvehiclebook", "carbook", "dinosaurbook", "robotbook", "pmicbook"})
        self.assertEqual(next(item["outcome"] for item in DECISIONS["decisions"] if item["projectId"] == "engineeringmathbook"), "defer-or-cancel")

    def test_provenance_requires_assessment_and_complete_original_and_third_party_records(self):
        empty = copy.deepcopy(PROVENANCE)
        next(item for item in empty["works"] if item["workId"] == "pmicbook")["reuseRecords"] = []
        with self.assertRaisesRegex(ri.ReferenceError, r"reuseRecords: \[\] is too short|at least one explicit rights/provenance assessment"):
            ri.validate_provenance_records(empty)

        original = copy.deepcopy(PROVENANCE)
        record = next(item for item in original["works"] if item["workId"] == "watbook")["reuseRecords"][0]
        record.pop("rightsStatus")
        with self.assertRaisesRegex(ri.ReferenceError, "rightsStatus"):
            ri.validate_provenance_records(original)

        external = {
            "classification": "third-party-material",
            "summary": "External licensed illustration reviewed for planned use.",
            "sourceTitle": "Illustration asset",
            "sourceAuthor": "Example Creator",
            "sourceUrl": "https://assets.example.org/illustration/42",
            "sourcePath": "asset id 42",
            "licenseName": "CC BY 4.0",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "rightsStatus": "The example license permits reuse subject to attribution.",
            "restrictions": "No additional restrictions identified in the example license.",
            "requiredNotices": ["Credit Example Creator and link to CC BY 4.0."],
            "noticeLocation": "docs/THIRD_PARTY_NOTICES.md#illustration-42",
            "destinationPath": "site/assets/illustration.svg",
        }
        external_audit = copy.deepcopy(PROVENANCE)
        next(item for item in external_audit["works"] if item["workId"] == "watbook")["reuseRecords"].append(external)
        ri.validate_provenance_records(external_audit)

        for field in ("destinationPath", "rightsStatus", "restrictions", "requiredNotices", "noticeLocation"):
            incomplete = copy.deepcopy(external_audit)
            source = next(item for item in incomplete["works"] if item["workId"] == "watbook")["reuseRecords"][-1]
            source.pop(field)
            with self.subTest(field=field), self.assertRaises(ri.ReferenceError):
                ri.validate_provenance_records(incomplete)

    def test_adaptations_require_notices_translation_and_actionable_follow_up(self):
        for field in ("requiredNotices", "translationStatus"):
            audit = copy.deepcopy(PROVENANCE)
            record = next(item for item in audit["works"] if item["workId"] == "pmicbook")["reuseRecords"][0]
            record.pop(field)
            with self.subTest(field=field), self.assertRaises(ri.ReferenceError):
                ri.validate_provenance_records(audit)

        audit = copy.deepcopy(PROVENANCE)
        heavy_vehicle = next(item for item in audit["works"] if item["workId"] == "heavyvehiclebook")
        heavy_vehicle["findings"][0]["recommendedAction"] = "   "
        with self.assertRaisesRegex(ri.ReferenceError, "recommendedAction"):
            ri.validate_provenance_records(audit)
        heavy_vehicle["findings"] = []
        with self.assertRaisesRegex(ri.ReferenceError, "follow-up-required needs a concrete"):
            ri.validate_provenance_records(audit)

    def test_github_source_urls_are_bound_to_repo_sha_and_exact_source_path(self):
        sha = "a" * 40
        base_record = {
            "summary": "A pinned source assessment.",
            "sourceTitle": "Example source",
            "sourceAuthor": "Example publisher",
            "sourceRepository": "https://github.com/geniuskey/examplebook",
            "sourceCommitSha": sha,
            "sourcePath": "chapters/example.html",
            "sourceUrl": f"https://github.com/geniuskey/examplebook/blob/{sha}/chapters/example.html",
            "destinationPath": "docs/references.md",
        }
        class_fields = {
            "reference-only": {"licenseObservation": "Linked for context; no material copied."},
            "third-party-material": {
                "licenseName": "CC BY 4.0", "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
                "rightsStatus": "The source identifies a reusable asset under CC BY 4.0.",
                "restrictions": "Attribution required.", "requiredNotices": ["Credit the creator and link the license."],
                "noticeLocation": "docs/THIRD_PARTY_NOTICES.md#example",
            },
            "cc-by-4.0-adaptation": {
                "licenseName": "CC BY 4.0", "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
                "changesMade": "Translated and adapted for the learner.", "translationStatus": "English source translated to Korean.",
                "requiredNotices": ["Credit the creator, link the license, and identify changes."],
            },
        }

        for classification, extra in class_fields.items():
            record = {**base_record, "classification": classification, **extra}
            audit = copy.deepcopy(PROVENANCE)
            next(item for item in audit["works"] if item["workId"] == "watbook")["reuseRecords"].append(record)
            ri.validate_provenance_records(audit)

            invalid_urls = (
                "https://github.com/geniuskey/examplebook/blob/main/chapters/example.html",
                "https://github.com./geniuskey/examplebook/blob/main/chapters/example.html",
                "https://raw.githubusercontent.com./geniuskey/examplebook/main/chapters/example.html",
                f"https://www.github.com/geniuskey/otherbook/blob/{sha}/chapters/example.html",
                f"https://github.com/geniuskey/examplebook/blob/{'b' * 40}/chapters/example.html",
                f"https://github.com/geniuskey/otherbook/blob/{sha}/chapters/example.html",
                f"https://github.com/geniuskey/examplebook/blob/{sha}/chapters/other.html",
            )
            for invalid_url in invalid_urls:
                broken = copy.deepcopy(audit)
                target = next(item for item in broken["works"] if item["workId"] == "watbook")["reuseRecords"][-1]
                target["sourceUrl"] = invalid_url
                with self.subTest(classification=classification, url=invalid_url), self.assertRaisesRegex(ri.ReferenceError, "must pin the declared repository"):
                    ri.validate_provenance_records(broken)

        mapped = copy.deepcopy(PROVENANCE)
        device = next(item for item in mapped["works"] if item["workId"] == "watbook")["reuseRecords"][1]
        for mapping_url in (
            "https://github.com./geniuskey/devicebook/blob/main/chapters/transport.html",
            f"https://www.github.com/geniuskey/devicebook/blob/{'b' * 40}/chapters/transport.html",
        ):
            broken = copy.deepcopy(mapped)
            target = next(item for item in broken["works"] if item["workId"] == "watbook")["reuseRecords"][1]
            target["sourceMappings"][0]["url"] = mapping_url
            with self.subTest(mapping_url=mapping_url), self.assertRaisesRegex(ri.ReferenceError, "must pin the declared repository"):
                ri.validate_provenance_records(broken)

    def test_project_gate_freshness_is_scoped_and_checks_catalog_url_and_paths(self):
        decisions = copy.deepcopy(DECISIONS)
        algebra = next(item for item in decisions["decisions"] if item["projectId"] == "algebrabook")
        algebra["reviewedAgainstCatalogSha"] = INVENTORY["upstream"]["catalogHeadSha"]
        thinfilm = next(item for item in decisions["decisions"] if item["projectId"] == "thinfilmbook")
        stale_sha = "a" * 40
        thinfilm["sourceRevisions"][0]["observedSha"] = stale_sha
        repo_name = next(item for item in INVENTORY["books"] if item["id"] == thinfilm["sourceRevisions"][0]["bookId"])["repository"]["fullName"]
        thinfilm["sourceRevisions"][0]["sourceUrl"] = f"https://github.com/{repo_name}/tree/{stale_sha}"
        ri.validate_review_records(decisions, INVENTORY)
        self.assertEqual(ri.validate_project_gate("algebrabook", decisions, INVENTORY)["projectId"], "algebrabook")
        with self.assertRaisesRegex(ri.ReferenceError, "refresh the reviewed source revision"):
            ri.validate_project_gate("thinfilmbook", decisions, INVENTORY)

        current = copy.deepcopy(DECISIONS)
        current["decisions"][0]["sourceRevisions"][0]["sourcePaths"].append("chapters/not-indexed.html")
        with self.assertRaisesRegex(ri.ReferenceError, "not in the current indexed inventory"):
            ri.validate_project_gate("fabcontrolbook", current, INVENTORY)

        current = copy.deepcopy(DECISIONS)
        current["decisions"][0]["reviewedAgainstCatalogSha"] = "b" * 40
        with self.assertRaisesRegex(ri.ReferenceError, "current central catalog SHA"):
            ri.validate_project_gate("fabcontrolbook", current, INVENTORY)

        current = copy.deepcopy(DECISIONS)
        current["decisions"][0]["sourceRevisions"][0]["sourceUrl"] = "https://github.com/geniuskey/yieldbook/tree/main"
        with self.assertRaisesRegex(ri.ReferenceError, "must pin its repository and observed SHA"):
            ri.validate_review_records(current, INVENTORY)

    def test_upstream_catalog_root_and_rows_are_validated_before_access(self):
        valid = {"books": [{"id": "example", "title": "Example", "topics": ["math"]}]}
        self.assertEqual(ri.validate_upstream_catalog(valid), valid["books"])
        malformed = [
            [],
            {},
            {"books": [None]},
            {"books": [[]]},
            {"books": [{"id": "example", "title": 3}]},
            {"books": [{"id": "example", "title": "Example", "topics": ["valid", 4]}]},
            {"books": [{"id": "example", "title": "Example"}, {"id": "example", "title": "Duplicate"}]},
            {"books": [{"id": "example", "title": "Example", "featured": [None]}]},
            {"books": [{"id": "example", "title": "Example", "featured": None}]},
            {"books": [{"id": "example", "title": "Example", "featured": [{"title": "No link"}]}]},
            {"books": [{"id": "example", "title": "Example", "featured": [{"link": "/chapters/one.html", "title": 7}]}]},
            {"books": [{"id": "published", "title": "Published", "status": "published"}]},
            {"books": [{"id": "published", "title": "Published", "status": "published", "repo": "https://github.com/other/book"}]},
            {"books": [{"id": "published", "title": "Published", "status": "published", "repo": "https://example.com/book"}]},
        ]
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(ri.ReferenceError):
                ri.validate_upstream_catalog(value)

    def test_chapter_title_reports_parser_failure_status(self):
        class RawClient:
            def raw(self, *args, **kwargs): return "<h1>ignored</h1>"

        class BrokenParser:
            def __init__(self): pass
            def feed(self, page): raise ValueError("malformed html")

        with mock.patch.object(ri, "ChapterTitleParser", BrokenParser):
            self.assertEqual(ri.chapter_title(RawClient(), "https://raw.githubusercontent.com/x", "path title"),
                             ("path title", "path-derived-fallback-parse-error"))

    def test_repository_urls_and_ids_are_strict(self):
        self.assertEqual(ri.repository_from_url("https://github.com/geniuskey/devicebook"), ("geniuskey", "devicebook"))
        for value in ("http://github.com/geniuskey/devicebook", "https://github.com/other/devicebook", "https://github.com/geniuskey/devicebook/tree/main", "https://user:pass@github.com/geniuskey/devicebook", "https://github.com/geniuskey/../devicebook"):
            self.assertIsNone(ri.repository_from_url(value), value)
        with self.assertRaises(ri.ReferenceError):
            ri.validate_inventory({"schemaVersion": 1, "upstream": {}, "books": [{"id": "../bad"}]})

    def test_unchanged_repository_head_reuses_path_and_chapter_indexes(self):
        book = next(item for item in INVENTORY["books"] if item["id"] == "processbook")
        record = {"id": book["id"], "title": book["title"], "subtitle": book["subtitle"], "status": book["status"], "field": book["subject"], "level": book["audience"], "topics": book["topics"], "chapters": book["catalogChapterCount"], "simulators": book["catalogSimulatorCount"], "repo": book["repositoryUrl"], "url": book["websiteUrl"], "featured": []}

        class UnchangedClient:
            def __init__(self): self.requests = []
            def json(self, url, **kwargs):
                self.requests.append(url)
                if url.endswith("/commits?per_page=1"):
                    return 200, [{"sha": book["repository"]["headSha"], "commit": {"committer": {"date": "2026-10-13T00:00:00Z"}, "message": "unchanged"}, "html_url": "https://github.com/geniuskey/processbook/commit/" + book["repository"]["headSha"]}]
                raise AssertionError(f"unchanged repositories must not refetch metadata/tree: {url}")
            def raw(self, *args, **kwargs): raise AssertionError("unchanged chapters/licenses must not refetch raw source")

        client = UnchangedClient()
        updated = ri.inventory_one(client, record, "2026-10-13T00:00:00Z", previous=book)
        self.assertEqual(updated["repository"]["headSha"], book["repository"]["headSha"])
        self.assertEqual(len(updated["chapters"]), len(book["chapters"]))
        self.assertEqual(len(client.requests), 1)

    def test_changes_include_chapter_license_notice_add_delete_move_and_project_join(self):
        before = copy.deepcopy(INVENTORY)
        after = copy.deepcopy(INVENTORY)
        old = next(item for item in before["books"] if item["id"] == "processbook")
        new = next(item for item in after["books"] if item["id"] == "processbook")
        new["repository"]["headSha"] = "b" * 40
        source_map = new["repository"]["relevantSourceFiles"]
        old_map = old["repository"]["relevantSourceFiles"]
        old_map["chapters/old.html"] = {"blobSha": "1" * 40, "kind": "chapter", "size": 10}
        source_map["chapters/old.html"] = {"blobSha": "1" * 40, "kind": "chapter", "size": 10}
        source_map.pop("chapters/old.html")
        source_map["chapters/new.html"] = {"blobSha": "1" * 40, "kind": "chapter", "size": 10}
        source_map["chapters/added.html"] = {"blobSha": "2" * 40, "kind": "chapter", "size": 10}
        source_map["THIRD_PARTY_NOTICES.md"] = {"blobSha": "3" * 40, "kind": "rights-notice", "size": 10}
        source_map["LICENSE.md"]["blobSha"] = "4" * 40
        new["license"]["declaredFiles"][0]["blobSha"] = "4" * 40
        after_changes = ri.compare_inventories(before, after, {"decisions": [{"projectId": "thinfilmbook", "outcome": "original-deeper-treatment", "reviewedAt": "2026-10-13", "reviewedAgainstCatalogSha": INVENTORY["upstream"]["catalogHeadSha"], "sourceRevisions": [{"bookId": "processbook", "observedSha": old["repository"]["headSha"]}]}]})
        kinds = {item["kind"] for item in after_changes}
        self.assertIn("source-chapter-moved", kinds)
        self.assertIn("source-chapter-added", kinds)
        self.assertIn("source-rights-notice-added", kinds)
        self.assertIn("source-license-changed", kinds)
        self.assertIn("license-file-changed", kinds)
        move = next(item for item in after_changes if item["kind"] == "source-chapter-moved")
        self.assertEqual(move["affectedProjects"][0]["projectId"], "thinfilmbook")
        self.assertEqual(move["affectedProjects"][0]["lastReviewedSha"], old["repository"]["headSha"])

    def test_catalog_add_remove_and_status_changes_are_detected(self):
        before = copy.deepcopy(INVENTORY)
        after = copy.deepcopy(INVENTORY)
        after["upstream"]["catalogHeadSha"] = "c" * 40
        candidate = copy.deepcopy(next(book for book in before["books"] if book["status"] == "planned"))
        candidate["id"] = "another-planned-book"
        candidate["title"] = "Another Planned Book"
        after["books"].append(candidate)
        after["upstream"]["entryCount"] += 1
        removed = next(book for book in after["books"] if book["status"] == "planned" and book["id"] != candidate["id"])
        removed_id = removed["id"]
        after["books"].remove(removed)
        after["upstream"]["entryCount"] -= 1
        existing = next(book for book in after["books"] if book["id"] == "processbook")
        existing["status"] = "writing"
        kinds = {item["kind"] for item in ri.compare_inventories(before, after)}
        self.assertIn("catalog-book-added", kinds)
        changes = ri.compare_inventories(before, after)
        self.assertTrue(any(item["kind"] == "catalog-book-removed" and item["bookId"] == removed_id for item in changes))
        self.assertTrue(any(item["kind"] == "catalog-metadata-changed" and item["bookId"] == "processbook" and item["field"] == "status" for item in changes))

    def test_editorial_backlog_changes_are_reported_and_join_to_project(self):
        before = copy.deepcopy(INVENTORY)
        after = copy.deepcopy(INVENTORY)
        after["upstream"]["catalogHeadSha"] = "c" * 40
        backlog = after["upstream"]["centralSourceFiles"]["data/editorial-backlog.json"]
        robot = next(entry for entry in backlog["entries"] if entry["id"] == "robotbook")
        robot["disposition"] = "merge"
        changes = ri.compare_inventories(before, after, DECISIONS)
        changed = next(item for item in changes if item["kind"] == "central-editorial-backlog-changed" and item["bookId"] == "robotbook")
        self.assertIn("robotbook", {item["projectId"] for item in changed["affectedProjects"]})

    def test_central_license_file_changes_are_reported(self):
        before = copy.deepcopy(INVENTORY)
        after = copy.deepcopy(INVENTORY)
        after["upstream"]["catalogHeadSha"] = "c" * 40
        license_record = after["upstream"]["centralSourceFiles"]["LICENSE.md"]
        license_record["blobSha"] = "f" * 40
        changes = ri.compare_inventories(before, after, DECISIONS)
        self.assertTrue(any(item["kind"] == "central-license-changed" and item["path"] == "LICENSE.md" for item in changes))

    def test_removed_repository_is_reported_without_losing_catalog_record(self):
        book = next(item for item in INVENTORY["books"] if item["id"] == "processbook")
        record = {"id": book["id"], "title": book["title"], "subtitle": book["subtitle"], "status": book["status"], "field": book["subject"], "level": book["audience"], "topics": book["topics"], "chapters": book["catalogChapterCount"], "simulators": book["catalogSimulatorCount"], "repo": book["repositoryUrl"], "url": book["websiteUrl"], "featured": []}

        class RemovedClient:
            def json(self, url, **kwargs): return 404, None

        removed = ri.inventory_one(RemovedClient(), record, "2026-10-13T00:00:00Z", previous=book)
        after = copy.deepcopy(INVENTORY)
        after["books"] = [removed if item["id"] == "processbook" else item for item in after["books"]]
        after["upstream"]["publishedRepositoryCount"] -= 1
        changes = ri.compare_inventories(INVENTORY, after, DECISIONS)
        self.assertTrue(any(item["kind"] == "repository-unavailable" and item["bookId"] == "processbook" for item in changes))

    def test_truncated_repository_tree_fails_instead_of_indexing_partial_content(self):
        book = next(item for item in INVENTORY["books"] if item["id"] == "processbook")
        record = {"id": book["id"], "title": book["title"], "subtitle": book["subtitle"], "status": book["status"], "field": book["subject"], "level": book["audience"], "topics": book["topics"], "chapters": book["catalogChapterCount"], "simulators": book["catalogSimulatorCount"], "repo": book["repositoryUrl"], "url": book["websiteUrl"], "featured": []}

        class TruncatedClient:
            def json(self, url, **kwargs):
                if "/commits?" in url:
                    return 200, [{"sha": "e" * 40, "commit": {"message": "new", "committer": {"date": "2026-10-13T00:00:00Z"}}, "html_url": "https://github.com/geniuskey/processbook/commit/" + "e" * 40}]
                if url.endswith("/repos/geniuskey/processbook"):
                    return 200, {"default_branch": "main", "license": None}
                if "/git/trees/" in url:
                    return 200, {"truncated": True, "tree": []}
                raise AssertionError(url)

        with self.assertRaisesRegex(ri.ReferenceError, "tree was truncated"):
            ri.inventory_one(TruncatedClient(), record, "2026-10-13T00:00:00Z", previous=book)

    def test_repeat_monitor_scan_leaves_tracker_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline_path = Path(directory) / "baseline.json"
            ri.write_json(baseline_path, INVENTORY)
            comments = [{"id": i, "user": {"login": "github-actions[bot]"}, "body": body, "updated_at": f"2026-10-13T00:00:0{i}Z"} for i, body in enumerate(ri._encode_checkpoint(INVENTORY), 1)]
            issue = {"number": 42, "state": "closed", "title": "Upstream reference intelligence — review tracker", "body": ri.ISSUE_MARKER + "\n\n<!-- MY_LIBRARY_REFERENCE_DELTA_V1:" + "a" * 64 + " -->"}
            args = SimpleNamespace(baseline=str(baseline_path), decisions=str(ROOT / "catalog/reference-intelligence/editorial-decisions.json"), output_dir=str(Path(directory) / "report"), checkpoint_input=None, token=None, persist_issue=True, owner="frbread7", repo="books", github_output=None)
            same_observation = copy.deepcopy(INVENTORY)
            same_observation["upstream"]["lastSuccessfulInspectionAt"] = "2026-10-13T12:00:00Z"
            with mock.patch.object(ri, "GitHubClient"), mock.patch.object(ri, "find_tracking_issue", return_value=issue), mock.patch.object(ri, "issue_comments", return_value=comments), mock.patch.object(ri, "current_inventory", return_value=same_observation), mock.patch.object(ri, "issue_write") as issue_write:
                self.assertEqual(ri.monitor_command(args), 0)
                issue_write.assert_not_called()

    def test_monitor_command_creates_tracker_checkpoint_then_deduplicates_repeat_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline_path = Path(directory) / "baseline.json"
            ri.write_json(baseline_path, INVENTORY)
            changed = copy.deepcopy(INVENTORY)
            changed["upstream"]["catalogHeadSha"] = "c" * 40
            changed["books"][0]["subtitle"] = (changed["books"][0].get("subtitle") or "") + " revised"
            args = SimpleNamespace(
                baseline=str(baseline_path),
                decisions=str(ROOT / "catalog/reference-intelligence/editorial-decisions.json"),
                output_dir=str(Path(directory) / "report"),
                checkpoint_input=None,
                token="test-token",
                persist_issue=True,
                owner="frbread7",
                repo="books",
                github_output=None,
            )
            client = ri.GitHubClient(token="test-token")
            issue_holder = {}
            checkpoint_comments = []
            write_calls = []

            def write(client, url, method, payload):
                write_calls.append((url, method, payload))
                if method == "POST" and url.endswith("/issues"):
                    issue_holder.update({"number": 88, "state": "open", "title": payload["title"], "body": payload["body"], "user": {"login": "github-actions[bot]"}})
                    return {"number": 88}
                if method == "POST" and url.endswith("/issues/88/comments"):
                    checkpoint_comments.append({"id": len(checkpoint_comments) + 1, "user": {"login": "github-actions[bot]"}, "body": payload["body"], "updated_at": "2026-10-13T12:00:00Z"})
                    return {"id": len(checkpoint_comments)}
                self.fail(f"unexpected tracker write: {method} {url}")

            with mock.patch.object(ri, "GitHubClient", return_value=client), \
                 mock.patch.object(ri, "current_inventory", return_value=changed), \
                 mock.patch.object(ri, "find_tracking_issue", side_effect=lambda *args: issue_holder or None), \
                 mock.patch.object(ri, "issue_comments", side_effect=lambda *args: list(checkpoint_comments)), \
                 mock.patch.object(ri, "issue_write", side_effect=write), \
                 mock.patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(ri.monitor_command(args), 0)
                first_output = output.getvalue()
                self.assertIn("created issue #88", first_output)
                self.assertGreater(len(checkpoint_comments), 0)
                first_write_count = len(write_calls)
                self.assertGreater(first_write_count, 1)

                # Identical source revisions produce no new delta and no issue/comment write.
                self.assertEqual(ri.monitor_command(args), 0)
                second_output = output.getvalue()[len(first_output):]

            self.assertIn("no new changes since the monitor checkpoint", second_output)
            self.assertIn("1 total unreviewed change(s)", second_output)
            self.assertEqual(len(write_calls), first_write_count)
            self.assertEqual(len(checkpoint_comments), first_write_count - 1)


    def test_notice_files_are_indexed_as_rights_sources(self):
        for path in ("NOTICE.md", "THIRD_PARTY_NOTICES.md", "third_party-notices.txt"):
            self.assertEqual(ri.file_kind(path), "rights-notice")
        for path in ("LICENSE", "licenses/LICENSE-MIT", "LICENSE-CC-BY-4.0"):
            self.assertEqual(ri.file_kind(path), "license")

    def test_checkpoint_round_trip_is_chunked_hashed_and_safe(self):
        chunks = ri._encode_checkpoint(INVENTORY)
        self.assertGreater(len(chunks), 1)
        comments = [{"user": {"login": "github-actions[bot]"}, "body": body, "updated_at": f"2026-10-13T00:00:0{i}Z"} for i, body in enumerate(chunks)]
        restored = ri._decode_checkpoint(comments)
        self.assertEqual(restored, INVENTORY)
        bad = copy.deepcopy(comments)
        bad[0]["body"] = bad[0]["body"].replace(":1:", ":2:", 1)
        # Untrusted/tampered comment data never yields a silently accepted state.
        self.assertIsNone(ri._decode_checkpoint(bad))
        self.assertIsNone(ri._decode_checkpoint([{"user": {"login": "untrusted"}, "body": comments[0]["body"]}]))

    def test_change_fingerprint_ignores_object_key_insertion_order(self):
        self.assertEqual(ri.change_fingerprint([{"a": 1, "b": 2}]), ri.change_fingerprint([{"b": 2, "a": 1}]))

    def test_report_escapes_untrusted_titles_and_paths(self):
        current = copy.deepcopy(INVENTORY)
        current["upstream"]["lastSuccessfulInspectionAt"] = "2026-10-13T00:00:00Z"
        malicious = copy.deepcopy(next(item for item in current["books"] if item["id"] == "processbook"))
        malicious["title"] = "**[fake](https://attacker.invalid)**\n<!-- injected -->"
        current["books"].append(malicious)
        change = {"kind": "source-chapter-changed", "bookId": "processbook", "title": malicious["title"], "path": "chapters/a`](/bad).html", "afterBlob": "a" * 40}
        report = ri.summarize_changes([change], current)
        self.assertNotIn("[fake](https://attacker.invalid)", report)
        self.assertNotIn("<!-- injected -->", report)
        self.assertIn("chapters/a`](/bad).html", report)
        self.assertNotIn("\n<!-- injected -->", report)

    def test_report_caps_large_change_bursts_for_tracker_and_artifact_remains_complete(self):
        changes = [{"kind": "source-chapter-changed", "bookId": "processbook", "title": "ProcessBook", "path": f"chapters/c{i}.html"} for i in range(1000)]
        report = ri.summarize_changes(changes, INVENTORY)
        self.assertLessEqual(len(report), ri.MAX_TRACKER_BODY_CHARS - 2000)
        self.assertIn("Showing 60 of 1000 changes", report)
        self.assertIn("reference-intelligence-report", report)


class TrackingIssueLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.client = ri.GitHubClient(token="test-token")
        self.current = copy.deepcopy(INVENTORY)
        self.changes = [{"kind": "catalog-book-added", "bookId": "newbook", "title": "New Book", "status": "planned"}]
        self.report = "# Upstream reference intelligence\n\nA new catalog entry was observed.\n"

    def test_material_change_creates_tracker_and_persists_checkpoint(self):
        with mock.patch.object(ri, "issue_write", return_value={"number": 51}) as write, \
             mock.patch.object(ri, "persist_checkpoint_comments", return_value=2) as checkpoint:
            result = ri.update_tracking_issue(self.client, "frbread7", "books", self.current, self.changes, self.report)
        self.assertIn("created issue #51", result)
        args = write.call_args.args
        self.assertEqual(args[2], "POST")
        self.assertTrue(args[1].endswith("/repos/frbread7/books/issues"))
        self.assertIn(ri.ISSUE_MARKER, args[3]["body"])
        self.assertIn(ri.change_fingerprint(self.changes), args[3]["body"])
        checkpoint.assert_called_once_with(self.client, "frbread7", "books", 51, self.current)

    def test_material_change_updates_tracker_and_reopens_when_closed(self):
        previous = [{"kind": "catalog-book-added", "bookId": "oldbook"}]
        for state in ("open", "closed"):
            issue = {"number": 52, "state": state, "body": ri.ISSUE_MARKER + "\n<!-- MY_LIBRARY_REFERENCE_DELTA_V1:" + ri.change_fingerprint(previous) + " -->"}
            with self.subTest(state=state), mock.patch.object(ri, "issue_write", return_value={"number": 52}) as write, \
                 mock.patch.object(ri, "persist_checkpoint_comments", return_value=2) as checkpoint:
                result = ri.update_tracking_issue(self.client, "frbread7", "books", self.current, self.changes, self.report, issue)
            self.assertIn("updated issue #52", result)
            args = write.call_args.args
            self.assertEqual(args[2], "PATCH")
            self.assertEqual(args[3].get("state"), "open" if state == "closed" else None)
            checkpoint.assert_called_once()

    def test_repeated_delta_updates_checkpoint_without_duplicate_issue_write(self):
        issue = {"number": 53, "state": "open", "body": ri.ISSUE_MARKER + "\n<!-- MY_LIBRARY_REFERENCE_DELTA_V1:" + ri.change_fingerprint(self.changes) + " -->"}
        with mock.patch.object(ri, "issue_write") as write, mock.patch.object(ri, "persist_checkpoint_comments", return_value=2) as checkpoint:
            result = ri.update_tracking_issue(self.client, "frbread7", "books", self.current, self.changes, self.report, issue)
        self.assertIn("report already recorded", result)
        write.assert_not_called()
        checkpoint.assert_called_once_with(self.client, "frbread7", "books", 53, self.current)

    def test_checkpoint_failure_after_create_retries_checkpoint_without_duplicate_tracker(self):
        with mock.patch.object(ri, "issue_write", return_value={"number": 54}) as create, \
             mock.patch.object(ri, "persist_checkpoint_comments", side_effect=ri.ReferenceError("checkpoint write failed")):
            with self.assertRaisesRegex(ri.ReferenceError, "checkpoint write failed"):
                ri.update_tracking_issue(self.client, "frbread7", "books", self.current, self.changes, self.report)
        self.assertEqual(create.call_count, 1)
        created_body = create.call_args.args[3]["body"]
        issue = {"number": 54, "state": "open", "body": created_body}
        with mock.patch.object(ri, "issue_write") as write, \
             mock.patch.object(ri, "persist_checkpoint_comments", return_value=2) as checkpoint:
            result = ri.update_tracking_issue(self.client, "frbread7", "books", self.current, self.changes, self.report, issue)
        self.assertIn("report already recorded", result)
        write.assert_not_called()
        checkpoint.assert_called_once_with(self.client, "frbread7", "books", 54, self.current)

    def test_checkpoint_persistence_creates_missing_chunks_and_updates_existing_chunks(self):
        chunks = ri._encode_checkpoint(self.current)
        with mock.patch.object(ri, "issue_comments", return_value=[]), mock.patch.object(ri, "issue_write", return_value={}) as create:
            self.assertEqual(ri.persist_checkpoint_comments(self.client, "frbread7", "books", 55, self.current), len(chunks))
        self.assertEqual(create.call_count, len(chunks))
        self.assertTrue(all(call.args[2] == "POST" for call in create.call_args_list))

        prior_comments = [
            {"id": index, "user": {"login": "github-actions[bot]"}, "body": f"old state\n{body}"}
            for index, body in enumerate(chunks, 1)
        ]
        with mock.patch.object(ri, "issue_comments", return_value=prior_comments), mock.patch.object(ri, "issue_write", return_value={}) as update:
            self.assertEqual(ri.persist_checkpoint_comments(self.client, "frbread7", "books", 55, self.current), len(chunks))
        self.assertEqual(update.call_count, len(chunks))
        self.assertTrue(all(call.args[2] == "PATCH" for call in update.call_args_list))


class WorkflowSafetyTests(unittest.TestCase):
    def test_issue_write_workflow_is_main_only_and_checks_out_main(self):
        workflow = (ROOT / ".github/workflows/reference-monitor.yml").read_text(encoding="utf-8")
        self.assertIn("if: github.ref == 'refs/heads/main'", workflow)
        self.assertIn("group: reference-intelligence-main", workflow)
        self.assertIn("issues: write", workflow)
        checkout = workflow.split("- uses: actions/checkout@", 1)[1].split("- uses:", 1)[0]
        self.assertRegex(checkout, r"(?m)^\s+ref: main$")
        self.assertLess(workflow.index("if: github.ref == 'refs/heads/main'"), workflow.index("- uses: actions/checkout@"))


class GitHubClientSafetyTests(unittest.TestCase):
    class Response:
        status = 200
        headers = {}
        def __init__(self, body): self.body = body
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def read(self, size): return self.body[:size]

    def test_rejects_non_github_and_non_https_urls(self):
        client = ri.GitHubClient(token="test-token")
        for url in ("http://api.github.com/repos/geniuskey/books", "https://example.com/data", "file:///etc/passwd", "https://user@api.github.com/repos/geniuskey/books", "https://api.github.com:bad/repos/geniuskey/books"):
            with self.assertRaises(ri.ReferenceError):
                client.get(url)

    def test_bounds_response_size(self):
        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self, size): return b"x" * size
        client = ri.GitHubClient(token=None)
        with mock.patch.object(ri, "urlopen", return_value=Response()):
            with self.assertRaisesRegex(ri.ReferenceError, "exceeds"):
                client.get("https://api.github.com/repos/geniuskey/books", max_bytes=12)

    def test_api_404_is_a_normal_unavailable_result(self):
        client = ri.GitHubClient(token=None)
        error = HTTPError("https://api.github.com/repos/geniuskey/missing", 404, "not found", {}, None)
        with mock.patch.object(ri, "urlopen", side_effect=error):
            self.assertEqual(client.json("https://api.github.com/repos/geniuskey/missing"), (404, None))

    def test_api_retries_transient_server_and_rate_limit_failures(self):
        client = ri.GitHubClient(token=None)
        success = self.Response(b'{"ok":true}')
        failures = [
            HTTPError("https://api.github.com/test", 503, "busy", {}, None),
            HTTPError("https://api.github.com/test", 403, "rate limited", {"X-RateLimit-Remaining": "0", "Retry-After": "1"}, None),
            success,
        ]
        with mock.patch.object(ri, "urlopen", side_effect=failures) as opener, mock.patch.object(ri.time, "sleep"):
            status, data = client.json("https://api.github.com/test")
        self.assertEqual((status, data), (200, {"ok": True}))
        self.assertEqual(opener.call_count, 3)

    def test_secondary_rate_limit_honors_retry_after_and_default_wait(self):
        client = ri.GitHubClient(token=None)
        success = self.Response(b'{"ok":true}')
        retry_after = HTTPError("https://api.github.com/test", 403, "secondary", {"Retry-After": "7"}, io.BytesIO(b'{"message":"secondary rate limit"}'))
        with mock.patch.object(ri, "urlopen", side_effect=[retry_after, success]), mock.patch.object(ri.time, "sleep") as sleep:
            self.assertEqual(client.json("https://api.github.com/test"), (200, {"ok": True}))
        sleep.assert_called_once_with(7)

        secondary = HTTPError("https://api.github.com/test", 403, "secondary", {}, io.BytesIO(b'{"message":"secondary rate limit"}'))
        with mock.patch.object(ri, "urlopen", side_effect=[secondary, success]), mock.patch.object(ri.time, "sleep") as sleep:
            self.assertEqual(client.json("https://api.github.com/test"), (200, {"ok": True}))
        sleep.assert_called_once_with(60)

    def test_primary_limit_waits_until_reset_and_refuses_unbounded_wait(self):
        client = ri.GitHubClient(token=None)
        success = self.Response(b'{"ok":true}')
        reset = HTTPError("https://api.github.com/test", 403, "primary", {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000060"}, io.BytesIO(b'{"message":"API rate limit exceeded"}'))
        with mock.patch.object(ri.time, "time", return_value=1700000000), mock.patch.object(ri, "urlopen", side_effect=[reset, success]), mock.patch.object(ri.time, "sleep") as sleep:
            self.assertEqual(client.json("https://api.github.com/test"), (200, {"ok": True}))
        sleep.assert_called_once_with(60)

        too_long = HTTPError("https://api.github.com/test", 429, "limited", {"Retry-After": "601"}, io.BytesIO(b'{"message":"limited"}'))
        with mock.patch.object(ri, "urlopen", side_effect=[too_long]), mock.patch.object(ri.time, "sleep") as sleep:
            with self.assertRaisesRegex(ri.ReferenceError, "beyond this workflow's 600s retry bound"):
                client.json("https://api.github.com/test")
        sleep.assert_not_called()

    def test_issue_write_uses_secondary_retry_after(self):
        success = self.Response(b'{"number":7}')
        limited = HTTPError("https://api.github.com/test", 403, "secondary", {"Retry-After": "9"}, io.BytesIO(b'{"message":"secondary rate limit"}'))
        with mock.patch.object(ri, "urlopen", side_effect=[limited, success]), mock.patch.object(ri.time, "sleep") as sleep:
            self.assertEqual(ri.issue_write(ri.GitHubClient(token="token"), "https://api.github.com/test", "PATCH", {"title": "ok"}), {"number": 7})
        sleep.assert_called_once_with(9)

    def test_issue_create_post_does_not_retry_ambiguous_server_or_transport_failures(self):
        client = ri.GitHubClient(token="token")
        success = self.Response(b'{"number":7}')
        cases = (
            HTTPError("https://api.github.com/test", 500, "server error", {}, io.BytesIO(b"temporary")),
            URLError("connection timed out after request may have been sent"),
        )
        for failure in cases:
            with self.subTest(failure=failure), mock.patch.object(ri, "urlopen", side_effect=[failure, success]) as opener, mock.patch.object(ri.time, "sleep") as sleep:
                with self.assertRaisesRegex(ri.ReferenceError, "POST outcome is ambiguous"):
                    ri.issue_write(client, "https://api.github.com/test", "POST", {"title": "new tracker"})
                self.assertEqual(opener.call_count, 1)
                sleep.assert_not_called()

    def test_malformed_json_is_rejected(self):
        with self.assertRaisesRegex(ri.ReferenceError, "JSON is malformed"):
            ri.parse_json_bytes(b"{not json", "upstream catalog")


if __name__ == "__main__":
    unittest.main()
