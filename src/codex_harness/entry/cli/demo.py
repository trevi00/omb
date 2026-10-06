"""The `zeus demo` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus demo`), run (its store-backed body), _demo and _generation
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    d = commands.add_parser("demo")
    d.add_argument("--scope", default="bootstrap/windows/codex")


def _generation(service, agent: str) -> int:
    with service.store.transaction() as tx:
        return (tx.get("sessions", agent) or {"generation": 0})["generation"]


def _demo(service, scope: str) -> dict:
    """Scripted bootstrap lifecycle using real persistence, not autonomous agent review."""
    from uuid import uuid4

    from codex_harness.composition import cli as composition
    from codex_harness.kernel.ids import digest
    from codex_harness.kernel.message import envelope
    hooks, incidents, sessions = (composition.hook_units(service), composition.incidents(service),
                                  composition.sessions(service))
    correlation = "bootstrap-" + str(uuid4())
    records = []
    for _ in range(2):
        message = envelope("incident.report", "worker:implementation", "lead:improvement",
                           "record_incident", {"occurrence_id": str(uuid4()),
                           "root_cause": "powershell-codex-ps1-policy", "scope": scope,
                           "evidence_refs": ["fixture:windows-codex-ps1-policy"]}, correlation)
        records.append(incidents.record_incident(composition.validate_message(message)))
    hook_id = records[-1]["hook_id"]
    existing = hooks.get_hook(hook_id)
    if existing["status"] == "active":
        return {"mode": "scripted-bootstrap", "already_active": hook_id, "incidents": records}
    spec = {"kind": "executable_alias", "platform": "windows", "match": "codex.ps1",
            "replacement": "codex.cmd"}
    revision = "spec-sha256:" + digest(spec)
    hooks.propose(hook_id, "worker:implementation", spec, revision)
    canary = composition.executable_canary(spec)
    for actor in ("lead:improvement", "conductor"):
        hooks.review(hook_id, actor, revision, digest(spec), True,
                     "fixture:scripted-review-not-llm")
    hooks.record_canary(hook_id, revision, digest(spec), canary["checks"])
    if all(canary["checks"].values()):
        hooks.activate(hook_id)
    checkpoint = sessions.checkpoint("worker:implementation", _generation(service, "worker:implementation"),
                                     {"next_action": "apply active hooks before the next command",
                                      "source_revision": revision, "graph_snapshot": "bootstrap-fixture",
                                      "hook_id": hook_id})
    return {"mode": "scripted-bootstrap; no autonomous PR review or deployment",
            "incidents": records, "hook": hooks.get_hook(hook_id), "canary": canary,
            "prepared_command": hooks.prepare_command(["codex.ps1", "--version"], "windows"),
            "checkpoint": checkpoint}


def run(args) -> None:
    from codex_harness.composition import build
    from codex_harness.entry.cli.output import emit
    emit(_demo(build(), args.scope))
