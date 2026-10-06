"""The `zeus` CLI output helper (the previous implementation cli.py).

Layer: entry
Owns: emit (print one JSON document to stdout)
Does not own: the roots and the dispatch (the other modules of this package)
Entry points: emit
Contracts: none

Provenance: carried over from the previous implementation.
"""

import json


def emit(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2), flush=True)
