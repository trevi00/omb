"""The observation JSON-Schema validation (the packaged `observation.schema.json`).

Layer: adapters
Context: observation
Owns: the jsonschema check of one observation event before it is spooled or collected
Does not own: the observation shape and its builder (`observation.domain.observation`), the six-W message schema (`storage.adapters.message_schema`), the collector that applies the check (`observation.application.observations`, injected as `validate`), its composition
Entry points: validate_observation
Contracts: INV-OBSERVATION-001

Provenance: carried over from the previous implementation.
"""

import json
from importlib.resources import files

from jsonschema import Draft202012Validator, FormatChecker

from codex_harness.kernel.errors import ContractError

OBSERVATION_SCHEMA = json.loads(files("codex_harness.resources").joinpath("observation.schema.json").read_text())
OBSERVATION_VALIDATOR = Draft202012Validator(OBSERVATION_SCHEMA, format_checker=FormatChecker())


def validate_observation(event: dict) -> dict:
    """INV-OBSERVATION-001: the versioned observation schema, a different contract from six-W.

    The error names the path and the failed keyword only. jsonschema's default message repeats
    the offending instance value, which is exactly what a refused record must not carry into
    quarantine rows or health files.
    """
    errors = sorted(OBSERVATION_VALIDATOR.iter_errors(event), key=lambda e: str(e.path))
    if errors:
        raise ContractError("; ".join(f"{list(e.path)}: {e.validator}" for e in errors[:5]))
    return event
