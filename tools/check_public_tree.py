#!/usr/bin/env python3
"""Public-tree boundary check for the doc-only OMB repository.

Purpose: check the git-tracked file set of the repository it runs in against
the allowlist in public-files.txt, and check the content shape of every
tracked text file (private artifacts, secret shapes, format) plus a small
policy for workflow files. Python standard library only (3.10-3.14).

Output: one line per finding, "<path>:<line>: <rule-id>" (line 0 for
path-level rules), sorted, then "checked <n> files, <m> findings". It never
prints matched text, an excerpt or any file content.

Rules: allowlist-missing, allowlist-stale, allowlist-format, private-path,
not-text, too-large, crlf, no-final-newline, trailing-whitespace,
private-key, token-shape, home-path, email, url-host, ip-literal,
workflow-permissions, workflow-unpinned, workflow-forbidden,
workflow-persist-credentials.

Exit codes: 0 clean; 1 findings; 2 environment or usage error (not a git
repository, git missing, unknown argument, unreadable allowlist).

--self-test runs negative controls on temporary git repositories: a clean
one must give no findings and each rule must fire on exactly one planted
violation.

A passing run means the public file boundary and format checks passed. It
does NOT mean that any code was built or tested; this repository has none.
"""

import ipaddress
import os
import re
import shutil
import subprocess
import sys
import tempfile

ALLOWLIST = "public-files.txt"
MAX_BYTES = 262144
BOM = b"\xef\xbb\xbf"

PRIVATE_COMPONENTS = frozenset(
    ["private", "artifacts", "scratch", "evidence", ".claude", ".codex",
     ".venv", "node_modules", "__pycache__"])
PRIVATE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".jsonl", ".log",
                    ".sqlite", ".sqlite3", ".db", ".dump")
PRIVATE_PREFIXES = ("id_rsa", "id_ecdsa", "id_ed25519")

# Patterns whose own source would match a rule are built from parts.
_DASHES = "-" * 5
PRIVATE_KEY_RE = re.compile(_DASHES + "BEG" + "IN" + ".*" + "PRIVATE" + " KEY" + _DASHES)
TOKEN_RES = [re.compile(p) for p in (
    "sk-" + "ant-[A-Za-z0-9_-]{8,}",
    "gh[pou" + "sr]_[A-Za-z0-9]{20,}",
    "github" + "_pat_[A-Za-z0-9_]{20,}",
    "AK" + "IA[0-9A-Z]{16}",
    "xo" + "x[abprs]-[A-Za-z0-9-]{10,}",
)]
_NAME = "[A-Za-z0-9._-]+"
HOME_RE = re.compile(
    "/ho" + "me/" + _NAME + "/"
    + "|/Us" + "ers/" + _NAME + "/"
    + "|(?i:[a-z]:" + r"\\" + "users" + r"\\)")
EMAIL_RE = re.compile("[A-Za-z0-9._%+-]+" + "@" + r"([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
EMAIL_DOMAINS = frozenset(["example.com", "example.org", "example.net"])
EMAIL_SUFFIX = "users.noreply.github.com"
URL_RE = re.compile("(http" + "s?)" + "://" + r"([^\s/:?#\"'<>()\[\]]*)")
URL_HOSTS = frozenset(["github.com", "docs.github.com", "example.com",
                       "example.org", "example.net"])
IP_RE = re.compile(r"(?<!\d)(?<!\d\.)(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(?!\d)(?!\.\d)")
IP_OK = [ipaddress.ip_address("127.0.0.1"), ipaddress.ip_address("0.0.0.0")]
IP_NETS = [ipaddress.ip_network(n) for n in
           ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]

WF_WRITE_RE = re.compile(r"^\s+[a-z-]+:\s*write\s*$")
WF_USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*(.*)$")
WF_PINNED_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^@\s]+)?@[0-9a-f]{40}")
WF_PERSIST_RE = re.compile(r"^\s*persist-credentials:\s*false\s*$")
WF_BAD_PERMS = ("write" + "-all", "read" + "-all")
WF_FORBIDDEN = ("pull_request" + "_target", "workflow" + "_run",
                "secrets" + ".", "${{ github" + ".event.")


class EnvError(Exception):
    pass


def _git(root, *args):
    env = {k: v for k, v in os.environ.items()
           if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
    try:
        res = subprocess.run(["git", *args], cwd=root, env=env,
                             capture_output=True)
    except OSError:
        raise EnvError("git unavailable")
    return res


def repo_root(cwd):
    res = _git(cwd, "rev-parse", "--show-toplevel")
    if res.returncode != 0:
        raise EnvError("not a git repository")
    return os.fsdecode(res.stdout).strip()


def tracked_files(root):
    res = _git(root, "ls-files", "-z")
    if res.returncode != 0:
        raise EnvError("git ls-files failed")
    return sorted(os.fsdecode(p) for p in res.stdout.split(b"\0") if p)


def read_allowlist(root):
    """Return (entries, findings) from the allowlist file."""
    try:
        with open(os.path.join(root, ALLOWLIST), "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        raise EnvError("allowlist unreadable")
    if text.startswith("﻿"):
        text = text[1:]
    entries, findings, prev = set(), [], None
    for no, line in enumerate(text.split("\n"), 1):
        if line.startswith("#"):
            continue
        if no == len(text.split("\n")) and line == "":
            continue  # empty piece after the final newline
        if line == "" or line != line.strip():
            findings.append((ALLOWLIST, no, "allowlist-format"))
        entry = line.strip()
        if entry:
            if prev is not None and entry <= prev:
                findings.append((ALLOWLIST, no, "allowlist-format"))
            prev = entry
            entries.add(entry)
    return entries, findings


def path_findings(path):
    parts = path.split("/")
    base = parts[-1]
    low = base.lower()
    bad = (any(p in PRIVATE_COMPONENTS for p in parts)
           or (base == ".env" or (base.startswith(".env.") and base != ".env.example"))
           or low.endswith(PRIVATE_SUFFIXES)
           or base.startswith(PRIVATE_PREFIXES))
    return [(path, 0, "private-path")] if bad else []


def ip_is_ok(addr):
    return addr in IP_OK or any(addr in net for net in IP_NETS)


def line_findings(path, no, line):
    out = []
    if line.endswith((" ", "\t")):
        out.append("trailing-whitespace")
    if PRIVATE_KEY_RE.search(line):
        out.append("private-key")
    if any(r.search(line) for r in TOKEN_RES):
        out.append("token-shape")
    if HOME_RE.search(line):
        out.append("home-path")
    for m in EMAIL_RE.finditer(line):
        dom = m.group(1).lower()
        if dom not in EMAIL_DOMAINS and not dom.endswith(EMAIL_SUFFIX):
            out.append("email")
            break
    for m in URL_RE.finditer(line):
        if m.group(1) == "http" or m.group(2).lower() not in URL_HOSTS:
            out.append("url-host")
            break
    for m in IP_RE.finditer(line):
        octets = [int(g) for g in m.groups()]
        if max(octets) <= 255 and not ip_is_ok(
                ipaddress.ip_address(".".join(map(str, octets)))):
            out.append("ip-literal")
            break
    return [(path, no, r) for r in out]


def workflow_findings(path, lines):
    out = []
    text = "\n".join(lines)
    if (not any(l == "permissions:" for l in lines)
            or any(w in text for w in WF_BAD_PERMS)):
        out.append((path, 0, "workflow-permissions"))
    uses_checkout = False
    for no, line in enumerate(lines, 1):
        if WF_WRITE_RE.match(line):
            out.append((path, no, "workflow-permissions"))
        m = WF_USES_RE.match(line)
        if m:
            val = re.sub(r"\s+#.*$", "", m.group(1)).strip().strip("'\"")
            if not WF_PINNED_RE.fullmatch(val):
                out.append((path, no, "workflow-unpinned"))
            if val.startswith("actions/checkout@"):
                uses_checkout = True
        if any(f in line for f in WF_FORBIDDEN):
            out.append((path, no, "workflow-forbidden"))
    if uses_checkout and not any(WF_PERSIST_RE.match(l) for l in lines):
        out.append((path, 0, "workflow-persist-credentials"))
    return out


def content_findings(root, path):
    try:
        with open(os.path.join(root, path), "rb") as fh:
            raw = fh.read()
    except OSError:
        raise EnvError("tracked file unreadable")
    out = []
    if len(raw) > MAX_BYTES:
        out.append((path, 0, "too-large"))
    body = raw[len(BOM):] if raw.startswith(BOM) else raw
    try:
        if b"\0" in body:
            raise ValueError
        text = body.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return out + [(path, 0, "not-text")]
    if raw and not raw.endswith(b"\n"):
        out.append((path, 0, "no-final-newline"))
    lines = text.split("\n")
    for no, line in enumerate(lines, 1):
        if "\r" in line:
            out.append((path, no, "crlf"))
            break
    for no, line in enumerate(lines, 1):
        out.extend(line_findings(path, no, line))
    if (path.startswith(".github/workflows/")
            and path.endswith((".yml", ".yaml"))):
        out.extend(workflow_findings(path, lines))
    return out


def analyze(root):
    """Return (sorted unique findings, number of tracked files)."""
    files = tracked_files(root)
    listed, findings = read_allowlist(root)
    findings = list(findings)
    for path in files:
        if path not in listed:
            findings.append((path, 0, "allowlist-missing"))
        findings.extend(path_findings(path))
        findings.extend(content_findings(root, path))
    tracked = set(files)
    for entry in listed - tracked:
        findings.append((ALLOWLIST, 0, "allowlist-stale"))
    return sorted(set(findings)), len(files)


def report(findings, count, out):
    for path, no, rule in findings:
        print(f"{path}:{no}: {rule}", file=out)
    print(f"checked {count} files, {len(findings)} findings", file=out)


# ---- negative controls -------------------------------------------------

def _clean_workflow():
    return "\n".join([
        "name: sample",
        "on:",
        "  push:",
        "    branches: [main]",
        "permissions:",
        "  contents: read",
        "jobs:",
        "  sample:",
        "    runs-on: ubuntu-24.04",
        "    steps:",
        "      - uses: actions/checkout@" + "a" * 40 + " # pinned",
        "        with:",
        "          persist-credentials: false",
        "      - run: echo ok",
        ""])


def _wf(**changes):
    text = _clean_workflow()
    for old, new in changes.items():
        text = text.replace(old.replace("__", " "), new)
    return text


def _controls():
    """Yield (name, files, expected rules, raw allowlist or None)."""
    ok = "# notes\n\nA link: [x](" + "https" + "://example.com/).\n"
    wf = ".github/workflows/x.yml"
    chk = "actions/checkout@" + "a" * 40
    yield ("clean", {"a.md": ok, "b.md": "Contact: dev@example.org\n",
                     wf: _clean_workflow()}, set(), None)
    plants = [
        ("allowlist-missing", {"a.md": ok, "extra.md": ok}, "OMIT:extra.md"),
        ("allowlist-stale", {"a.md": ok}, "EXTRA:ghost.md"),
        ("allowlist-format", {"a.md": ok, "b.md": ok}, "RAW:b.md\na.md\npublic-files.txt\n"),
        ("private-path", {"private/n.md": ok}, None),
        ("not-text", {"a.md": b"\xff\xfe\xfa\n"}, None),
        ("too-large", {"a.md": "word\n" * 60000}, None),
        ("crlf", {"a.md": "one\r\ntwo\r\n"}, None),
        ("no-final-newline", {"a.md": "one"}, None),
        ("trailing-whitespace", {"a.md": "one \n"}, None),
        ("private-key", {"a.md": "-----BEG" + "IN RSA PRIV" + "ATE KEY-----\n"}, None),
        ("token-shape", {"a.md": "sk-" + "ant-" + "abcdefgh12\n"}, None),
        ("home-path", {"a.md": "see /ho" + "me/dev/x\n"}, None),
        ("email", {"a.md": "me@" + "corp.test\n"}, None),
        ("url-host", {"a.md": "https" + "://other.test/x\n"}, None),
        ("ip-literal", {"a.md": "host 10." + "1.2.3 here\n"}, None),
        ("workflow-permissions", {wf: _wf(**{"permissions:": "perms:"})}, None),
        ("workflow-unpinned", {wf: _wf(**{chk: "actions/checkout@v7"})}, None),
        ("workflow-forbidden", {wf: _clean_workflow() + "# pull_request" + "_target\n"}, None),
        ("workflow-persist-credentials",
         {wf: _wf(**{"persist-credentials: false": "fetch-depth: 1"})}, None),
        # extra controls: variants of the rules above
        ("not-text", {"a.md": b"one\0two\n"}, None),
        ("private-path", {".env": ok}, None),
        ("private-path", {"k/id_rsa_x": ok}, None),
        ("url-host", {"a.md": "http" + "://example.com/\n"}, None),
        ("ip-literal", {"a.md": "up 8.8." + "8.8\n"}, None),
        ("email", {"a.md": "x@" + "sub.example.com\n"}, None),
        ("workflow-permissions", {wf: _wf(**{"contents: read": "contents: write"})}, None),
        ("workflow-unpinned", {wf: _wf(**{chk: "./local"})}, None),
        ("workflow-forbidden", {wf: _clean_workflow() + "# ${{ sec" + "rets.X }}\n"}, None),
    ]
    for rule, files, mode in plants:
        yield (rule, files, {rule}, mode)
    # allowed shapes must stay quiet
    yield ("allowed-shapes",
           {"a.md": "ok 127.0.0.1 192.0.2.7 u@users.noreply.github.com "
                    "https" + "://docs.github.com/x\n"}, set(), None)


def _build(base, files, mode):
    for rel, content in files.items():
        full = os.path.join(base, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        data = content if isinstance(content, bytes) else content.encode()
        with open(full, "wb") as fh:
            fh.write(data)
    names = set(files) | {ALLOWLIST}
    raw = None
    if mode and mode.startswith("OMIT:"):
        names.discard(mode[5:])
    elif mode and mode.startswith("EXTRA:"):
        names.add(mode[6:])
    elif mode and mode.startswith("RAW:"):
        raw = "# list\n" + mode[4:]
        names = None
    if raw is None:
        raw = "# list\n" + "".join(n + "\n" for n in sorted(names))
    with open(os.path.join(base, ALLOWLIST), "w", newline="\n") as fh:
        fh.write(raw)


def self_test():
    passed = total = 0
    for name, files, expect, mode in _controls():
        total += 1
        base = tempfile.mkdtemp()
        try:
            _git(base, "init", "-q")
            _build(base, files, mode)
            _git(base, "add", "-f", "-A")
            found, _ = analyze(base)
            got = {r for _, _, r in found}
            if got == expect:
                passed += 1
            else:
                print(f"control failed: {name}")
        except EnvError:
            print(f"control failed: {name}")
        finally:
            shutil.rmtree(base, ignore_errors=True)
    print(f"self-test: {passed}/{total} controls passed")
    return 0 if passed == total else 1


def main(argv):
    if argv not in ([], ["--self-test"]):
        print("usage: check_public_tree.py [--self-test]", file=sys.stderr)
        return 2
    try:
        if argv:
            return self_test()
        root = repo_root(os.getcwd())
        findings, count = analyze(root)
    except EnvError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    report(findings, count, sys.stdout)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
