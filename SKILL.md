---
name: agents-md
description: Generate or refresh concise, evidence-backed Simplified-Chinese AGENTS.md files for embedded C/C++, OSS, and other software repositories. Uses staged inspection, bounded extraction, external evidence, and resumable sessions to prevent repository-ingest context overflow.
disable-model-invocation: true
---

# AGENTS.md Generation Skill

## 1. Purpose

Generate a concise, evidence-backed repository guide that helps a coding assistant understand the target repository before changing code.

The output is a repository orientation and maintenance-boundary guide. It is not a complete code index, design specification, generic coding standard, build manual, or scan database.

The core rule is:

> Never ingest a repository wholesale. Discover the repository, plan the smallest useful inspection, extract bounded evidence, persist it outside the repository, and write only claims that survive validation.

This Skill creates or refreshes a root AGENTS.md and a sibling CLAUDE.md shim containing exactly:

~~~text
@AGENTS.md
~~~

## 2. Language policy

- Keep this Skill and all reference files in English.
- Write generated AGENTS.md files, scan reports, review summaries, and approval requests in Simplified Chinese.
- Preserve identifiers exactly: paths, filenames, symbols, macros, API names, enum members, protocol fields, target names, product names, and command names.
- Use established English technical terms when translation would reduce precision; explain them in Chinese when needed.

## 3. Hard constraints

### 3.1 Repository boundary

- Operate on exactly one target repository root supplied by the user, or the current repository when no path is supplied.
- Do not silently expand the target to its parent, siblings, or the entire workspace.
- Parent or sibling AGENTS.md files may be read as context only.
- Other repositories may be inspected read-only only when the task explicitly requires confirming a cross-repository consumer.
- Default to one root AGENTS.md. Do not create nested AGENTS.md files unless explicitly requested.
- The helper must never write into the target repository.

### 3.2 Generated-document scope

Include only useful, stable, repository-specific information:

- Project map and module responsibilities.
- Runtime entry points, lifecycle, and important relationships.
- Platform and deployment facts, distinguishing configured, built, deployed, and runtime-loaded.
- Cross-component contracts and public/internal interface boundaries.
- Existing repository-specific code conventions and concrete pitfalls.
- Tests, tools, samples, and CI integration.
- Maintenance boundaries that are supported by repository evidence.

Do not include:

- Build, test, lint, formatting, packaging, or deployment commands.
- A build-command or Soong/AOSP command chapter.
- Git branch, commit, PR, release, or contribution workflow instructions.
- A standalone open-questions or pending-items section.
- Generic C/C++ coding standards or generic best-practice advice.
- Secrets, generated output, caches, or unrelated vendor implementation.
- build.sh as a build reference. Record its presence only if useful; never inspect it as an authoritative build source.

Build systems, target names, compiler flags, platform mappings, tests, CI checks, and deployment manifests may be described as repository facts, but never as copy-pasteable procedures.

### 3.3 Evidence before claims

Every material statement must be traceable to current source evidence or an explicit project-owned decision.

Classify observations as:

- Verified fact.
- Verified convention.
- Historical fact.
- Potential discrepancy.
- Unverified hypothesis.

Only verified facts and verified conventions normally enter AGENTS.md. Include a discrepancy only in the relevant section, with the observed evidence and the label 需确认. Never promote a hypothesis or an isolated example into a project rule.

### 3.4 Safe refresh

When AGENTS.md already exists:

1. Read it completely in bounded ranges.
2. Treat unmarked content as potentially human-authored.
3. Preserve rationale and facts that cannot be reconstructed from source.
4. Revalidate current-code claims.
5. Prepare a complete proposed replacement and diff.
6. Wait for explicit user approval before replacing the existing file.

Apply the same rule to CLAUDE.md. If it already contains exactly @AGENTS.md, leave it unchanged. If it contains other content, preserve it and request approval before replacement.

## 4. Invocation

- /agents-md <repository-path> — inspect the specified repository.
- /agents-md — inspect the current repository.

Determine Create or Refresh from the target root. Do not ask the user to select a mode.

Resolve the path and confirm that it is the intended repository root before scanning. If the path is ambiguous, inaccessible, or not a repository, ask one focused clarification rather than scanning a nearby directory.

## 5. Mandatory ingest strategy: progressive, not wholesale

“Ingest” means extracting a small set of evidence-bearing facts into an external session. It does not mean loading all repository files into model context.

Use the helper at scripts/agent_wiki.py for deterministic inventory, bounded search/read/count, evidence persistence, and checkpoints. It uses Python's standard library only. Do not use AST, a code graph, subagents, IDE-specific APIs, an external database, or a service.

### Phase A — Preflight and metadata-only inventory

Run inventory once:

~~~bash
python scripts/agent_wiki.py inventory --repo <repository-path>
~~~

The command creates a session and stores a source manifest outside the target repository. It returns only a compact inventory summary, candidate authoritative files, exclusions, and a session ID.

At this stage:

- Do not read source files recursively.
- Do not print a full file listing into context.
- Do not run recursive grep that returns unbounded source lines.
- Do not inspect build.sh.
- Do not treat directory names as proof of module responsibilities.

If the inventory is truncated, state that fact. Do not claim the inventory is exhaustive.

### Phase B — Classify and create a scan plan

Classify the repository using evidence, not folder names alone:

| Profile | Evidence | Inspection emphasis |
|---|---|---|
| Custom embedded component | Project-owned APP/CBB/FWK/HAL-style code, internal manifests, platform integration, or internal build framework | Runtime, platform/deployment, ABI/IPC, dependencies, existing conventions |
| OSS component | Identifiable upstream project, license/notice, upstream baseline, and local integration or patches | Upstream identity, local changes, exported API, packaging, consumers, license facts |
| Other or mixed | Neither profile fits, or repository has multiple roles | Keep only dimensions relevant to the actual repository |

Before reading implementation files, write a short plan containing:

- Selected profile and evidence for classification.
- Relevant dimensions and why they matter.
- Authoritative files to inspect first.
- Search questions and expected evidence.
- Explicit exclusions.
- Per-task output budget.

Use the checklist as a menu, not a mandatory sequence. Skip irrelevant dimensions.

### Phase C — Targeted extraction

Follow this source-reading order unless evidence suggests otherwise:

1. Authoritative manifests and interface definitions.
2. Runtime entry points and registration points.
3. Public headers and cross-module contracts.
4. Representative implementation files selected by a specific question.
5. Tests and tools that confirm behavior or constraints.
6. History only when it explains a current compatibility boundary.

Use bounded helper operations:

~~~bash
python scripts/agent_wiki.py search --repo <repo> --session <id> --pattern "<symbol-or-contract>"
python scripts/agent_wiki.py read --repo <repo> --session <id> --path <relative-path> --start-line <n> --end-line <n>
python scripts/agent_wiki.py count --repo <repo> --session <id> --pattern "<whole-token-or-pattern>"
~~~

Default limits are defined in references/SCAN_POLICY.md. Do not raise them merely to avoid planning. Narrow the path, symbol, module, or line range first.

Search is for locating evidence, not for generating a source dump. Read only the smallest range that answers the current question. A search result or count is incomplete unless the helper explicitly reports completion.

For large repositories, split inspection into logical units such as runtime entry points, platform integration, public interfaces, IPC contracts, or test wiring. Finish one unit, persist its evidence, checkpoint, and then move to the next.

### Phase D — Externalize evidence

For each material claim, store a compact evidence record outside the target repository:

~~~bash
python scripts/agent_wiki.py evidence add --repo <repo> --session <id> --claim "<claim>" --classification verified_fact --path <relative-path> --symbol <symbol>
~~~

Evidence records store claims, source paths, line/symbol locators, and source fingerprints. They do not store full source files or large snippets.

Use references/EVIDENCE_POLICY.md to classify claims. A source path without a specific claim is not useful evidence. A claim without a verifiable source is not eligible for AGENTS.md.

### Phase E — Checkpoint and resume

After each logical unit, save the phase, completed task, and next task:

~~~bash
python scripts/agent_wiki.py checkpoint --repo <repo> --session <id> --phase evidence --completed-task "runtime-map" --next-task "public-interface-boundaries"
~~~

If context is compacted, the session is interrupted, or the scan must continue later:

~~~bash
python scripts/agent_wiki.py resume --repo <repo> --session <id>
python scripts/agent_wiki.py context-pack --repo <repo> --session <id>
~~~

Resume from the recorded next task. Do not repeat completed work unless its source fingerprint is stale or the current task requires a different question.

When starting a new session, the helper may reuse prior evidence only after re-hashing every cited source file. Changed or missing sources invalidate the corresponding claim. Never reuse an old claim merely because the repository path is the same.

### Phase F — Compose

Use references/SECTION_TEMPLATES.md. Compose from the validated evidence set, not from raw search output.

The document must be concise, navigable, repository-specific, and written in Simplified Chinese. Prefer a small project map and a few high-value constraints over exhaustive module lists or call graphs.

Do not include a claim just because it was collected. Keep volatile values as links to authoritative files rather than copying them.

### Phase G — Validate and deliver

Before writing:

- Verify each cited path, symbol, target, and manifest entry.
- Confirm counts cover the declared applicable scope.
- Distinguish configured, built, deployed, and runtime-loaded.
- Check for contradictory evidence.
- Check that secrets and excluded implementation were not copied.
- Check all generated-document exclusions in Section 3.2.
- Verify that CLAUDE.md is exactly one line: @AGENTS.md.

For a new repository with no conflicting output files, create AGENTS.md and CLAUDE.md. For refreshes or conflicting CLAUDE.md content, show the complete proposed diff and wait for explicit approval.

After approval, write only the permitted output files. Verify the final contents and report what was inspected, what was excluded, and what remains incomplete.

## 6. Context budgets and stop conditions

Use references/SCAN_POLICY.md as the authoritative budget table.

Stop and checkpoint when:

- A helper operation reaches its file, byte, match, or output limit.
- The next extraction would exceed the task's remaining context budget.
- A large repository requires another logical scan unit.
- The evidence is sufficient to answer the question.
- A source is unavailable, generated, vendored, binary, or outside the target boundary.

Do not work around a limit by dumping a directory, increasing all limits, or pasting full files into context. Narrow the query or continue in a new bounded task.

## 7. Reporting

Deliver the report in Simplified Chinese. Include:

- Repository path, profile, Create/Refresh mode, and commit when available.
- Files created, updated, unchanged, or not written.
- Key evidence paths for project map, runtime, platform/deployment, contracts, conventions, and tests/tools.
- Whether inventory, searches, and counts completed or were truncated.
- Reused and invalidated evidence, if any.
- Excluded or inaccessible paths and dimensions not assessed.
- Whether a human approval step remains.

Never invent line counts, coverage percentages, commit IDs, test results, or completeness claims.
