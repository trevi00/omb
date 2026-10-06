"""The `zeus send` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus send`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition, composition.cli, composition.cli_bus)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    send = commands.add_parser("send")
    send.add_argument("file")


def run(args) -> None:
    import json
    from pathlib import Path

    from codex_harness.composition import build, cli_bus
    from codex_harness.composition import cli as composition
    from codex_harness.entry.cli.output import emit
    service = build()
    message = composition.validate_message(json.loads(Path(args.file).read_text(encoding="utf-8")))
    service.org.authorize(message)
    emit({"stream_id": cli_bus.bus().publish(message)})
