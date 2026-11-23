# Repository Pattern Catalog

This catalog is an analysis menu, not a list of rules to impose. Inspect only patterns relevant to the repository and retain only patterns that are stable, project-specific, and useful to a coding assistant.

## Evidence threshold

A repeated pattern may be described as an existing convention when it appears in at least 80% of applicable occurrences and in at least three independent source files, or when an explicit project-owned policy, ADR, or maintainer decision establishes it.

The threshold applies to repeated conventions, not to every repository fact. One authoritative IDL can define a protocol field; one real entry point can establish where initialization begins; one regression test can establish a concrete pitfall.

Counts must use a declared full scope and exclude generated, vendored, binary, and build-output files. Raw text counts are not semantic counts unless comments, strings, and generated text are handled appropriately.

## Candidate dimensions

| Dimension | Candidate evidence | Useful output |
|---|---|---|
| Layout and ownership | Source roots, module owners, public/private headers | Module map and boundaries |
| Runtime and lifecycle | Entry points, initialization order, teardown, callbacks | Verified runtime flow |
| Module boundaries | Includes, exported targets, registration, call direction | Stable dependencies and coupling |
| Naming and symbols | API prefixes, type/function names, registration strings | Existing project vocabulary |
| Error handling | Error domains, return conventions, mappings | Error contract |
| Logging | Logging APIs, severity mapping, subsystem use | Which logging interface belongs to which subsystem |
| Configuration | Config sources, defaults, feature flags, platform branches | Authoritative configuration and override behavior |
| Concurrency | Locks, atomics, event loops, callback threading, ownership | Verified thread/lifecycle constraints |
| Memory and resources | Allocation/free pairing, RAII, handles, fixed buffers | Project-specific resource contracts |
| Persistence and IPC | Shared memory, sockets, file paths, protocol framing | Data and process boundaries |
| Generated files | Generator inputs, banners, generated outputs | Source of truth and files not to edit directly |
| Testing | Fixtures, harnesses, mocks, target registration | Actual validation coverage |
| Pitfalls | Guards, warnings, regression tests, reverts | Concrete failure modes and protected assumptions |
| History and co-change | Repeated fixes/reverts, files changed together | Historical risks and integration touchpoints |

## Classification

Choose one classification for each candidate:

- verified_convention — meets the threshold or is explicitly documented.
- tool_enforced — enforced by a CI/linter/build configuration; cite the enforcement point.
- migration — old and new styles coexist with an evidenced direction; state scope and exceptions.
- split — multiple styles coexist without a dominant pattern; omit as a convention.
- isolated_example — one-off occurrence; do not promote to a convention.

## Historical evidence

Use Git history selectively:

- A revert or repeated regression can reveal a concrete failure mode.
- A regression test can corroborate behavior that must remain protected.
- Co-change analysis can suggest related files to inspect when a feature changes.
- A commit message alone does not establish a current invariant.
- Historical facts belong in AGENTS.md only when they explain a current compatibility or maintenance boundary.

## Output discipline

- State the observed pattern, scope, and representative paths.
- Keep raw counts out unless they materially support a stable convention.
- Never write “the project standard is” from a small sample.
- Do not invent a migration direction or recommend a migration without evidence.
- Do not add generic C/C++ advice.
