"""Windows console and tree-kill primitives for piped, non-interactive children.

Layer: adapters
Context: host_os
Owns: the Win32 creation flags by value and the `taskkill /T` argv
Does not own: process creation (host_os.adapters.process_groups.popen/run, the one chokepoint)
Entry points: creation_kwargs, taskkill_argv, CREATE_NO_WINDOW, CREATE_NEW_PROCESS_GROUP

Provenance: carried over from the previous implementation.
"""
from __future__ import annotations

import subprocess

# Win32 creation flags by value: `subprocess` exposes them only on Windows, and the helper below
# has to be able to describe the Windows policy from a Linux test.
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)


def creation_kwargs(*, process_group: bool = False, creationflags: int = 0) -> dict:
    """CREATE_NO_WINDOW, the caller's extra flags and, when the caller owns the child's group for its
    own kill path, CREATE_NEW_PROCESS_GROUP. CREATE_NEW_CONSOLE and DETACHED_PROCESS are never added:
    Windows ignores CREATE_NO_WINDOW next to either of them."""
    flags = CREATE_NO_WINDOW | creationflags
    if process_group:
        flags |= CREATE_NEW_PROCESS_GROUP
    return {"creationflags": flags}


def taskkill_argv(pid: int) -> list[str]:
    """Kill a child's whole tree on Windows (`/T`), forcibly (`/F`)."""
    return ["taskkill", "/PID", str(pid), "/T", "/F"]
