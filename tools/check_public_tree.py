#!/usr/bin/env python3
"""Public-tree boundary check for the OMB repository (documents, imported code and tests, workflows).

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

Reviewed allowances (D-E2-16), each committed here with its reason and covered
by negative controls; none is a pattern that a new file could match by
accident, and a finding is never silenced by widening one:
private-path applies the artifact names (artifacts, evidence, scratch) to the
FIRST path component only, so a source package of that name is not an
artifact location; too-large has an exact per-path list (LARGE_FILES);
private-key has an exact path and pattern-kind list (PRIVATE_KEY_FILES) for
detector code and the tests of detectors; url-host accepts only the https
hosts in URL_HOSTS (reviewed one by one, each with its reason in
ci/public-hosts.txt; a private host is never listed), reads an escaped dot
as a dot and ignores an empty host; email accepts example.<tld>, *.invalid and
the GitHub no-reply suffix; ip-literal accepts the loopback block, the
unspecified address and the RFC 5737 documentation ranges; home-path accepts
only the placeholder user "example". LINE_ALLOWED lists the few exact
path:line entries where the shape is not what the rule is about (a template
marker, a key-type name, an XML namespace identifier, a test whose subject is
the shape itself), each with its reason.

Exit codes: 0 clean; 1 findings; 2 environment or usage error (not a git
repository, git missing, unknown argument, unreadable allowlist).

--self-test runs negative controls on temporary git repositories: a clean
one must give no findings and each rule must fire on exactly one planted
violation; it also checks, for every allowance, that an allowed value is
quiet and that near misses fire the rule.

A passing run means: every tracked file is listed in public-files.txt, and no
tracked text file has a private-artifact path shape, a key or token shape, a
URL host, email domain, IP address or home path outside the allowances, a
format violation or a workflow-policy violation. It does NOT mean that the
content holds nothing private that these shapes cannot detect (names,
internal identifiers, prose), that a file-level review or a license check was
done, or that the code builds, passes its tests or is secure; the CI jobs and
the release checks report those separately.
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
    ["private", ".claude", ".codex", ".venv", "node_modules", "__pycache__"])
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
EMAIL_EXAMPLE_RE = re.compile(r"example\.[a-z]{2,}")
EMAIL_INVALID_SUFFIX = ".invalid"
URL_RE = re.compile("(http" + "s?)" + "://" + r"([^\s/:?#\"'<>()\[\]]*)")
URL_HOSTS = frozenset(["api.github.com", "chatgpt.com", "docs.github.com", "example.com",
                       "example.invalid", "example.net", "example.org",
                       "files.pythonhosted.org", "github.com", "gitlab.com", "invalid.example",
                       "json-schema.org", "news.hada.io", "pypi.org", "tailwindcss.com",
                       "www.github.com", "www.psycopg.org", "www.w3.org"])
IP_RE = re.compile(r"(?<!\d)(?<!\d\.)(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(?!\d)(?!\.\d)")
IP_OK = [ipaddress.ip_address("127.0.0.1"), ipaddress.ip_address("0.0.0.0")]
IP_NETS = [ipaddress.ip_network(n) for n in
           ("127.0.0.0/8", "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]

HOME_PLACEHOLDERS = frozenset(["/ho" + "me/example/", "/Us" + "ers/example/"])

# Reviewed exceptions (D-E2-16): exact entries, each with its reason.
ARTIFACT_ROOTS = frozenset(["artifacts", "evidence", "scratch"])

LARGE_FILES = {
    "docs/contracts.md": "the reviewed contracts document; larger than the size limit by design",
}

PRIVATE_KEY_FILES = {
    ("src/codex_harness/knowledge/domain/profile_privacy.py", "detector-regex"): (
        "detector code: a regex that looks for key blocks"),
    ("src/codex_harness/observation/domain/observation.py", "detector-regex"): (
        "detector code: a regex that looks for key blocks"),
    ("tests/ported/test_observation_contract.py", "synthetic-sample"): (
        "a placeholder block fed to the detector (short body)"),
    ("tests/ported/test_profile_privacy.py", "synthetic-sample"): (
        "a placeholder block fed to the detector (short body)"),
}

LINE_ALLOWED = {
    ("email", "deploy/host/polkit/50-omb-managed-fleet.rules.in", 7): (
        "the deployment-namespace template marker, not an address"),
    ("email", "deploy/host/systemd/omb-monitor-web.service.in", 7): (
        "the deployment-namespace template marker, not an address"),
    ("email", "deploy/host/systemd/omb.target.in", 6): (
        "the deployment-namespace template marker, not an address"),
    ("email", "src/codex_harness/intake/adapters/ticket_authority.py", 71): (
        "an SSH key-type name that the signature check compares, not an address"),
    ("email", "tests/ported/test_check_binding.py", 116): (
        "a decorator inside the source text of a fixture file, not an address"),
    ("email", "tests/ported/test_git_workspace.py", 87): (
        "the scp-style forge remote spelling whose parsing the test is about"),
    ("email", "tests/ported/test_git_workspace.py", 88): (
        "the ssh-URL forge remote spelling whose parsing the test is about"),
    ("email", "tests/ported/test_release_suite.py", 175): (
        "a decorator inside the source text of a fixture file, not an address"),
    ("url-host", "src/codex_harness/research/adapters/research.py", 92): (
        "the Atom XML namespace identifier (an identifier, not a fetched URL)"),
    ("url-host", "src/codex_harness/research/adapters/research.py", 93): (
        "the Atom XML namespace identifier (an identifier, not a fetched URL)"),
    ("url-host", "src/codex_harness/resources/pipeline/overlays/java.overlay.yaml", 188): (
        "an http loopback URL with a placeholder port in held pipeline text (a check "
        "instruction, never fetched by the code); variant only"),
    ("url-host", "src/codex_harness/resources/pipeline/stages.yaml", 363): (
        "an http loopback URL with a placeholder port in held pipeline text (a check "
        "instruction, never fetched by the code); variant only"),
    ("url-host", "tests/ported/test_output_validation.py", 81): (
        "the JSON Schema dialect identifier the test feeds to the validator (an "
        "identifier, not a fetched URL)"),
    ("url-host", "tests/ported/test_output_validation.py", 93): (
        "the JSON Schema dialect identifier the test feeds to the validator (an "
        "identifier, not a fetched URL)"),
    ("url-host", "tests/ported/test_output_validation.py", 103): (
        "the JSON Schema dialect identifier the test feeds to the validator (an "
        "identifier, not a fetched URL)"),
    ("url-host", "tests/ported/test_research_program.py", 140): (
        "the plain-http spelling whose rejection the test is about"),
    ("url-host", "tests/ported/test_skill_history.py", 156): (
        "a fixture remote with embedded credentials (reserved placeholder host) whose "
        "rejection the test is about"),
}

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
    if text.startswith("\ufeff"):
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
           or parts[0] in ARTIFACT_ROOTS
           or (base == ".env" or (base.startswith(".env.") and base != ".env.example"))
           or low.endswith(PRIVATE_SUFFIXES)
           or base.startswith(PRIVATE_PREFIXES))
    return [(path, 0, "private-path")] if bad else []


def ip_is_ok(addr):
    return addr in IP_OK or any(addr in net for net in IP_NETS)


def email_domain_ok(dom):
    return (dom in EMAIL_DOMAINS or dom.endswith(EMAIL_SUFFIX)
            or EMAIL_EXAMPLE_RE.fullmatch(dom) is not None
            or (dom.endswith(EMAIL_INVALID_SUFFIX) and len(dom) > len(EMAIL_INVALID_SUFFIX)))


B64_RUN_RE = re.compile(r"[A-Za-z0-9+/]{32,}")
SAMPLE_KEY_RE = re.compile(r"KEY-----\\n[A-Za-z0-9+/=]{1,16}\\n-----END")


def key_kind(line):
    """The kind of a private-key-shaped line: "detector-regex" (a regex that looks for key blocks), "synthetic-sample"
    (a header, a short placeholder body and a footer written as an escaped one-line string) or None. A line that holds
    a long base64-like run is never one of them."""
    if B64_RUN_RE.search(line):
        return None
    if "re.compile(" in line:
        return "detector-regex"
    if SAMPLE_KEY_RE.search(line):
        return "synthetic-sample"
    return None


def key_line_allowed(path, line):
    return (path, key_kind(line)) in PRIVATE_KEY_FILES


def line_findings(path, no, line):
    out = []
    if line.endswith((" ", "\t")):
        out.append("trailing-whitespace")
    if PRIVATE_KEY_RE.search(line) and not key_line_allowed(path, line):
        out.append("private-key")
    if any(r.search(line) for r in TOKEN_RES):
        out.append("token-shape")
    if any(m.group(0) not in HOME_PLACEHOLDERS for m in HOME_RE.finditer(line)):
        out.append("home-path")
    for m in EMAIL_RE.finditer(line):
        dom = m.group(1).lower()
        if not email_domain_ok(dom):
            out.append("email")
            break
    for m in URL_RE.finditer(line):
        host = m.group(2).replace("\\.", ".").lower()
        if host and (m.group(1) == "http" or host not in URL_HOSTS):
            out.append("url-host")
            break
    for m in IP_RE.finditer(line):
        octets = [int(g) for g in m.groups()]
        if max(octets) <= 255 and not ip_is_ok(
                ipaddress.ip_address(".".join(map(str, octets)))):
            out.append("ip-literal")
            break
    return [(path, no, r) for r in out if (r, path, no) not in LINE_ALLOWED]


def workflow_findings(path, lines):
    out = []
    text = "\n".join(lines)
    if (not any(ln == "permissions:" for ln in lines)
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
    if uses_checkout and not any(WF_PERSIST_RE.match(ln) for ln in lines):
        out.append((path, 0, "workflow-persist-credentials"))
    return out


def content_findings(root, path):
    try:
        with open(os.path.join(root, path), "rb") as fh:
            raw = fh.read()
    except OSError:
        raise EnvError("tracked file unreadable")
    out = []
    if len(raw) > MAX_BYTES and path not in LARGE_FILES:
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


def _content(path, data):
    """content_findings on one file of a temporary directory."""
    base = tempfile.mkdtemp()
    try:
        full = os.path.join(base, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:
            fh.write(data)
        return [r for _, _, r in content_findings(base, path)]
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _hosts_file_matches():
    """ci/public-hosts.txt lists exactly URL_HOSTS, each with a one-line reason."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ci", "public-hosts.txt")
    try:
        with open(path, encoding="utf-8") as fh:
            rows = [ln.split("\t") for ln in fh.read().split("\n") if ln and not ln.startswith("#")]
    except OSError:
        return False
    return (sorted(r[0] for r in rows) == sorted(URL_HOSTS)
            and all(len(r) == 2 and r[1].strip() for r in rows))


def _allowance_controls():
    """Yield (name, passed): an allowed value is quiet, a near miss fires exactly its rule."""
    def rules(text, path="a.md", no=1):
        return [r for _, _, r in line_findings(path, no, text)]
    yield ("hosts-file-matches-table", _hosts_file_matches())
    for host in sorted(URL_HOSTS):
        yield ("host-allowed:" + host, rules("see https" + "://" + host + "/x") == [])
        yield ("host-prefix-miss:" + host, rules("see https" + "://evil-" + host + "/x") == ["url-host"])
        yield ("host-suffix-miss:" + host, rules("see https" + "://" + host + ".test/x") == ["url-host"])
        yield ("host-http-miss:" + host, rules("see http" + "://" + host + "/x") == ["url-host"])
    scheme = "https" + "://"
    yield ("url-escaped-dot-allowed", rules("re = r'" + scheme + "github" + "\\." + "com/x'") == [])
    yield ("url-escaped-dot-miss", rules("re = r'" + scheme + "evil" + "\\." + "test/x'") == ["url-host"])
    yield ("url-empty-host-allowed", rules("if u.startswith(\"" + scheme + "\"):") == [])
    yield ("url-empty-host-then-miss", rules("u.startswith(\"" + scheme + "\") or " + scheme + "evil.test/x") == ["url-host"])
    yield ("url-bare-token-miss", rules("see " + scheme + "x/y") == ["url-host"])
    yield ("url-userinfo-miss", "url-host" in rules("see " + scheme + "u" + "@evil.test/y"))
    for value in ("u@example.com", "u@example.io", "u@host.invalid", "u@a.b.invalid"):
        yield ("email-allowed:" + value.split("@")[1], rules("mail " + value) == [])
    for dom in ("sub.example.com", "example.com.test", "notexample.com", "invalid.test", "corp.invalidx"):
        yield ("email-miss:" + dom, rules("mail u" + "@" + dom) == ["email"])
    for value in ("127.0.0.1", "127.255.255.254", "192.0.2.1", "198.51.100.9", "203.0.113.5", "0.0.0.0"):
        yield ("ip-allowed:" + value, rules("at " + value) == [])
    for value in ("128.0.0." + "1", "126.255.255." + "255", "10.0.0." + "1", "192.0.3." + "1", "1.1.1." + "1",
                  "192.168.0." + "10", "172.30.1." + "20", "192.0.1." + "1", "198.51.101." + "1"):
        yield ("ip-miss:" + value, rules("at " + value) == ["ip-literal"])
    for value in ("/ho" + "me/example/x", "/Us" + "ers/example/x"):
        yield ("home-allowed:" + value[:4], rules("at " + value) == [])
    for value in ("/ho" + "me/examples/x", "/ho" + "me/example2/x", "/Us" + "ers/other/x", "/ho" + "me/x/example/"):
        yield ("home-miss:" + value[:4], rules("at " + value) == ["home-path"])
    # private-path: the artifact names only as the first component; the other private names at any depth
    for path in ("evidence/x.json", "artifacts/x.md", "scratch/x.md", "evidence/a/b/c.md"):
        yield ("path-root-artifact:" + path, path_findings(path) == [(path, 0, "private-path")])
    for path in ("src/pkg/evidence/x.py", "a/artifacts/b.py", "docs/scratch/n.md", "evidence.md", "evidences/x.md"):
        yield ("path-nested-artifact-allowed:" + path, path_findings(path) == [])
    for path in ("a/private/n.md", "a/.claude/x.md", "a/b/.venv/x.py", "a/node_modules/x.js", "a/__pycache__/m.py"):
        yield ("path-private-any-depth:" + path, path_findings(path) == [(path, 0, "private-path")])
    # too-large: an exact per-path list
    big = b"word\n" * 60000
    for path in sorted(LARGE_FILES):
        yield ("large-listed-quiet:" + path, "too-large" not in _content(path, big))
        yield ("large-other-path-fires:" + path, "too-large" in _content("other/" + path, big))
        yield ("large-sibling-fires:" + path, "too-large" in _content(path + ".copy", big))
    # private-key: exact path and pattern kind; a real-looking block fires everywhere else
    dashes = "-" * 5
    head = dashes + "BEG" + "IN RSA PRIV" + "ATE KEY" + dashes
    detector = "pat = re.compile(r'" + dashes + "BEG" + "IN [A-Z ]*PRIV" + "ATE KEY" + dashes + "')"
    sample = "x = '" + head + "\\nMIIB\\n" + dashes + "END RSA PRIV" + "ATE KEY" + dashes + "'"
    body = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC"
    for (path, kind), _ in sorted(PRIVATE_KEY_FILES.items()):
        line = detector if kind == "detector-regex" else sample
        other = sample if kind == "detector-regex" else detector
        yield ("key-listed-quiet:" + kind + ":" + path, rules(line, path) == [])
        yield ("key-other-path-fires:" + kind + ":" + path, rules(line, "x/" + path) == ["private-key"])
        yield ("key-other-kind-fires:" + kind + ":" + path, rules(other, path) == ["private-key"])
        yield ("key-plain-header-fires:" + kind + ":" + path, rules(head, path) == ["private-key"])
        yield ("key-real-body-fires:" + kind + ":" + path,
               rules(line.replace("MIIB", body).replace("re.compile(r'", "re.compile(r'" + body), path) == ["private-key"])
    yield ("key-anywhere-else-fires", rules(head, "src/other.py") == ["private-key"])
    yield ("key-sample-anywhere-else-fires", rules(sample, "tests/other.py") == ["private-key"])
    # LINE_ALLOWED: exact rule, path and line only (a synthetic entry; the committed entries use the same lookup)
    LINE_ALLOWED[("email", "t/a.py", 3)] = "control"
    try:
        yield ("line-allowed-exact", rules("mail u" + "@corp.test", "t/a.py", 3) == [])
        yield ("line-allowed-next-line-fires", rules("mail u" + "@corp.test", "t/a.py", 4) == ["email"])
        yield ("line-allowed-other-path-fires", rules("mail u" + "@corp.test", "t/b.py", 3) == ["email"])
        yield ("line-allowed-other-rule-fires", rules("mail u" + "@corp.test and 10." + "1.2.3", "t/a.py", 3) == ["ip-literal"])
    finally:
        del LINE_ALLOWED[("email", "t/a.py", 3)]


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
    for name, good in _allowance_controls():
        total += 1
        if good:
            passed += 1
        else:
            print(f"control failed: {name}")
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
