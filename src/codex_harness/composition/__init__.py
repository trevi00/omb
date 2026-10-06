"""Composition roots: object graphs per process kind: the store service handle and the database settings.

Layer: composition
Owns: ServiceHandle (the typed holder of the store and organization), build, database_url, redis_url
Does not own: the store-backed use-case wiring (composition.cli) and the settings layers (composition.configuration)
Entry points: build, database_url, redis_url
Contracts: none

Provenance: carried over from the previous implementation.
"""

from dataclasses import dataclass


def database_url() -> str:
    from codex_harness.composition.configuration import settings
    value = settings().get("HARNESS_DATABASE_URL")
    if not value:
        raise RuntimeError("Run scripts/setup.py or set HARNESS_DATABASE_URL")
    return value


@dataclass(frozen=True)
class ServiceHandle:
    store: object
    org: object


def build() -> ServiceHandle:
    from codex_harness.routing.adapters.organization_source import packaged_organization
    from codex_harness.storage.adapters.postgres_store import PostgresStore
    return ServiceHandle(PostgresStore(database_url()), packaged_organization())


def redis_url() -> str:
    from codex_harness.composition.configuration import settings
    return settings().get("HARNESS_REDIS_URL", "redis://127.0.0.1:56379/0")
