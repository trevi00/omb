"""The `zeus status` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus status`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition, composition.cli)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    commands.add_parser("status")


def run(args) -> None:
    from codex_harness.composition import build
    from codex_harness.entry.cli.output import emit
    from codex_harness.kernel.policy import POLICY
    service = build()
    with service.store.transaction() as tx:
        tasks = tx.scan("tasks")
        decisions = tx.scan("decisions_pending")
        terminal = [task for task in tasks if task["status"] in {"succeeded", "failed", "expired"}]
        emit({"policy": POLICY.snapshot(), "tasks": {state: sum(t["status"] == state for t in tasks)
              for state in sorted({t["status"] for t in tasks})},
              "observed_task_success_rate": sum(t["status"] == "succeeded" for t in terminal) / len(terminal) if terminal else None,
              "sample_size": len(terminal), "active_deployment": tx.get("deployment", "active"),
              "health": tx.get("health", "latest"),
              "blocked_decisions": [{"id": d["id"], "actor": d["actor"], "result": d.get("result")}
                                    for d in decisions if d["status"] in {"failed", "blocked"}],
              "pending_hooks": [{"id": h["id"], "status": h["status"]} for h in tx.scan("hooks") if h["status"] != "active"]})
