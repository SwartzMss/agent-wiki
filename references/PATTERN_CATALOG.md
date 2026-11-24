# Repository Architecture and Contract Catalog

This catalog is a **project-knowledge discovery menu**, not a coding-standard generator. The goal is to capture stable facts and constraints that help a coding Agent locate code and avoid breaking real repository behavior.

## Scope

Include only repository-specific knowledge that affects implementation, integration, runtime behavior, compatibility, or safe maintenance. Exclude coding style and format rules even when they appear frequently in source.

| Dimension | Evidence to inspect | Useful AGENTS.md output |
|---|---|---|
| Project map | Targets, modules, source roots, exported interfaces | What each module owns and where to start |
| Runtime lifecycle | Entry points, service registration, initialization and teardown | Actual startup flow and lifecycle constraints |
| Module boundaries | Public exports, active links, RPC/IPC, consumers | How components interact and depend on one another |
| Platform integration | QNX/Android/Linux branches, manifests, deploy rules | Configured vs built vs deployed vs loaded |
| ABI and public API | Export rules, ABI-sensitive types, public headers | Compatibility boundaries and source-of-truth locations |
| Protocol contracts | IDL, RPC schemas, numeric IDs, enums, error codes | Wire/data contracts and required consistency |
| Shared resources | IPC handles, shared memory, buffers, device nodes, persistent paths | Ownership, lifetime, and external resource boundaries |
| Concurrency and threading | Callback registration, mutex ownership, thread-affinity guards, tests | Proven thread and lifecycle invariants |
| Configuration | Active config sources, feature switches, defaults with external impact | Where runtime behavior is configured |
| Generated files | IDL/schema inputs, generators, generated outputs | Which source should be changed and which outputs are derived |
| Dependency relationships | Declared deps, linked artifacts, runtime-loaded components, consumers | Actual impact scope for changes |
| Tests and CI | Executed tests, regression coverage, integration targets | What is currently validated |
| Concrete pitfalls | Regression tests, guards, warnings, reverts corroborated by current code | Failure modes and protected assumptions |

## Evidence gates

- **Verified fact:** a current source, active manifest, exported interface, or registered test establishes the claim.
- **Verified project constraint:** a current API/ABI/protocol contract, runtime guard, active configuration, regression test, or explicit project-owned decision establishes a constraint, with its affected scope.
- **Historical fact:** history helps explain an existing compatibility boundary; a commit message alone never proves current behavior.
- **Potential discrepancy:** current sources disagree; cite both sides and mark it 需确认.
- **Unverified hypothesis:** keep out of AGENTS.md.

A single authoritative IDL or lifecycle entry point may be sufficient evidence. Do not require a prevalence percentage or multiple examples for a directly defined contract. Conversely, repeated text usage alone does not establish an invariant.

## Explicit exclusions

Do not analyze, count, or recommend:

- NULL vs nullptr preferences, indentation, whitespace, or brace formatting.
- Naming case/style, generic file layout preferences, or include/header-guard style.
- Copyright-header *coverage rates* or other coding-style census.
- Logging macro usage rates when the API choice is merely stylistic.
- Generic C/C++ coding standards, automated formatting rules, or best practices.
- A migration direction from old to new style based only on code prevalence.

License and NOTICE *facts* remain relevant for OSS provenance. A logging API, error representation, or naming string remains relevant only when it is a demonstrated public interface, protocol field, runtime registration key, or cross-component contract.

## When to use the helper count command

Counting is **not a default stage**. Use it only when an explicit project-specific question requires a complete scope, such as determining registered service endpoints or the consumers of a protocol symbol. Declare the file scope, verify completeness, then inspect representative authoritative definitions. A raw count is supporting evidence, not proof of semantics.

## Output discipline

- Explain what the repository currently does, not how every C/C++ project should be written.
- Reference exact source paths and symbols; do not copy large code blocks.
- Label a genuine discrepancy 需确认 and do not turn it into an unsupported prohibition.
- Keep project-specific maintenance constraints concise and attached to their evidence.
- Prefer a small set of high-impact contracts and lifecycle facts over exhaustive code statistics.
