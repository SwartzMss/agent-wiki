"""Hardening tests for repository boundaries, durable cursors, and count retries."""

import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import agent_wiki


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        base = Path(self.work.name)
        self.repo = base / "repo"
        self.state = base / "state"
        self.repo.mkdir()
        (self.repo / "src").mkdir()
        (self.repo / "src" / "service.cpp").write_text(
            "RegisterService();\n" * 105, encoding="utf-8"
        )
        (self.repo / "src" / "other.cpp").write_text(
            "RegisterService();\n", encoding="utf-8"
        )
        self.session = self.run_command(agent_wiki.inventory_command, argparse.Namespace(
            repo=str(self.repo), state_dir=str(self.state),
            max_entries=agent_wiki.MAX_INVENTORY_ENTRIES
        ))["session_id"]

    def tearDown(self):
        self.work.cleanup()

    def run_command(self, function, args):
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            function(args)
        return json.loads(sink.getvalue())

    def common(self):
        return dict(repo=str(self.repo), state_dir=str(self.state), session=self.session)

    def search_args(self):
        return argparse.Namespace(
            **self.common(), pattern="RegisterService", glob="src/*.cpp",
            regex=False, case_sensitive=True, offset=None, line_offset=None,
            restart=False, max_files=100, max_matches=80,
            max_bytes=agent_wiki.MAX_SEARCH_BYTES, before=0, after=0,
        )

    def count_args(self):
        return argparse.Namespace(
            **self.common(), pattern="RegisterService", glob="src/*.cpp",
            regex=False, case_sensitive=True, max_files=100,
            max_bytes=agent_wiki.MAX_COUNT_BYTES, restart=False,
            retry_skipped=False,
        )

    def test_search_cursor_persists_and_auto_resumes(self):
        args = self.search_args()
        first = self.run_command(agent_wiki.search_command, args)
        self.assertEqual(first["match_lines_found"], 80)
        self.assertEqual(first["next_line_offset"], 80)

        resume = self.run_command(
            agent_wiki.resume_command,
            argparse.Namespace(**self.common()),
        )
        self.assertEqual(len(resume["search_jobs"]), 1)
        job = next(iter(resume["search_jobs"].values()))
        self.assertEqual(job["next_line_offset"], 80)

        second = self.run_command(agent_wiki.search_command, args)
        self.assertEqual(second["match_lines_found"], 26)
        self.assertTrue(second["complete"])
        finished = self.run_command(agent_wiki.search_command, args)
        self.assertTrue(finished["finished"])
        self.assertEqual(finished["match_lines_found"], 0)

    def test_search_byte_budget_resumes_without_duplicate_lines(self):
        (self.repo / "src" / "service.cpp").write_text(
            "RegisterService();\n" * 4, encoding="utf-8"
        )
        args = self.search_args()
        args.max_bytes = 39  # Two lines of 19 bytes each fit.
        args.max_matches = 80
        counts = []
        for _ in range(5):
            batch = self.run_command(agent_wiki.search_command, args)
            counts.append(batch["match_lines_found"])
            if batch["finished"]:
                break
        self.assertEqual(sum(counts), 5)
        self.assertTrue(batch["complete"])

    def test_changed_file_invalidates_search_cursor(self):
        args = self.search_args()
        first = self.run_command(agent_wiki.search_command, args)
        self.assertFalse(first["finished"])
        (self.repo / "src" / "service.cpp").write_text(
            "different symbols\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "Search source changed"):
            agent_wiki.search_command(args)
        args.restart = True
        restarted = self.run_command(agent_wiki.search_command, args)
        self.assertTrue(restarted["complete"])
        self.assertEqual(restarted["match_lines_found"], 1)

    def test_long_line_search_is_incomplete_and_not_silent(self):
        (self.repo / "src" / "service.cpp").write_text(
            "RegisterService()" * 10000, encoding="utf-8"
        )
        args = self.search_args()
        batch = self.run_command(agent_wiki.search_command, args)
        self.assertFalse(batch["complete"])
        self.assertTrue(batch["finished"])
        self.assertIn("src/service.cpp", batch["skipped_files"])

    def test_count_cache_is_compact_and_can_retry_skipped(self):
        (self.repo / "src" / "service.cpp").write_text(
            "RegisterService()" * 10000, encoding="utf-8"
        )
        args = self.count_args()
        first = self.run_command(agent_wiki.count_command, args)
        self.assertFalse(first["complete"])
        self.assertEqual(first["matches"], 1)
        self.assertIn("src/service.cpp", first["skipped_large_files"])
        cached = self.run_command(agent_wiki.count_command, args)
        self.assertNotIn("source_fingerprints", cached)

        (self.repo / "src" / "service.cpp").write_text(
            "RegisterService();\n", encoding="utf-8"
        )
        args.retry_skipped = True
        retried = self.run_command(agent_wiki.count_command, args)
        self.assertTrue(retried["complete"])
        self.assertEqual(retried["matches"], 2)
        self.assertEqual(retried["skipped_count"], 0)

    def test_nested_git_repository_is_not_ingested(self):
        nested = self.repo / "nested"
        nested.mkdir()
        (nested / ".git").write_text(
            "gitdir: ../private/.git/modules/nested\n", encoding="utf-8"
        )
        (nested / "secrets.cpp").write_text('const char *token = "secret";\n', encoding="utf-8")
        (self.repo / ".gitmodules").write_text(
            '[submodule "nested"]\npath = nested\n', encoding="utf-8"
        )
        git, tracked = agent_wiki.git_metadata(self.repo)
        inventory = agent_wiki.build_inventory(
            self.repo, git, tracked, agent_wiki.MAX_INVENTORY_ENTRIES
        )
        paths = {x["path"] for x in inventory["entries"]}
        self.assertNotIn("nested/secrets.cpp", paths)
        self.assertIn(".gitmodules", paths)
        self.assertTrue(any(item["path"] == "nested" for item in inventory["excluded_paths"]))
        self.assertTrue(inventory["inventory_complete"])

    def test_scan_error_marks_inventory_incomplete(self):
        original_walk = agent_wiki.os.walk

        def interrupted_walk(*args, **kwargs):
            kwargs["onerror"](PermissionError(13, "permission denied", str(self.repo / "protected")))
            yield from original_walk(*args, **kwargs)

        with patch.object(agent_wiki.os, "walk", interrupted_walk):
            git, tracked = agent_wiki.git_metadata(self.repo)
            result = agent_wiki.build_inventory(
                self.repo, git, tracked, agent_wiki.MAX_INVENTORY_ENTRIES
            )
        self.assertFalse(result["inventory_complete"])
        self.assertTrue(result["scan_errors"])

    def test_engineering_files_are_readable_but_keys_are_not(self):
        for name in ("Kconfig", "Kbuild", "BUILD", "WORKSPACE", ".gitmodules"):
            (self.repo / name).write_text("CONFIG_SERVICE=y\n", encoding="utf-8")
        (self.repo / "private.pem").write_text("private\n", encoding="utf-8")
        git, tracked = agent_wiki.git_metadata(self.repo)
        result = agent_wiki.build_inventory(
            self.repo, git, tracked, agent_wiki.MAX_INVENTORY_ENTRIES
        )
        found = {item["path"]: item for item in result["entries"]}
        for name in ("Kconfig", "Kbuild", "BUILD", "WORKSPACE", ".gitmodules"):
            self.assertTrue(found[name]["text_candidate"], name)
        self.assertFalse(found["private.pem"]["text_candidate"])

    def test_hash_file_has_hard_limit(self):
        path = self.repo / "src" / "other.cpp"
        with self.assertRaisesRegex(ValueError, "too large"):
            agent_wiki.hash_file(path, max_bytes=4)


if __name__ == "__main__":
    unittest.main()
