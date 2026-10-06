"""Observe a Git source without executing its hooks or project code.

Layer: adapters
Context: research
Owns: observe_source, the read-only Git observation of a reverse-documentation source project (worktree root, HEAD, tree, dirty or clean) that never executes the project's hooks or code
Does not own: the process runner (host_os's run_process, injected as `run_process` by composition), the progress rules (research.application.reverse_progress, which consumes the observation) and the CLI
Entry points: observe_source
Contracts: INV-REVERSE-001

Provenance: carried over from the previous implementation.
"""
from __future__ import annotations

from pathlib import Path

from codex_harness.kernel.errors import require


def observe_source(path, *, run_process=None):
    # Host_os's `run_process`, wired by composition. The check precedes the `try`: its `except Exception` would turn the refusal
    # into an `unknown` observation.
    require(run_process is not None, 'run_process is not wired')
    root = str(Path(path).resolve())
    def git(*args):
        result = run_process(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
                              '-c', 'core.untrackedCache=false', '-C', root, *args], timeout=15)
        if result.returncode:
            raise ValueError('Git source observation failed')
        return result.stdout.strip()
    try:
        repository = git('rev-parse', '--show-toplevel')
        if Path(repository).resolve() != Path(root):
            return {'status': 'unknown', 'repository': repository,
                    'reason': 'Source must identify the Git worktree root'}
        before = git('rev-parse', 'HEAD')
        tree = git('rev-parse', before + '^{tree}')
        dirty = bool(git('status', '--porcelain=v1', '--untracked-files=all',
                         '--ignore-submodules=none'))
        after = git('rev-parse', 'HEAD')
        if before != after:
            return {'status': 'unknown', 'repository': repository, 'reason': 'HEAD changed during observation'}
        return {'status': 'dirty' if dirty else 'clean',
                'repository': str(Path(repository).resolve()), 'commit': before, 'tree': tree}
    except Exception as exc:
        return {'status': 'unknown', 'repository': root, 'reason': type(exc).__name__}
