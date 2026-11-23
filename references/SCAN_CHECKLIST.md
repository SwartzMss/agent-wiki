# Repository Scan Checklist

Use this as a menu of evidence sources after creating the scan plan. Skip irrelevant dimensions. Do not copy the checklist into the generated AGENTS.md.

## 0. Inventory and boundaries

- Top-level structure and actual source roots.
- README and project-owned architecture documentation.
- CMakeLists.txt, cmake/, Android.bp, Android.mk, Meson, Autotools, or other active manifests.
- dependency.xml and other source-controlled dependency manifests.
- deploy.xml, package manifests, service manifests, and startup integration.
- VERSION, VERSION.dat, CHANGELOG, CHANGES, and embedded version metadata.
- LICENSE, NOTICE, copyright, upstream URL, and submodule metadata.
- src/, include/, test/, tests/, tools/, samples/, config/, and CI definitions.
- Generated output, binary files, caches, vendor code, and empty template directories.
- Submodule state and inaccessible paths when Git metadata is available.

Do not inspect build.sh. Record its presence only when relevant. Do not confuse a source-controlled dependency.xml with a generated dependency/ directory.

## 1. Project map and runtime

- Identify real modules from source roots, active targets, manifests, and entry points.
- Find main functions, service registration, plugin initialization, framework callbacks, and process entry points.
- Trace only the startup or lifecycle path needed to explain runtime behavior.
- Identify important module-to-module calls, events, IPC, RPC, sockets, shared memory, or service relationships.
- Locate state ownership, caches, persistence paths, and lifecycle boundaries.
- Separate facts visible in code from architecture inferred from names.

## 2. Platform and deployment

Inspect active configuration and target wiring, not just file presence.

- CMake add_subdirectory, add_library, add_executable, install/export rules, and platform conditionals.
- Soong cc_library_*, cc_binary, cc_prebuilt_library_*, genrule, export_include_dirs, and architecture branches.
- Internal platform configuration, buildkit metadata, package manifests, deploy.xml, init scripts, and service manifests.
- Platform/product macros such as _QNX_, _ANDROID_, _LINUX_X86_, AG35, or AG55.
- Compiler/linker flags and feature switches only when they affect compatibility, ABI, or platform behavior.

For each platform, distinguish:
1. Configured — named in configuration.
2. Built — an active target is connected for that platform.
3. Deployed — a deployment or packaging manifest installs the artifact.
4. Runtime-loaded — a service, plugin, or loader actually loads it.

Do not infer support from a macro occurrence alone.

## 3. Public and internal interfaces

- Confirm public headers through install/export rules, Soong exports, visibility declarations, and actual consumers.
- Identify private headers and implementation-only interfaces.
- Inspect exported symbols, function signatures, structure layout, calling convention, ownership, and ABI-sensitive types when relevant.
- Locate IDL, .rpc, protocol schemas, generated bindings, field numbers, message IDs, and version negotiation.
- Identify shared enums, numeric IDs, error-code ranges, registration strings, provider names, plugin keys, and factory names.
- Record fixed buffer/protocol limits only when they affect an external contract.
- Distinguish source-of-truth definitions from generated copies.

A header under include/ is not automatically public.

## 4. Cross-component and cross-repository contracts

Prioritize only contracts that cross a module, process, repository, or deployment boundary.

- ABI and exported API.
- RPC, IPC, wire formats, and protocol compatibility.
- Shared enum values, indexes, error codes, and registration names.
- Shared memory keys, device nodes, socket paths, service endpoints, and persistent storage locations.
- Inbound consumers and outbound dependencies, within the explicitly accessible workspace.
- Duplicate headers, protocol structures, or constants across known repositories.

State the workspace boundary. Never claim an exhaustive reverse-dependency list outside the scanned workspace.

## 5. Existing code patterns

Use references/PATTERN_CATALOG.md. Candidate checks may include:

- NULL versus nullptr.
- Logging API families and severity mapping.
- Header guards and include conventions.
- Copyright-header coverage.
- Error handling and resource lifecycle.
- Threading, locks, callbacks, and ownership.
- Configuration defaults and feature flags.
- Generated-file banners and source-of-truth relationships.

Counts are optional. Run full-scope counts only when a candidate convention would materially improve AGENTS.md.

## 6. Dependencies and versions

- Compare declared dependencies with active target links/imports.
- Identify runtime-loaded libraries and plugins when evidence exists.
- Record platform-specific dependency differences.
- Compare upstream version, internal package version, embedded version, and changelog only when present.
- Identify duplicate declarations and version drift.
- Treat declaration/use mismatches as discrepancies, not automatic defects.

A source include or symbol reference alone does not prove a link-time or runtime dependency.

## 7. Tests, tools, samples, and CI

- Find test roots and actual test registration.
- Identify test frameworks, harnesses, mocks, fixtures, and platform restrictions.
- Distinguish executable assertions from empty scaffolding.
- Locate tools, debug utilities, samples, and configuration examples.
- Inspect CI workflows and connected lint/static-analysis/coverage checks.
- Describe what is wired and what it covers; do not include commands.

## 8. OSS-specific evidence

For an identifiable upstream component:

- Upstream repository URL and exact baseline tag/commit.
- LICENSE, NOTICE, copyright, and attribution facts.
- Upstream README capability claims, checked against local source where needed.
- Local patches, internal integration, packaging, and platform adaptations.
- Patch markers and their observed coverage, if used.
- Android prebuilt source, artifact names, and license metadata, where relevant.
- Distinguish upstream version from internal package version.

Do not infer legal conclusions or assume every local change has a patch marker.

## 9. Discrepancy candidates

Investigate only when the scan plan calls for it:

- Version values disagree.
- Changelog headings repeat or appear stale.
- Active linked dependency is absent from a manifest.
- Declared dependency is not used by active targets.
- Old header/library names remain in consumers.
- Platform identifiers disagree across configuration, targets, and deployment.
- Generated files appear to be maintained source.
- Required submodules are uninitialized.
- Duplicate ABI/protocol definitions diverge.
- Sensitive values appear in source or configuration.

These are investigation candidates, not automatic defects. Report only verified facts and redacted security risks.

## 10. Evidence gate

Before using a claim, answer:

- What exactly is being claimed?
- Which path, symbol, target, manifest, test, or decision supports it?
- Is the evidence current, historical, inferred, or contradictory?
- What is the applicable scope?
- Could the claim mislead an AI assistant if it is wrong?
- Is the claim stable and useful enough for AGENTS.md?

If any answer is unclear, omit the claim or keep it in the chat report as an unverified item.
