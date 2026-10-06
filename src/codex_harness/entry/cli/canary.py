"""The `zeus canary` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus canary`), run (its store-free body)
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    canary = commands.add_parser("canary")
    canary.add_argument("--live", action="store_true", help="Execute a real Codex file task (uses account quota)")


def run(args) -> None:
    from pathlib import Path

    from codex_harness.composition import cli as composition
    from codex_harness.entry.cli.output import emit
    runtime = composition.codex_runtime()
    result = runtime.probe()
    if args.live:
        import tempfile

        with tempfile.TemporaryDirectory(prefix="harness-canary-") as directory:
            fixture = Path(directory) / "input.txt"
            fixture.write_text("HARNESS_CANARY_42", encoding="utf-8")
            schema = {"type": "object", "additionalProperties": False,
                      "properties": {"value": {"type": "string"}}, "required": ["value"]}
            run = runtime.run("Read input.txt, write its exact contents to output.txt. "
                              "Return the exact input in the value field. Use no network.",
                              directory, schema)
            output = Path(directory) / "output.txt"
            result["live_passed"] = (run["answer"]["value"] == "HARNESS_CANARY_42"
                                     and output.exists()
                                     and output.read_text(encoding="utf-8").strip() == "HARNESS_CANARY_42")
            result["event_count"] = len(run["events"])
    emit(result)
    if not result["passed"] or result.get("live_passed") is False:
        raise SystemExit(1)
