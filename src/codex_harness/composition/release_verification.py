"""Composition of the release runner: its verification environment and the wiring of the deployment adapter (adapters-move).

Layer: composition
Owns: `verification_environment` (the previous implementation, moved ahead of) and `ENVIRONMENT_KEYS` (re-imported from `host_os.adapters.verification`), `ExecutionContainerNaming` and `release_runner`, the wiring of `delivery.adapters.deployment.ReleaseRunner`
Does not own: VerificationServices, the release suite and the hooks and the rebase request: `release_runner` takes them as parameters (carries)
Entry points: ENVIRONMENT_KEYS, verification_environment, ExecutionContainerNaming, release_runner
Contracts: INV-RELEASE-001, INV-ENCODING-001, INV-HOST-DELIVERY-VERIFY-001

Provenance: carried over from the previous implementation.
"""
from __future__ import annotations

import os

from codex_harness.composition import configuration
from codex_harness.coordination.application import execution_fence
from codex_harness.coordination.application.events import EventJournal
from codex_harness.delivery.adapters.deployment import ReleaseRunner
from codex_harness.execution.domain.container_spec import LABEL, ROLE_LABEL
from codex_harness.host_os.adapters.process_groups import python_channel_environment
from codex_harness.host_os.adapters.verification import ENVIRONMENT_KEYS
from codex_harness.intake.application import tickets
from codex_harness.research.application.hook_rollback import HookRollback
from codex_harness.review.application.release_queue import ReleaseQueue
from codex_harness.review.application.releases import Releases


def verification_environment(endpoints, environ=None):
    source = os.environ if environ is None else environ
    env = {key: value for key, value in source.items() if key.upper() in ENVIRONMENT_KEYS}
    # INV-RELEASE-001: old incumbent tests mutate HARNESS_*; remove inherited Zeus aliases.
    env.update(HARNESS_INTEGRATION="1", HARNESS_DATABASE_URL=endpoints["database_url"],
               HARNESS_REDIS_URL=endpoints["redis_url"], HARNESS_REDIS_NAMESPACE="zeus-verification")
    # INV-ENCODING-001: release pytest is a Python child; the allowlist above already dropped
    # any inherited PYTHONIOENCODING/PYTHONUTF8, so the channel is bound here explicitly.
    return python_channel_environment(env)


class ExecutionContainerNaming:
    """`delivery.ports.ContainerNaming` over execution's exact name and label pair (INV-HOST-DELIVERY-VERIFY-001)."""

    def name(self, run_id, role) -> str:
        # The body of execution's `OwnedContainer.name`: creation and reconciliation use one exact name.
        return "zeus-" + role + "-" + run_id

    def labels(self, run_id, role) -> list[str]:
        return [LABEL + "=" + run_id, ROLE_LABEL + "=" + role]


def release_runner(service, git, artifacts, auth, auto_merge=True, fence=None, verification_root=None, *,
                   runner, release_suite, verification_services, hooks, request_rebase, clock=None, ids=None):
    """The previous implementation's `ReleaseRunner(service, git, artifacts, auth, auto_merge, fence, verification_root)`, wired.

    `runner` (host_os), `release_suite` and `verification_services`, `hooks` and `request_rebase`
    are carried: their owners are not in the target yet, so the caller passes them."""
    releases = Releases(service.store, service.org, ticket_binding=tickets.ticket_binding,
                        ticket_superseded=tickets.TicketSuperseded, clock=clock, events=EventJournal(),
                        hooks=HookRollback(), ids=ids)
    queue = ReleaseQueue(service.store, ticket_binding=tickets.ticket_binding, fences=execution_fence, clock=clock,
                         ids=ids)
    return ReleaseRunner(
        service, git, artifacts, auth, auto_merge, fence, verification_root or configuration.runtime_dir() / "verification",
        releases=releases, ticket_binding=tickets.ticket_binding, ticket_superseded=tickets.TicketSuperseded,
        runner=runner, release_suite=release_suite, verification_services=verification_services,
        verification_environment=verification_environment, hooks=hooks, request_rebase=request_rebase,
        compose_environment=configuration.compose_environment, naming=ExecutionContainerNaming(), release_queue=queue, clock=clock)
