"""The `zeus run-command` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus run-command`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""

import argparse


def add_parser(commands) -> None:
    run = commands.add_parser("run-command")
    run.add_argument("--timeout", type=int, default=120)
    run.add_argument("argv", nargs=argparse.REMAINDER)


def run(args) -> None:
    import os

    from codex_harness.composition import build
    from codex_harness.composition import cli as composition
    from codex_harness.entry.cli.output import emit
    from codex_harness.kernel.errors import require
    service = build()
    argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    require(bool(argv), "Command argv required after --")
    command = composition.hook_units(service).prepare_command(argv, "windows" if os.name == "nt" else "linux")
    result = composition.run_process(command, timeout=args.timeout)
    emit({"argv": command, "exit_code": result.returncode, "stdout": result.stdout,
          "stderr": result.stderr})
    if result.returncode:
        raise SystemExit(result.returncode)
