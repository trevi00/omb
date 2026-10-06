"""The `zeus seed-research-backlog` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus seed-research-backlog`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    seed = commands.add_parser("seed-research-backlog")
    seed.add_argument("--artifacts", required=True)


def run(args) -> None:
    from codex_harness.composition import build
    from codex_harness.composition import cli as composition
    from codex_harness.entry.cli.output import emit
    service = build()
    audits = composition.research_audits(service, composition.artifacts(args.artifacts))
    records = audits.seed_backlog()
    emit([{k: r[k] for k in ("id", "repository", "priority", "status", "activation",
                             "reviewed_paths")} for r in records])
