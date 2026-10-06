"""Kernel ports: the clock, the id source and the observation sink every context may depend on.

Layer: kernel
Context: kernel
Owns: the Protocols only; `kernel.ids` holds the system implementations
Does not own: the observation spool itself (observation context)
Entry points: Clock.now, IdSource.uuid4, ObservationSink.append, REASON_CODE

Time and identifiers are injected (R-D): target code that records a time or
mints an id takes a Clock/IdSource, so a differential run supplies the scripted fakes instead of
patching the standard library.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Protocol
from uuid import UUID


class Clock(Protocol):
    def now(self) -> datetime:
        """The current time as an aware UTC datetime."""
        ...


class IdSource(Protocol):
    def uuid4(self) -> UUID:
        """A fresh random (version 4) UUID."""
        ...


# The syntax of an observation `reason_code` (the previous implementation `domain/observation.REASON_CODE`, the same pattern). It is
# part of the observation port contract, defined once here because producers in every context (execution's
# worker sessions) must only hand the observer a code of this form, and observation validates
# with the same definition; no context imports observation.
REASON_CODE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,79}$")


class ObservationSink(Protocol):
    """Append-only observation records of one process run (INV-OBSERVATION-001 is owned by
    observation; this is the narrow write side other contexts are allowed to see)."""

    def append(self, kind: str, event: dict) -> int: ...
