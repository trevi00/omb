"""The one ISO-8601 to epoch-seconds reader for audit and threshold telemetry.

Layer: kernel
Context: kernel
Owns: `timestamp`, the previous implementation `domain/skill_audit.timestamp` (context skills audit and research threshold replay share it, neither may import the other)
Does not own: the skill audit aggregation (context.domain.skills.audit)
Entry points: timestamp
Contracts: INV-SKILL-HISTORY-001

Provenance: carried over from the previous implementation.
"""
from datetime import datetime, timezone


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.replace(tzinfo=timezone.utc).timestamp() if parsed.tzinfo is None else parsed.timestamp()
    except (ValueError, OverflowError, OSError):
        return None
