"""Observation ports: the buckets observation owns (single writer).

Layer: ports
Context: observation
Owns: OWNED_BUCKETS of the observation context; SpoolFull and ObservationSpool (the previous implementation `ports.py`, moved ahead
    unchanged: the append-only record store the Observer writes through); DeskHttp, the desk routes the viewer
    serves only when a desk is injected (passes `entry.http.desk` itself);
    CollectorPorts, the seams `collectors.collect` is given (builds it once)
Does not own: ObservationDirectory (9 methods, above the port-size limit) and the other observation Protocols
    (PostgresFacts, RedisFacts, ...)
Entry points: OWNED_BUCKETS, SpoolFull, ObservationSpool, DeskHttp, CollectorPorts
Contracts: INV-OBSERVATION-001
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

# `metric_observations`: (coordinator), declared before its one writer, the previous implementation application/measurements.py
# (no other writer). `observation_metrics` (a different bucket): (coordinator), the
# metrics projection's aggregates, an addition with no counterpart, declared before its one writer
# `application.metrics_projector`.
OWNED_BUCKETS = ("observation_audit", "observations", "observation_quarantine", "observation_alerts",
                 "observation_collections", "observation_terminations", "health", "metric_observations",
                 "observation_metrics")


class SpoolFull(RuntimeError):
    """The bounded observation spool cannot take another record; the caller counts and reports."""


class ObservationSpool(Protocol):
    """One process run's append-only durable record store (INV-OBSERVATION-001)."""
    process_run_id: str

    def append(self, kind: str, event: dict) -> int: ...
    def close(self) -> None: ...


class DeskHttp(Protocol):
    """The desk routes of the previous implementation, as the viewer calls them.

    The viewer reads it only when a desk service is injected; a module satisfies it structurally."""
    JSON: str
    READ_TIMEOUT_SECONDS: float
    ROUTES_POST: set

    def handle_get(self, desk, path: str): ...
    def check_intent(self, handler, authority: str): ...
    def read_body(self, handler): ...
    def handle_post(self, desk, path: str, document: dict): ...
    def error(self, code: str) -> bytes: ...


@dataclass(frozen=True)
class CollectorPorts:
    """What the previous implementation imported from other contexts, injected.

    `run_process` runs the read-only docker commands; `bus_factory(url)` builds the Redis bus whose streams are read;
    each projection takes the read-only store and returns its owner's status; `registered(store)` is the Fleet's
    registered configuration (it raises the coordination `FleetRefused` when unregistered)."""
    run_process: Callable
    bus_factory: Callable
    fleet: Callable
    research_program: Callable
    portfolio: Callable
    fleet_backlog: Callable
    host_delivery: Callable
    worker_session: Callable
    continuation: Callable
    discovery_pressure: Callable
    registered: Callable
