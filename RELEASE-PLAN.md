# Public release plan

## Outcome and scope

Prepare OMB as a publicly reusable agent-team harness. Keep existing operational development running independently. This initial delivery establishes the public repository and release boundary only; it does not import code, deploy services, rename running components, or publish marketing messages.

## Ownership and flow

Reviewed source revision -> explicit export file list -> public-content and license review -> standalone build and tests -> documented Linux deployment -> verified client connection -> release. Implementation and independent acceptance remain separate responsibilities.

Private operational evidence stays outside this repository. Public examples use synthetic identities and configurations. Importing an old Git history is outside scope.

## Acceptance

- Initial repository: only newly authored public preparation documents and generic ignore rules.
- Code export: provenance and required third-party notices preserved; no private source analyses or customer identifiers.
- Runtime: setup, execution, cancellation, restart/recovery, and client reconnection verified on supported platforms.
- Failure/unavailable: failures and unexecuted checks disclosed; no capability claims based only on configuration.
- Concurrent development: export a pinned revision without moving or editing an active operational checkout.
- Cleanup: retain necessary evidence privately; no deletion of existing volumes or workspaces.

## Delivery stages

1. Establish the clean repository (this delivery).
2. Review and export reusable code, tests, and sanitized documentation; original project material is MIT-licensed (see LICENSE); third-party code keeps its own license and notices, and compatibility is checked before release.
3. Complete Buzz integration and verify the user journey with a Linux server and supported client.
4. Prepare a reproducible demo, installation guide, security guidance, and release evidence.
5. Finalize Oh My Buzz branding and launch materials after the product works. Promotional publication is a later delivery; do not claim unmeasured performance or costs.

## Status of the import

The outcome above describes the initial delivery. The import (delivery stage 2) is a snapshot of an earlier source revision; its state is:

- The code, tests and documents in this tree are imported from the reviewed export. Each file has a recorded
  file-level review verdict in a private audit that is not published; `public-files.txt` lists every file.
- The context-skills capability, the research-threshold replay and the pipeline resources are included. They are adapted
  from a personal project owned by the repository owner and are licensed under the MIT License (see `NOTICE`,
  `THIRD_PARTY_NOTICES` and `REUSE.toml`).
- The tests that were measured failing in a standalone run are listed in `ci/excluded-tests.txt`: the ones that need a
  private design document, or a file that is not published, are excluded with that reason, the integration-planned ones
  are described below, and the others were fixed.
- The CI `integration` job runs the integration-planned tests of `ci/excluded-tests.txt` apart from the unit job. It starts
  PostgreSQL and Redis containers but passes no connection settings, and those tests need neither. Service-backed tests
  are NOT run in OMB CI.
- Identifiers that look internal (names, URNs, schema ids) are kept for compatibility, so existing durable state
  stays readable.
- Dependency licenses are in `THIRD_PARTY_NOTICES`; three entries were resolved from public package-index metadata,
  and one of them (py-rust-stemmers) must be confirmed against its LICENSE file at E3. `REUSE.toml` declares MIT for
  original material and would carry any third-party file's own license.
- No release is published. A passing check or CI run does not mean the code is production ready.

## Snapshot status and known limitations

- This tree is a snapshot of an EARLIER source revision, not the final rebuilt runtime. The security fixes made after
  that revision are NOT carried here.
- It is a library and its tests only: there are no service entry points and no runnable release.
- A later refresh export from the accepted rebuilt revision follows; until then do not run this tree as a service.

## Provenance

Parts of this repository (the context-skills scoring, guidance and history modules, the research threshold proposal and
replay modules with their tests, and the pipeline stage definitions) are adapted from a personal project owned by the
repository owner and are licensed under the MIT License of this repository; see `NOTICE`. Material whose ownership could
not be established is not included.

Creating this repository does not remove content already published elsewhere. Any previous exposure requires separate containment and remediation.
