"""Load the packaged organization graph.

Layer: adapters
Context: routing
Owns: reading `resources/organization.json` into a validated Organization
Does not own: authorization rules (routing.domain.organization)
Entry points: packaged_organization

Provenance: carried over from the previous implementation.
"""

from __future__ import annotations

import json
from importlib.resources import files

from codex_harness.routing.domain.organization import Agent, Organization


def packaged_organization() -> Organization:
    data = json.loads(files("codex_harness.resources").joinpath("organization.json").read_text())
    org = Organization({a["id"]: Agent(**a) for a in data["agents"]})
    org.validate()
    return org
