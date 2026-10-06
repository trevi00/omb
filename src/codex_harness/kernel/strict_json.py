"""Strict JSON reading: duplicate object keys are refused.

Layer: kernel
Context: kernel
Owns: `parse_json`, the pure strict JSON reader (the previous implementation, moved ahead)
Does not own: reading spec files, Git and the SDD adapter (the review SDD adapter, step 6)
Entry points: parse_json
Contracts: INV-SDD-001

Provenance: carried over from the previous implementation.
"""
import json

from codex_harness.kernel.errors import require


def parse_json(body):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(body, object_pairs_hook=unique)
