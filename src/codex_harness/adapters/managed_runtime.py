"""Permanent entry shim: `python -m codex_harness.adapters.managed_runtime launch|entry|supervise --state-dir DIR ...`.

The launched managed Fleet processes' argv (the previous implementation ManagedFleetTarget and the unit's ExecStart, byte-identical
adapters-move); it only delegates, and re-exports the wired `supervise` for module-name imports.
"""
from codex_harness.entry.processes.managed_runtime import main, supervise

__all__ = ["main", "supervise"]

if __name__ == "__main__":
    raise SystemExit(main())
