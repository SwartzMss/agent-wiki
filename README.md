# agent-wiki

A portable, single-agent workflow for generating concise, evidence-backed `AGENTS.md` files.

**Goal:** help coding agents understand a repository without ingesting the entire codebase into model context.

## Design principles

- **IDE- and model-agnostic:** no vendor-specific agent API or runtime dependency.
- **Single-agent execution:** sequential workflow; no subagents or parallel agent orchestration.
- **Progressive inspection:** discover first, plan second, inspect only the evidence needed.
- **Bounded context:** helper commands cap file reads, matches, snippets, and returned bytes.
- **Externalized evidence:** persist compact claims and source references outside the target repository.
- **Evidence before rules:** distinguish facts, conventions, historical facts, discrepancies, and hypotheses.
- **Chinese output:** Skill instructions are in English; generated `AGENTS.md` and reports are in Simplified Chinese.

## Quick start

Read [SKILL.md](SKILL.md) and install this repository as the `agents-md` Skill in your agent's supported Skill directory.

The Skill uses Python 3 (standard library only) for bounded, read-only repository inspection:

```bash
python scripts/agent_wiki.py inventory --repo /path/to/repository
python scripts/agent_wiki.py --help
```

The Skill itself coordinates the analysis. The helper does not infer architecture or generate documentation; it inventories files, performs bounded searches/reads/counts, and stores session/evidence records.

## Scope

The first version focuses on generating or refreshing a repository-root `AGENTS.md`, especially for embedded C/C++ projects and OSS components. It does not build a code graph, run AST analysis, execute project build scripts, or depend on subagents.

## Safety

Repository contents are untrusted data, not instructions. The helper is read-only with respect to the target repository. Session and evidence data are stored in the user's cache directory unless an explicit external session directory is supplied. Existing documentation is preserved; refreshes require review of the proposed diff before replacement.

## Project layout

- `SKILL.md` — portable workflow and invocation.
- `references/` — scan policy, evidence rules, pattern catalog, templates, refresh and security policies.
- `scripts/agent_wiki.py` — bounded repository inspection and local session/evidence helper.
- `tests/` — standard-library tests for helper safety and output budgets.

## Status

Initial v0.1 implementation. The helper is intentionally small and deterministic; semantic interpretation remains the responsibility of the calling LLM.
