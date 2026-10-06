"""The `zeus execution-recovery` argument parser (the previous implementation cli.py).

Layer: entry
Owns: add_parser (the argument shape of `zeus execution-recovery`), run (its store-backed body)
Does not own: dispatch (entry.cli main) and composition (composition.cli, composition.configuration)
Entry points: add_parser, run
Contracts: none

Provenance: carried over from the previous implementation.
"""

from pathlib import Path


def add_parser(commands) -> None:
    recovery = commands.add_parser('execution-recovery', help='Explicit trusted local operator recovery; no human attestation')
    actions = recovery.add_subparsers(dest='recovery_action', required=True)
    prepare = actions.add_parser('prepare')
    prepare.add_argument('task_id')
    prepare.add_argument('--bucket', choices=['tasks', 'decisions_pending'], default='tasks')
    prepare.add_argument('--operation', choices=['migrate', 'resume', 'repair'], required=True)
    prepare.add_argument('--max-attempts', type=int, required=True, help='Total ceiling including attempts already spent')
    prepare.add_argument('--deadline', help='Future aware ISO timestamp; existing deadline cannot be removed')
    prepare.add_argument('--reason', required=True)
    prepare.add_argument('--operator', required=True, help='Audit label, not authenticated identity')
    prepare.add_argument('--evidence', action='append', required=True, help='Existing sha256 artifact reference')
    prepare.add_argument('--output', type=Path, required=True)
    apply = actions.add_parser('apply')
    apply.add_argument('--packet', type=Path, required=True)


def run(args) -> None:
    from codex_harness.composition import build
    from codex_harness.composition import cli as composition
    from codex_harness.composition.configuration import runtime_dir
    from codex_harness.entry.cli.output import emit
    from codex_harness.kernel.errors import ContractError, require
    from codex_harness.kernel.ids import canonical
    service = build()
    recovery = composition.execution_recovery(service, composition.artifacts(runtime_dir() / 'artifacts'))
    if args.recovery_action == 'prepare':
        packet = recovery.prepare(args.bucket, args.task_id, operation=args.operation,
            max_attempts=args.max_attempts, deadline=args.deadline, reason=args.reason,
            evidence_refs=args.evidence, operator=args.operator)
        try:
            with args.output.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(canonical(packet))
        except OSError as exc:
            raise ContractError('Cannot create new recovery packet file') from exc
        emit({'packet': str(args.output), 'authority': packet['authority'], 'applied': False})
    else:
        from codex_harness.kernel.strict_json import parse_json
        try:
            require(args.packet.stat().st_size <= 1024 * 1024, 'Recovery packet exceeds budget')
            packet = parse_json(args.packet.read_text(encoding='utf-8'))
        except OSError as exc:
            raise ContractError('Recovery packet file unavailable') from exc
        emit(recovery.apply(packet))
