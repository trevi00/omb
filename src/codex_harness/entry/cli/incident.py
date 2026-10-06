"""The `zeus incident` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus incident`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    i = commands.add_parser("incident")
    i.add_argument("file")


def run(args) -> None:
    import json
    from pathlib import Path

    from codex_harness.composition import build
    from codex_harness.composition import cli as composition
    from codex_harness.entry.cli.output import emit
    service = build()
    emit(composition.incidents(service).record_incident(
        composition.validate_message(json.loads(Path(args.file).read_text(encoding="utf-8")))))
