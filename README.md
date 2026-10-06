# OMB

An agent-team harness with planned Buzz integration.

**Status: project preparation. No runnable release is published here yet.**

## Direction

- Linux-hosted agent execution and durable task ownership.
- A client interface for conversations, visibility, and human intervention.
- Specification-driven implementation, bounded independent review, and evidence-based improvement.
- Reusable code and synthetic examples suitable for public distribution.

The intended launch name is **Oh My Buzz**, subject to branding and upstream notice review. This project is independent and does not claim endorsement by upstream projects.

## Import status

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

## Public release boundary

This repository starts with a new history. Code imports require a file-level public-distribution review, dependency and license checks, and verification against the imported revision. Private project analyses, credentials, raw execution logs, account details, and customer-specific configuration are excluded.

Original OMB project material is released under the [MIT License](LICENSE). Any third-party code imported later keeps its own license and notices; it is not relicensed by this project.

See [RELEASE-PLAN.md](RELEASE-PLAN.md).
