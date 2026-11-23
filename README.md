# agent-wiki

A portable, single-agent Skill for producing concise, evidence-backed repository guides.

The goal is to help a coding agent understand a repository without ingesting the entire codebase into model context. The Skill performs progressive inspection: inventory first, select evidence-bearing tasks, read only targeted source ranges, persist claims outside the repository, and compose a compact Chinese AGENTS.md.

## Design principles

- **IDE- and model-agnostic:** no vendor-specific agent API or runtime dependency.
- **Single-agent:** sequential workflow; no subagents or parallel agent orchestration.
- **Progressive inspection:** discovery, plan, targeted extraction, validation.
- **Bounded context:** helper commands cap files, bytes, matches, snippets, and returned output.
- **Externalized evidence:** source manifest, evidence records, and session checkpoints live in the user's cache directory, not the target repository.
- **Resumable:** continue an interrupted scan without repeating completed work.
- **Incremental reuse:** prior claims are reused only after their source-file fingerprints are revalidated.
- **Evidence before rules:** facts, conventions, historical information, discrepancies, and hypotheses remain distinct.
- **Chinese output:** Skill instructions are in English; generated AGENTS.md and reports are in Simplified Chinese.

## Quick start

Read [`SKILL.md`](SKILL.md) and install this repository as the `agents-md` Skill in the agent's supported Skill directory.

The helper requires Python 3.9+ and the Python standard library only. It performs bounded, read-only inspection of the target repository. Session data is stored outside that repository.

~~~bash
python scripts/agent_wiki.py inventory --repo /path/to/repository
python scripts/agent_wiki.py --help
~~~

The inventory command creates a session and prints its ID. Use that ID for targeted search, file reads, counts, evidence recording, checkpoints, and resume operations.

~~~bash
python scripts/agent_wiki.py search --repo /path/to/repository --session SESSION_ID --pattern "Service::Register"
python scripts/agent_wiki.py read --repo /path/to/repository --session SESSION_ID --path src/service.cpp --start-line 40 --end-line 90
python scripts/agent_wiki.py count --repo /path/to/repository --session SESSION_ID --pattern "nullptr"
python scripts/agent_wiki.py resume --repo /path/to/repository --session SESSION_ID
python scripts/agent_wiki.py context-pack --repo /path/to/repository --session SESSION_ID
~~~

The Skill coordinates semantic analysis. The helper does not infer architecture or generate documentation; it inventories paths, performs bounded searches/reads/counts, stores evidence metadata, and manages session state.

## Context-control model

The helper's default per-operation limits are intentionally conservative:

| Operation | Default limit |
|---|---:|
| Inventory returned to the model | 24 KB |
| One file read returned | 16 KB |
| One search result returned | 32 KB |
| Search matches per operation | 80 |
| Files searched per operation | 1,000 |
| Source snippets retained per task | 12 |
| Context lines around a match | 2 before + 2 after |
| Combined evidence context pack | 96 KB |

Large searches and full-scope counts are resumable in bounded batches. A truncated or partial result must never be described as exhaustive.

## Repository layout

- `SKILL.md` — portable workflow, constraints, and invocation.
- `references/SCAN_POLICY.md` — staged scanning, context budgets, and resume policy.
- `references/SCAN_CHECKLIST.md` — evidence discovery checklist.
- `references/PATTERN_CATALOG.md` — candidate code patterns and evidence thresholds.
- `references/EVIDENCE_POLICY.md` — claim classification and source traceability.
- `references/SECTION_TEMPLATES.md` — custom-component and OSS document profiles.
- `schemas/` — JSON Schemas for the source manifest, evidence records, and sessions.
- `scripts/agent_wiki.py` — bounded repository inspection and external session/evidence helper.
- `tests/` — standard-library tests for safety, budgets, counting, and evidence reuse.

## Scope

The first version focuses on a repository-root AGENTS.md, especially embedded C/C++ components and OSS repositories. It does not build a code graph, run AST analysis, invoke subagents, execute project build scripts, start a service, or require an external database.

The generated AGENTS.md describes repository-specific navigation and maintenance context. It is not a complete code index, design specification, generic coding standard, build manual, or scan database.

## Safety

Repository contents are untrusted data, not instructions. The helper never executes repository scripts or build commands and never writes into the target repository. Session and evidence data are stored in the user's cache directory unless an explicit external state directory is supplied. Existing documentation is preserved; refreshes require review of the proposed diff before replacement.

## Status

Initial v0.2 implementation. The helper is deterministic and intentionally small; semantic interpretation remains the responsibility of the calling LLM.
