"""Validate actual helper artifacts against the published JSON Schemas."""

import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from scripts import agent_wiki

ROOT = Path(__file__).resolve().parents[1]


class SchemaCompatibilityTests(unittest.TestCase):
    def test_schema_documents_and_real_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            (repo / "src").mkdir()
            (repo / "src" / "app.cpp").write_text(
                "int main() { return 0; }\n", encoding="utf-8"
            )
            state = Path(temporary) / "state"
            args = argparse.Namespace(
                repo=str(repo), state_dir=str(state),
                max_entries=agent_wiki.MAX_INVENTORY_ENTRIES,
            )
            with contextlib.redirect_stdout(io.StringIO()):
                session = agent_wiki.inventory_command(args)
            session_id = session["session_id"]
            ev = argparse.Namespace(
                repo=str(repo), state_dir=str(state), session=session_id,
                claim="入口在 src/app.cpp", classification="verified_fact",
                path="src/app.cpp", symbol="main", start_line=1, end_line=1,
                scope="", notes="",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                agent_wiki.evidence_add_command(ev)

            session_dir, _, _ = agent_wiki.load_session(repo, session_id, str(state))
            pairs = {
                "source-manifest": json.loads(
                    (session_dir / "source-manifest.json").read_text(encoding="utf-8")
                ),
                "session": json.loads(
                    (session_dir / "session.json").read_text(encoding="utf-8")
                ),
                "evidence": json.loads(
                    (session_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()[0]
                ),
            }
            for name, record in pairs.items():
                with self.subTest(schema=name):
                    schema = json.loads(
                        (ROOT / "schemas" / (name + ".schema.json")).read_text(
                            encoding="utf-8"
                        )
                    )
                    Draft202012Validator.check_schema(schema)
                    Draft202012Validator(
                        schema, format_checker=FormatChecker()
                    ).validate(record)


if __name__ == "__main__":
    unittest.main()
