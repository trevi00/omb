"""Permanent entry shim: `python -m codex_harness.adapters.host_delivery service --state-dir DIR [--max-seconds N]`.

The launched delivery service's argv (the previous implementation ProcessHostTarget, byte-identical, adapters-move); it only delegates.
"""
from codex_harness.entry.processes.delivery_service import main

if __name__ == "__main__":
    raise SystemExit(main())
