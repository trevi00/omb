"""Composition of the fleet recovery collectors: the Docker call and the wired `state`, `run_records` and git source (adapters-move).

Layer: composition
Owns: `_docker` (the previous implementation, moved ahead of) and the collector wiring
Does not own: the rest of the isolated worker, the machine call budget
Entry points: collectors
Contracts: INV-FLEET-001

Provenance: carried over from the previous implementation.
"""
from __future__ import annotations

import subprocess
from functools import partial
from types import SimpleNamespace

from codex_harness.coordination.adapters.fleet_recovery import docker_state
from codex_harness.execution.adapters.containers import cleanup_ledger
from codex_harness.execution.adapters.containers.owned_container import docker_environment
from codex_harness.host_os.adapters import git_source
from codex_harness.host_os.adapters.process_groups import run_process


def _docker(docker, args, *, timeout, env=None):
    try:
        return run_process([docker, *args], timeout=timeout, env=env if env is not None else docker_environment())
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess([docker, *args], None, "", type(exc).__name__)


def collectors(*, budget):
    """The collaborators `coordination.adapters.fleet_recovery` requires, wired (adapters-move):
    `state` is `docker_state` over the Docker call above, `run_records` is the execution run-record reader and
    `git_source` the host Git source factory. `budget` stays a parameter: it is execution's CallBudget, which the
    composition constructs (carry); only `collect_recovery_proof` takes it."""
    return SimpleNamespace(state=partial(docker_state, call=_docker), run_records=cleanup_ledger.run_records,
                           git_source=git_source.GitSource, budget=budget)
