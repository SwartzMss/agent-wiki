"""Closure regressions for existing evidence, cache, state, and context-budget contracts."""

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import agent_wiki

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "agent_wiki.py"


class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.state = self.root / "state"
        self.repo.mkdir()
        (self.repo / "src").mkdir()
        self.source = self.repo / "src" / "service.cpp"
        self.source.write_text("RegisterService();\n", encoding="utf-8")
        inventory = self.invoke(
            agent_wiki.inventory_command,
            argparse.Namespace(repo=str(self.repo), state_dir=str(self.state),
                               max_entries=agent_wiki.MAX_INVENTORY_ENTRIES)
        )
        self.session_id = inventory["session_id"]

    def tearDown(self):
        self.temp.cleanup()

    def common(self):
        return dict(repo=str(self.repo), state_dir=str(self.state), session=self.session_id)

    def invoke(self, function, args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            function(args)
        return json.loads(out.getvalue())

    def evidence_args(self):
        return argparse.Namespace(
            **self.common(), path="src/service.cpp",
            claim="存在服务注册入口", classification="verified_fact",
            start_line=1, end_line=1, symbol="RegisterService",
            notes="", scope=""
        )

    def count_args(self):
        return argparse.Namespace(
            **self.common(), pattern="RegisterService", glob="src/*.cpp",
            regex=False, case_sensitive=True,
            restart=False, retry_skipped=False,
            max_files=20, max_bytes=agent_wiki.MAX_COUNT_BYTES
        )

    def test_evidence_line_and_symbol_must_exist(self):
        good = self.evidence_args()
        self.assertTrue(self.invoke(agent_wiki.evidence_add_command, good)["stored"])
        good.start_line = 2
        good.end_line = 2
        with self.assertRaisesRegex(ValueError, "start-line"):
            agent_wiki.evidence_add_command(good)
        good.start_line, good.end_line = 1, 3
        with self.assertRaisesRegex(ValueError, "end-line"):
            agent_wiki.evidence_add_command(good)
        good.start_line, good.end_line = 1, 1
        good.symbol = "MissingRegistration"
        with self.assertRaisesRegex(ValueError, "symbol"):
            agent_wiki.evidence_add_command(good)
        good.symbol = "RegisterService"
        good.start_line, good.end_line = None, None
        self.assertTrue(self.invoke(agent_wiki.evidence_add_command, good)["stored"])

    def test_count_hash_detects_same_size_and_restored_mtime_edit(self):
        args = self.count_args()
        first = self.invoke(agent_wiki.count_command, args)
        self.assertEqual(first["matches"], 1)
        timestamp = self.source.stat()
        self.source.write_text("UnknownService_();\n", encoding="utf-8")
        self.assertEqual(self.source.stat().st_size, timestamp.st_size)
        os.utime(self.source, ns=(timestamp.st_atime_ns, timestamp.st_mtime_ns))
        after = self.invoke(agent_wiki.count_command, args)
        self.assertEqual(after["matches"], 0)
        self.assertTrue(after["invalidated_cache"])

    def test_unsafe_regex_rejected_and_safe_single_quantifier_accepted(self):
        for pattern in (r"(a+)+$", r"[a-z]+[a-z]+$", r"(?=foo)foo"):
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(ValueError, "Regex"):
                    agent_wiki.validate_safe_regex(pattern)
        agent_wiki.validate_safe_regex(r"Register\s+Service")

    def test_git_status_timeout_does_not_report_clean(self):
        def fake_git(_root, *args, **_kwargs):
            if args[:2] == ("rev-parse", "--show-toplevel"):
                return str(self.repo.resolve())
            if args[:2] == ("rev-parse", "HEAD"):
                return "a" * 40
            if args[0] == "branch":
                return "main"
            if args[0] == "status":
                return None
            if args[0] == "ls-files":
                return "src/service.cpp\0"
            return None
        with patch.object(agent_wiki, "git_output", fake_git):
            metadata, _ = agent_wiki.git_metadata(self.repo.resolve())
        self.assertIsNone(metadata["dirty"])

    def test_session_output_budget_gates_source_but_not_checkpoint(self):
        session_dir, session, _ = agent_wiki.load_session(
            self.repo, self.session_id, str(self.state)
        )
        session["usage"]["helper_output_bytes"] = (
            agent_wiki.MAX_SESSION_OUTPUT_BYTES - agent_wiki.MAX_READ_OUTPUT + 1
        )
        agent_wiki.save_session(session_dir, session)
        read = argparse.Namespace(**self.common(),
            path="src/service.cpp", start_line=1, end_line=1,
            max_bytes=agent_wiki.MAX_READ_OUTPUT)
        with self.assertRaisesRegex(ValueError, "Session Helper output budget"):
            agent_wiki.read_command(read)
        report = self.invoke(agent_wiki.resume_command, argparse.Namespace(**self.common()))
        self.assertEqual(report["session_id"], self.session_id)
        self.assertGreater(report["helper_output_bytes"], 0)

    def test_two_simultaneous_cli_checkpoints_do_not_overwrite_each_other(self):
        base = [
            "--repo", str(self.repo), "--state-dir", str(self.state),
            "--session", self.session_id,
        ]
        commands = [
            [sys.executable, str(SCRIPT), "checkpoint", *base, "--phase", "evidence",
             "--completed-task", "first-step"],
            [sys.executable, str(SCRIPT), "checkpoint", *base, "--phase", "evidence",
             "--completed-task", "second-step"],
        ]
        processes = [
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8")
            for cmd in commands
        ]
        for process in processes:
            out, err = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, msg=err + out)
        session_dir, session, _ = agent_wiki.load_session(
            self.repo, self.session_id, str(self.state)
        )
        self.assertEqual(
            set(session["checkpoint"]["completed_tasks"]),
            {"first-step", "second-step"}
        )


if __name__ == "__main__":
    unittest.main()
