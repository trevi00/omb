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
2. Review and export reusable code, tests, and sanitized documentation; select a compatible license before releasing code.
3. Complete Buzz integration and verify the user journey with a Linux server and supported client.
4. Prepare a reproducible demo, installation guide, security guidance, and release evidence.
5. Finalize Oh My Buzz branding and launch materials after the product works. Promotional publication is a later delivery; do not claim unmeasured performance or costs.

Creating this repository does not remove content already published elsewhere. Any previous exposure requires separate containment and remediation.
