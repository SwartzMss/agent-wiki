# Scan Policy

## Objective

Choose the smallest inspection plan that can support a reliable repository guide. The scan is adaptive: the checklist lists possible evidence sources; it is not a mandatory sequence.

The model context is a scarce output channel. Repository bytes should be inspected locally in bounded operations and represented in context by compact claims, locators, and short snippets only when necessary.

## Three inspection levels

### 1. Discovery — always

Discovery is metadata-only:

- Resolve the exact repository root and current Git revision when available.
- Inventory top-level entries, file counts by extension, likely source roots, authoritative manifests, tests, tools, and CI paths.
- Identify generated, binary, vendor, cache, and build-output exclusions.
- Record inaccessible paths and inventory truncation.

Do not read implementation files during discovery. The helper stores the manifest outside the target repository.

### 2. Targeted analysis — select by profile and evidence

Select only relevant dimensions:

- Project map and module boundaries.
- Runtime entry points and lifecycle.
- Platform selection and deployment.
- Public versus internal interfaces.
- Cross-component ABI, IPC, RPC, protocol, registration, and persistent-state contracts.
- Dependencies and consumers.
- Existing conventions and concrete pitfalls.
- Tests, tools, samples, and CI.
- OSS upstream identity, license facts, and local integration.

Read authoritative files first. Use search to locate symbols and read only the smallest useful ranges.

### 3. Deep inspection — trigger-based

Deep inspection is justified only when a targeted question remains unanswered or a high-impact contract requires verification. Examples:

- Full-scope counts to validate a candidate convention.
- Cross-repository reverse-dependency checks when sibling repositories are explicitly accessible.
- Duplicate ABI/protocol/enum definitions across known consumers.
- Git history for a repeated regression, revert, compatibility fix, or co-change.
- Version/changelog consistency checks.
- Security-sensitive configuration review, reporting paths and redacted risk only.

Do not run every deep check for every repository.

## Default context budgets

These are hard output budgets for the helper, not targets to fill.

| Budget | Default |
|---|---:|
| Inventory returned to the model | 24 KB |
| One file read returned | 16 KB |
| One search result returned | 32 KB |
| Search matches per operation | 80 |
| Files searched per operation | 1,000 |
| Search bytes scanned per operation | 128 MB |
| Source snippets retained per task | 12 |
| Context lines around a match | 2 before + 2 after |
| One source line in a snippet | 1,000 characters |
| Combined context pack | 96 KB |
| Count files per batch | 1,000 |
| Count bytes per batch | 256 MB |
| Count maximum single file | 64 MB |
| Manifest entries | 50,000 |

The helper may return less than these limits. It must never silently exceed them. A configured limit is not proof that all applicable files were inspected.

## Batched extraction

For each logical task:

1. Define one question and its applicable file scope.
2. Search at most the configured number of files and bytes.
3. Retain only the most useful matches and short surrounding context.
4. Read a small range from the authoritative file or representative implementation.
5. Record the claim and source locator externally.
6. Checkpoint the completed task and next task.

If a search or count is incomplete, continue from the helper's saved cursor/job state or label the result incomplete. Do not infer a repository-wide convention from a partial batch.

## Ingest is not context loading

The word ingest refers to the local evidence-extraction process. It does not mean:

- Reading every source file into the model.
- Concatenating the repository into one prompt.
- Retaining all search output in conversation history.
- Repeating the same extraction after a context reset.
- Treating a schema or manifest as a substitute for bounded extraction.

The model should receive a compact inventory, a scan plan, a few evidence snippets, and validated claim records. The full source remains in the repository.

## External session and evidence storage

The helper stores data under the user's cache directory:

- Linux/macOS: XDG_CACHE_HOME when set, otherwise ~/.cache.
- Windows: LOCALAPPDATA when set, otherwise the user's local application data directory.
- An explicit state directory may be supplied, but it must remain outside the target repository.

Each session contains:

- source-manifest.json — metadata-only inventory.
- evidence.jsonl — one compact claim record per line.
- session.json — phase, checkpoint, budgets, task state, and reuse metadata.

No scan artifacts are written into the target repository. No database or background service is required.

## Session lifecycle

- A new inventory creates a new session.
- The helper finds the latest prior session for the same canonical repository path.
- Prior evidence is copied only if every cited source still exists and its SHA-256 fingerprint matches.
- Missing or changed source files invalidate the corresponding evidence record.
- Unverified hypotheses are never reused into a new session.
- Resume uses the saved phase and next task; it does not replay completed tasks by default.
- If the repository changes during a session, revalidate the evidence before composing the document.

File metadata such as size and modification time is useful for inventory, but is not sufficient to validate a claim. Evidence reuse requires a source-content fingerprint.

## Search and read policy

- Search is for locating evidence, not for generating a source dump.
- Search output is capped by file count, bytes, matches, snippets, line length, and total returned bytes.
- Read one file or a narrow line range at a time.
- Files larger than the read budget must be inspected through targeted ranges or narrower searches.
- Binary, generated, vendored, and excluded files are not normal source evidence.
- build.sh is never read or treated as authoritative.
- A raw text search does not establish semantic usage or a code convention.

## Count policy

A full-scope count must declare its applicable file scope, extensions, exclusions, and matching semantics.

The helper's count operation is resumable and reports cumulative files, bytes, matches, skipped large files, and completion state. A count is complete only when every applicable file was scanned and no relevant file was skipped. The helper performs raw line-based matching; it does not parse C/C++ comments, string literals, macros, or syntax. Do not describe a raw count as a semantic count.

## Stop conditions

Stop and checkpoint when the task is answered, an output budget is reached, a source is unavailable, or further inspection would not change the document. A report must state partial coverage, inaccessible submodules, truncated inventories, skipped large files, and other material limitations.

## Failure handling

If a helper operation fails:

- Preserve the session and prior evidence.
- Narrow the scope or fix the path.
- Do not switch to an unbounded recursive dump as a fallback.
- If the helper cannot be used, apply the same limits manually and clearly report that helper-backed session/resume was unavailable.
