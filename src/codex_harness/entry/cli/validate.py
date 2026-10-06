"""The `zeus validate` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus validate`), run (its store-free body)
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    v = commands.add_parser("validate")
    v.add_argument("file")


def run(args) -> None:
    import json
    from pathlib import Path

    from codex_harness.composition.cli import organization, validate_message
    from codex_harness.entry.cli.output import emit
    message = validate_message(json.loads(Path(args.file).read_text(encoding="utf-8")))
    organization().authorize(message)
    emit({"valid": True, "message_id": message["message_id"]})
