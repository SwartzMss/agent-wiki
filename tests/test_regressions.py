"""Cross-platform, security, and resumability regressions for the helper."""

import argparse
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import agent_wiki


class RegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.repo, self.state = base / "repo", base / "state"
        self.repo.mkdir()
        (self.repo / "src").mkdir()
        for i in range(3):
            (self.repo / "src" / f"file{i}.cpp").write_text(
                "RegisterService();\n", encoding="utf-8"
            )
        (self.repo / "README.md").write_text("Repository guide\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def invoke(self, fn, args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            fn(args)
        return json.loads(out.getvalue())

    def inventory(self):
        return self.invoke(agent_wiki.inventory_command, argparse.Namespace(
            repo=str(self.repo), state_dir=str(self.state),
            max_entries=agent_wiki.MAX_INVENTORY_ENTRIES
        ))["session_id"]

    def common(self, session):
        return dict(repo=str(self.repo), state_dir=str(self.state), session=session)

    def search_args(self, session):
        return argparse.Namespace(**self.common(session),
            pattern="RegisterService", glob="src/*.cpp", regex=False,
            case_sensitive=True, offset=0, line_offset=0, max_files=100,
            max_matches=80, max_bytes=agent_wiki.MAX_SEARCH_BYTES,
            before=0, after=0)

    def count_args(self, session):
        return argparse.Namespace(**self.common(session),
            pattern="RegisterService", glob=r"src\*.cpp", regex=False,
            case_sensitive=True, restart=False, max_files=20,
            max_bytes=agent_wiki.MAX_COUNT_BYTES)

    def test_search_continues_within_same_file(self):
        (self.repo / "src" / "file0.cpp").write_text(
            "RegisterService();\n" * 105, encoding="utf-8"
        )
        session = self.inventory()
        args = self.search_args(session)
        first = self.invoke(agent_wiki.search_command, args)
        self.assertEqual(first["match_lines_found"], 80)
        self.assertFalse(first["complete"])
        self.assertEqual(first["cursor"], {"file_offset": 0, "line_offset": 80})
        args.offset, args.line_offset = first["next_offset"], first["next_line_offset"]
        second = self.invoke(agent_wiki.search_command, args)
        self.assertTrue(second["complete"])
        self.assertEqual(second["match_lines_found"], 27)
        self.assertEqual(first["match_lines_found"] + second["match_lines_found"], 107)

    def test_windows_separators_for_read_evidence_search_and_count(self):
        session = self.inventory()
        read = argparse.Namespace(**self.common(session),
            path=r"src\file0.cpp", start_line=1, end_line=1, max_bytes=2048)
        self.assertEqual(self.invoke(agent_wiki.read_command, read)["path"], "src/file0.cpp")

        evidence = argparse.Namespace(**self.common(session),
            path=r"src\file0.cpp", claim="实际服务注册点", notes="",
            classification="verified_fact", symbol="RegisterService",
            start_line=1, end_line=1, scope="")
        stored = self.invoke(agent_wiki.evidence_add_command, evidence)
        self.assertEqual(stored["source"], "src/file0.cpp")
        search = self.search_args(session)
        search.glob = r"src\*.cpp"
        self.assertEqual(self.invoke(agent_wiki.search_command, search)["match_lines_found"], 3)
        self.assertEqual(self.invoke(agent_wiki.count_command, self.count_args(session))["matches"], 3)

    def test_sensitive_file_exclusion_and_redacted_outputs(self):
        (self.repo / ".env").write_text("PASSWORD=never-send-me\n", encoding="utf-8")
        (self.repo / "credentials.json").write_text(
            '{"client_secret": "never-send-me"}', encoding="utf-8"
        )
        (self.repo / "src" / "config.ini").write_text(
            "password: private-value\nAuthorization: Bearer sensitive-bearer\n",
            encoding="utf-8",
        )
        session = self.inventory()
        _, _, manifest = agent_wiki.load_session(self.repo, session, str(self.state))
        entries = {item["path"]: item for item in manifest["inventory"]["entries"]}
        self.assertFalse(entries[".env"]["text_candidate"])
        self.assertFalse(entries["credentials.json"]["text_candidate"])

        read = argparse.Namespace(**self.common(session),
            path="src/config.ini", start_line=None, end_line=None, max_bytes=2048)
        text = self.invoke(agent_wiki.read_command, read)["content"]
        self.assertNotIn("private-value", text)
        self.assertNotIn("sensitive-bearer", text)
        self.assertIn("[REDACTED]", text)

        read.path = ".env"
        with self.assertRaises(ValueError):
            agent_wiki.read_command(read)

        search = self.search_args(session)
        search.pattern, search.glob = "password", "src/*.ini"
        result = self.invoke(agent_wiki.search_command, search)
        self.assertNotIn("private-value", json.dumps(result))
        self.assertNotIn("sensitive-bearer", json.dumps(result))

        evidence = argparse.Namespace(**self.common(session),
            path="src/config.ini", claim="password: private-value",
            notes="client_secret=never-send-me", classification="potential_discrepancy",
            symbol=None, start_line=1, end_line=2, scope="")
        self.invoke(agent_wiki.evidence_add_command, evidence)
        directory, _, _ = agent_wiki.load_session(self.repo, session, str(self.state))
        persisted = (directory / "evidence.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("private-value", persisted)
        self.assertNotIn("never-send-me", persisted)

    def test_completed_count_invalidates_when_content_changes(self):
        session = self.inventory()
        args = self.count_args(session)
        first = self.invoke(agent_wiki.count_command, args)
        self.assertTrue(first["complete"])
        self.assertEqual(first["matches"], 3)
        self.assertEqual(self.invoke(agent_wiki.count_command, args)["matches"], 3)
        (self.repo / "src" / "file0.cpp").write_text(
            "RegisterService(); RegisterService();\n", encoding="utf-8"
        )
        refreshed = self.invoke(agent_wiki.count_command, args)
        self.assertTrue(refreshed["complete"])
        self.assertTrue(refreshed["invalidated_cache"])
        self.assertEqual(refreshed["matches"], 4)

    def test_count_scope_change_requires_new_inventory(self):
        session = self.inventory()
        args = self.count_args(session)
        self.invoke(agent_wiki.count_command, args)
        (self.repo / "src" / "added.cpp").write_text(
            "RegisterService();\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "inventory again"):
            agent_wiki.count_command(args)

    def test_cli_sequence_inventory_read_evidence_resume_pack(self):
        script = str(ROOT / "scripts" / "agent_wiki.py")
        base = ("--repo", str(self.repo), "--state-dir", str(self.state))

        def cli(*parts):
            proc = subprocess.run(
                [sys.executable, script, *parts],
                check=True, capture_output=True, encoding="utf-8", text=True
            )
            return json.loads(proc.stdout)

        session = cli("inventory", *base)["session_id"]
        common = (*base, "--session", session)
        read = cli("read", *common, "--path", r"src\file0.cpp",
                   "--start-line", "1", "--end-line", "1")
        self.assertEqual(read["path"], "src/file0.cpp")
        cli("evidence", "add", *common, "--claim", "已确认服务注册点",
            "--classification", "verified_fact", "--path", "src/file0.cpp")
        cli("checkpoint", *common, "--phase", "evidence",
            "--completed-task", "entry-points", "--next-task", "contracts")
        self.assertEqual(
            cli("resume", *common)["checkpoint"]["next_task"], "contracts"
        )
        claims = cli("context-pack", *common)["claims"]
        self.assertEqual([c["claim"] for c in claims], ["已确认服务注册点"])


    def test_compact_oversized_inventory_summary_still_returns_session_id(self):
        summary = {
            "session_id": "test-session",
            "repository": str(self.repo),
            "git": {},
            "inventory": {
                "file_count": 50000,
                "text_candidate_count": 30000,
                "by_extension": {f".ext{i}": 200 for i in range(150)},
                "top_level": ["directory-" + ("x" * 180) + str(i) for i in range(100)],
                "candidate_files": ["src/" + ("y" * 180) + str(i) for i in range(100)],
                "excluded_counts": {"binary": 50},
                "truncated": True,
            },
            "reuse": {"reused": 0, "invalidated": 0},
            "state_directory": str(self.state),
        }
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            agent_wiki.emit_inventory_summary(summary)
        payload = captured.getvalue()
        self.assertLessEqual(len(payload.encode("utf-8")), agent_wiki.MAX_INVENTORY_OUTPUT + 1)
        result = json.loads(payload)
        self.assertEqual(result["session_id"], "test-session")
        self.assertTrue(result["inventory"]["summary_truncated"])
        self.assertTrue(result["inventory"]["truncated"])

    def test_long_source_lines_do_not_expand_read_or_count_memory(self):
        (self.repo / "src" / "huge.cpp").write_text(
            "RegisterService();" * 10000, encoding="utf-8"
        )
        session = self.inventory()
        read = argparse.Namespace(**self.common(session),
            path="src/huge.cpp", start_line=1, end_line=1,
            max_bytes=agent_wiki.MAX_READ_OUTPUT)
        bounded = self.invoke(agent_wiki.read_command, read)
        self.assertTrue(bounded["truncated"])
        self.assertLessEqual(
            len(bounded["content"].encode("utf-8")), agent_wiki.MAX_READ_OUTPUT
        )
        counted = self.invoke(agent_wiki.count_command, self.count_args(session))
        self.assertFalse(counted["complete"])
        self.assertIn("huge.cpp", "".join(counted["skipped_large_files"]))

    def test_context_pack_skips_stale_and_does_not_reveal_secrets(self):
        session = self.inventory()
        evidence = argparse.Namespace(**self.common(session),
            path="src/file0.cpp",
            claim="token=very-secret-value",
            notes="password=keep-hidden",
            classification="verified_fact",
            symbol=None, start_line=1, end_line=1, scope="")
        self.invoke(agent_wiki.evidence_add_command, evidence)
        args = argparse.Namespace(**self.common(session),
            max_bytes=agent_wiki.MAX_CONTEXT_PACK,
            include_historical=False)
        pack = self.invoke(agent_wiki.context_pack_command, args)
        serialized = json.dumps(pack)
        self.assertNotIn("very-secret-value", serialized)
        self.assertNotIn("keep-hidden", serialized)
        (self.repo / "src" / "file0.cpp").write_text(
            "different entry point\n", encoding="utf-8"
        )
        self.assertEqual(self.invoke(agent_wiki.context_pack_command, args)["claims"], [])



    def test_context_pack_reports_all_omissions_without_loading_all_claims(self):
        session = self.inventory()
        for i in range(12):
            evidence = argparse.Namespace(**self.common(session),
                path="src/file0.cpp",
                claim="确认的服务契约 " + str(i) + " " + ("字" * 100),
                notes="", classification="verified_constraint",
                symbol="RegisterService", start_line=1, end_line=1, scope="")
            self.invoke(agent_wiki.evidence_add_command, evidence)
        args = argparse.Namespace(**self.common(session),
            max_bytes=900, include_historical=False)
        pack = self.invoke(agent_wiki.context_pack_command, args)
        self.assertEqual(pack["valid_claims"], 12)
        self.assertGreater(pack["omitted_by_budget"], 1)
        self.assertEqual(
            len(pack["claims"]) + pack["omitted_by_budget"], pack["valid_claims"]
        )



if __name__ == "__main__":
    unittest.main()
