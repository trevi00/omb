"""The `zeus desk` argument parser (the previous implementation).

Layer: entry
Owns: add_parser (the argument shape of `zeus desk`)
Does not own: dispatch and composition
Entry points: add_parser
Contracts: none

Provenance: carried over from the previous implementation.
"""


def add_parser(commands) -> None:
    desk = commands.add_parser("desk", help="Local front-door conversation runner; no conductor, no retries")
    sub = desk.add_subparsers(dest="desk_command", required=True)
    run = sub.add_parser("run", help="Own the desk and process queued local requests one at a time")
    run.add_argument("--revision", required=True, help="Full 40-hex base revision every request is answered at")
    run.add_argument("--once", action="store_true", help="Process what is queued now, then exit")
    status = sub.add_parser("status", help="Read desk sessions; store read only")
    status.add_argument("--revision", required=True, help="Full 40-hex base revision of this desk")
