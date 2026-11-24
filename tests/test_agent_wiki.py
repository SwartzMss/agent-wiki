import argparse
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import agent_wiki


class AgentWikiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.repo.mkdir()
        self.state = base / "state"
        (self.repo / "src").mkdir()
        (self.repo / "vendor" / "ignored").mkdir(parents=True)
        (self.repo / "README.md").write_text("# Demo\n", encoding="utf-8")
        (self.repo / "src" / "one.cpp").write_text(
            "int main() { return RegisterService(); }\n", encoding="utf-8"
        )
        (self.repo / "src" / "two.cpp").write_text(
            "void f() { RegisterService(); }\n", encoding="utf-8"
        )
        (self.repo / "src" / "three.cpp").write_text(
            "void g() { RegisterService(); }\n", encoding="utf-8"
        )
        (self.repo / "build.sh").write_text("echo do-not-read\n", encoding="utf-8")
        (self.repo / "vendor" / "ignored" / "vendor.cpp").write_text(
            "int vendored = 1;\n", encoding="utf-8"
        )

    def tearDown(self):
        self.temp.cleanup()

    def run_json(self, function, args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            function(args)
        return json.loads(output.getvalue())

    def inventory(self):
        args = argparse.Namespace(
            repo=str(self.repo),
            state_dir=str(self.state),
            max_entries=agent_wiki.MAX_INVENTORY_ENTRIES,
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            agent_wiki.inventory_command(args)
        return json.loads(output.getvalue())

    def session_args(self, session_id):
        return {
            "repo": str(self.repo),
            "state_dir": str(self.state),
            "session": session_id,
        }

    def test_inventory_excludes_build_script_and_vendor_tree(self):
        result = self.inventory()
        self.assertNotIn("build.sh", result["inventory"]["candidate_files"])
        session_id = result["session_id"]
        _, _, manifest = agent_wiki.load_session(self.repo, session_id, str(self.state))
        entries = {item["path"]: item for item in manifest["inventory"]["entries"]}
        self.assertIn("build.sh", entries)
        self.assertFalse(entries["build.sh"]["text_candidate"])
        self.assertEqual(entries["build.sh"]["excluded_reason"], "build.sh ignored by policy")
        self.assertFalse(any(path.startswith("vendor/") for path in entries))
        self.assertIn("build.sh ignored by policy", result["inventory"]["excluded_counts"])

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            agent_wiki.safe_file(self.repo, "../outside.txt")

    def test_read_output_is_bounded(self):
        result = self.inventory()
        args = argparse.Namespace(**self.session_args(result["session_id"]))
        args.path = "README.md"
        args.start_line = None
        args.end_line = None
        args.max_bytes = 1024
        (self.repo / "README.md").write_text("x" * 50000, encoding="utf-8")
        output = self.run_json(agent_wiki.read_command, args)
        self.assertLessEqual(len(output["content"].encode("utf-8")), 1024)
        self.assertTrue(output["truncated"])

    def test_count_resumes_in_bounded_batches(self):
        result = self.inventory()
        args = argparse.Namespace(**self.session_args(result["session_id"]))
        args.pattern = "RegisterService"
        args.glob = "src/*.cpp"
        args.regex = False
        args.case_sensitive = True
        args.restart = False
        args.max_files = 1
        args.max_bytes = agent_wiki.MAX_COUNT_BYTES

        first = self.run_json(agent_wiki.count_command, args)
        self.assertFalse(first["complete"])
        second = self.run_json(agent_wiki.count_command, args)
        self.assertFalse(second["complete"])
        third = self.run_json(agent_wiki.count_command, args)
        self.assertTrue(third["complete"])
        self.assertEqual(third["matches"], 3)
        self.assertEqual(third["files_scanned"], 3)

    def test_evidence_reuse_requires_unchanged_source(self):
        first = self.inventory()
        args = argparse.Namespace(**self.session_args(first["session_id"]))
        args.claim = "The source contains the main entry point."
        args.classification = "verified_fact"
        args.path = "src/one.cpp"
        args.symbol = "main"
        args.start_line = 1
        args.end_line = 1
        args.scope = ""
        args.notes = ""
        self.run_json(agent_wiki.evidence_add_command, args)

        second = self.inventory()
        self.assertEqual(second["reuse"]["reused"], 1)
        (self.repo / "src" / "one.cpp").write_text("int changed = 1;\n", encoding="utf-8")
        third = self.inventory()
        self.assertEqual(third["reuse"]["reused"], 0)
        self.assertEqual(third["reuse"]["invalidated"], 1)

    def test_context_pack_drops_stale_evidence(self):
        result = self.inventory()
        args = argparse.Namespace(**self.session_args(result["session_id"]))
        args.claim = "A source-backed fact."
        args.classification = "verified_fact"
        args.path = "src/one.cpp"
        args.symbol = None
        args.start_line = None
        args.end_line = None
        args.scope = ""
        args.notes = ""
        self.run_json(agent_wiki.evidence_add_command, args)
        (self.repo / "src" / "one.cpp").write_text("changed\n", encoding="utf-8")

        pack_args = argparse.Namespace(**self.session_args(result["session_id"]))
        pack_args.max_bytes = agent_wiki.MAX_CONTEXT_PACK
        pack_args.include_historical = False
        pack = self.run_json(agent_wiki.context_pack_command, pack_args)
        self.assertEqual(pack["claims"], [])
        self.assertEqual(pack["invalidated_claims"], 1)


if __name__ == "__main__":
    unittest.main()
