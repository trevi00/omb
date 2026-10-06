"""Finite-number predicate shared by every context that validates numeric policy values.

Layer: kernel
Context: kernel
Owns: the one definition of "a finite JSON number" (bool excluded)
Entry points: finite_number

Provenance: carried over from the previous implementation.
"""

from __future__ import annotations

import math


def finite_number(value) -> bool:
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False
