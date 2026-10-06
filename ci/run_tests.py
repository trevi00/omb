#!/usr/bin/env python3
"""Run the CI test selections from ci/excluded-tests.txt (Python standard library only).

    python3 ci/run_tests.py unit          pytest with every listed module ignored and every listed id deselected
    python3 ci/run_tests.py integration   only the listed ids whose reason starts with 'integration', with a pytest
                                          base directory outside the checkout (RUNNER_TEMP, else the system temp dir)
    python3 ci/run_tests.py --self-test

File format: lines starting with # are comments; every other line is <id> TAB <reason>. An id with :: is a test node
(deselected), anything else is a module path (ignored), except that a reason starting with "omitted" names a module
that is not in this tree at all (the entry records it; nothing is passed to pytest). A malformed line stops the run (exit 2). The pytest exit code
is passed through. A summary of what was excluded and why (counts by reason) goes to stdout and, when set, to the
GitHub step summary. Nothing is excluded that is not listed.
"""
import os
import subprocess
import sys
import tempfile

LIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "excluded-tests.txt")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse(text):
    entries = []
    for no, line in enumerate(text.split("\n"), 1):
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"excluded-tests.txt:{no}: expected <id> TAB <reason>")
        entries.append((parts[0], parts[1]))
    return entries


def unit_args(entries):
    args = []
    for tid, reason in entries:
        if reason.startswith("omitted"):
            continue  # the module is not in this tree; the entry only records what is missing
        args.append(("--deselect=" if "::" in tid else "--ignore=") + tid)
    return args


def integration_ids(entries):
    return [tid for tid, reason in entries if reason.startswith("integration")]


def by_reason(entries):
    out = {}
    for _, reason in entries:
        out[reason] = out.get(reason, 0) + 1
    return dict(sorted(out.items()))


def summary(mode, entries, selected):
    lines = [f"### {mode} job", ""]
    if mode == "unit":
        lines.append(f"Excluded from the unit run: {len(entries)} entries (ci/excluded-tests.txt), by reason:")
        lines += [f"- {n} x {reason}" for reason, n in by_reason(entries).items()]
    else:
        lines.append(f"Running {len(selected)} integration-planned tests; they need no service and no secret. The job's "
                     "PostgreSQL and Redis containers get no connection settings; no service-backed test runs in OMB CI.")
    return "\n".join(lines) + "\n"


def run(mode, extra):
    with open(LIST, encoding="utf-8") as f:
        entries = parse(f.read())
    selected = integration_ids(entries)
    text = summary(mode, entries, selected)
    sys.stdout.write(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text)
    cmd = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q"]
    if mode == "unit":
        cmd += unit_args(entries)
    else:
        base = os.path.join(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir(), "omb-integration-base")
        cmd += ["--basetemp=" + base] + selected
    return subprocess.run(cmd + extra, cwd=ROOT).returncode


def self_test():
    entries = parse("# c\n\na.py\treason one\nb.py::t[1]\tintegration (job x)\nc.py\tomitted: reason\n")
    ok = entries == [("a.py", "reason one"), ("b.py::t[1]", "integration (job x)"), ("c.py", "omitted: reason")]
    ok = ok and unit_args(entries) == ["--ignore=a.py", "--deselect=b.py::t[1]"]
    ok = ok and integration_ids(entries) == ["b.py::t[1]"] and by_reason(entries) == {
        "integration (job x)": 1, "omitted: reason": 1, "reason one": 1}
    for bad in ("a.py\n", "a.py\tr\textra\n", "\treason\n"):
        try:
            parse(bad)
            ok = False
        except ValueError:
            pass
    print("self-test: " + ("ok" if ok else "FAILED"))
    return 0 if ok else 1


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    if not argv or argv[0] not in ("unit", "integration"):
        print("usage: run_tests.py unit|integration [pytest args] | --self-test", file=sys.stderr)
        return 2
    try:
        return run(argv[0], argv[1:])
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
