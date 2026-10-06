"""Permanent entry shim: `python -m codex_harness.adapters.continuation_process --launch <dir> --seconds <s> -- <command>`.

The guardian argv every guarded launch spawns (the previous implementation ENTRY_ARGV, byte-identical); it only delegates.
"""
from codex_harness.entry.processes.guardian import main

if __name__ == "__main__":
    raise SystemExit(main())
