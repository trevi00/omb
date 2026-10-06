"""OMB-only: the deployment namespace, host settings and the protected list are configuration (D-E1-2, D-E2-4, D-E2-15).

The unit-name prefix, the target name, the polkit scope and the settings file names come from ONE namespace
(default `omb`); the data-transfer package protects no other project by default.
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "deploy" / "host" / "host_service.py"
TEMPLATES = ROOT / "deploy" / "host" / "systemd"
ROLE_SUFFIXES = ("fleet.service", "monitor-collect.service", "monitor-web.service", "inspect.service",
                 "inspect.timer", "managed-fleet.service", "owner-actions.service")

try:
    import fcntl  # noqa: F401
    import pwd  # noqa: F401
    LINUX = True
except ImportError:
    LINUX = False
linux_only = pytest.mark.skipif(not LINUX, reason="the host service tool is Linux-only")


def load_tool():
    spec = importlib.util.spec_from_file_location("host_service_namespace", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_args(tmp_path, **overrides):
    (tmp_path / "cfg.env").write_text("")
    (tmp_path / "sec.env").write_text("")
    values = dict(output=str(tmp_path / "units"), root="/opt/example", user="operator", group=None, uid=1500,
                  home="/home/operator", path="/usr/bin:/bin", python="/usr/bin/python3", tool=str(TOOL),
                  config_env=str(tmp_path / "cfg.env"), secret_env=str(tmp_path / "sec.env"), web_port=8787,
                  skip_account_check=True)
    values.update(overrides)
    return SimpleNamespace(**values)


def python_in(code, **env):
    """Run `code` in a fresh interpreter with the given environment settings (import-time configuration)."""
    environment = {k: v for k, v in os.environ.items() if k != "OMB_DEPLOY_NAMESPACE"}
    environment.update(env)
    environment["PYTHONPATH"] = os.pathsep.join([str(ROOT / "src"), str(ROOT / "scripts")])
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=environment, cwd=ROOT)


@linux_only
def test_default_namespace_is_omb_and_derives_every_unit_name():
    svc = load_tool()
    assert svc.DEFAULT_NAMESPACE == "omb"
    assert svc.UNITS == ("omb-fleet.service", "omb-monitor-collect.service", "omb-monitor-web.service",
                         "omb-inspect.service", "omb-inspect.timer", "omb.target", "omb-managed-fleet.service",
                         "omb-owner-actions.service")
    assert svc.ROLES["managed-fleet"] == "omb-managed-fleet.service"
    # the template files are named after the default namespace plus the role
    for unit in svc.UNITS:
        assert (TEMPLATES / (unit + ".in")).is_file()


@linux_only
def test_a_configured_namespace_derives_the_unit_names_from_the_same_role_suffixes():
    svc = load_tool()
    units = svc.unit_names("lab")
    assert units == tuple("lab-" + suffix if suffix else "lab.target"
                          for suffix in (*ROLE_SUFFIXES[:4], ROLE_SUFFIXES[4], None, *ROLE_SUFFIXES[5:]))
    assert svc.roles_of("lab")["fleet"] == "lab-fleet.service"
    assert svc.unit_name("target", "lab") == "lab.target"


@linux_only
@pytest.mark.parametrize("value", ["", "Lab", "1lab", "a b", "lab/x", "x" * 17, "lab.d"])
def test_an_invalid_namespace_is_refused(value):
    svc = load_tool()
    with pytest.raises(svc.Refused) as refusal:
        svc.namespace_of(value)
    assert refusal.value.reason == "namespace_invalid"


@linux_only
def test_render_installs_units_under_the_configured_namespace(tmp_path):
    svc = load_tool()
    manifest = svc.render(render_args(tmp_path, namespace="lab"))
    names = set(manifest["files"])
    assert names == set(svc.unit_names("lab")) | {"50-lab-managed-fleet.rules"}
    assert manifest["values"]["NAMESPACE"] == "lab"
    units = tmp_path / "units"
    for name in names:
        text = (units / name).read_text()
        assert not svc.PLACEHOLDER.search(text)
    target = (units / "lab.target").read_text()
    assert "lab-fleet.service" in target and "lab-monitor-web.service" in target
    fleet = svc.parse_unit((units / "lab-fleet.service").read_text())
    assert ("PartOf", "lab.target") in fleet["Unit"] and ("WantedBy", "lab.target") in fleet["Install"]
    assert ("Environment", "OMB_DEPLOY_NAMESPACE=lab") in fleet["Service"]
    assert 'action.lookup("unit") == "lab-managed-fleet.service"' in (units / "50-lab-managed-fleet.rules").read_text()
    # the units verify under their own namespace and are missing under the default one
    assert svc.verify(SimpleNamespace(directory=str(units), systemd_analyze=False, namespace="lab"))["findings"] == []
    missing = svc.verify(SimpleNamespace(directory=str(units), systemd_analyze=False))["findings"]
    assert {f["code"] for f in missing} == {"unit_missing"}


@linux_only
def test_render_without_a_namespace_uses_the_default(tmp_path):
    svc = load_tool()
    manifest = svc.render(render_args(tmp_path))
    assert set(manifest["files"]) == set(svc.UNITS) | {"50-omb-managed-fleet.rules"}
    assert manifest["values"]["NAMESPACE"] == "omb"
    assert manifest["values"]["CONFIG_ENV"] == str(tmp_path / "cfg.env")
    assert svc.render_values(render_args(tmp_path, config_env=None, secret_env=None, tool=None))["TOOL"] \
        == "/opt/example/deploy/host/host_service.py"


@linux_only
def test_the_settings_files_and_the_lifecycle_journal_follow_the_namespace(tmp_path):
    svc = load_tool()
    values = svc.render_values(render_args(tmp_path, namespace="lab", config_env=None, secret_env=None))
    assert values["CONFIG_ENV"] == "/opt/example/config/lab.env"
    assert values["SECRET_ENV"] == "/opt/example/secrets/lab.env"
    environ = {"INVOCATION_ID": "0" * 32, "OMB_DEPLOY_NAMESPACE": "lab"}
    assert svc.journal_entry("start", "managed-fleet", environ)["unit"] == "lab-managed-fleet.service"
    assert svc.journal_entry("start", "managed-fleet", {"INVOCATION_ID": "0" * 32})["unit"] == "omb-managed-fleet.service"


@linux_only
def test_the_fleet_owner_record_names_the_unit_of_the_configured_namespace(tmp_path):
    svc = load_tool()
    record = {"schema": svc.FLEET_OWNER_SCHEMA, "owner": "managed-fleet", "unit": "lab-managed-fleet.service"}
    (tmp_path / svc.FLEET_OWNER_FILE).write_text(json.dumps(record))
    assert svc.fleet_owner(tmp_path, "lab") == "managed-fleet"
    with pytest.raises(svc.Refused) as refusal:
        svc.fleet_owner(tmp_path)  # the default namespace does not accept another namespace's unit
    assert refusal.value.reason == "fleet_owner_invalid"


@linux_only
def test_render_and_inspect_need_an_explicit_host_root():
    svc = load_tool()
    parser = svc.parser()
    for argv in (["render", "--output", "/tmp/x", "--user", "operator", "--uid", "1500", "--home", "/home/operator"],
                 ["inspect"]):
        with pytest.raises(SystemExit):
            parser.parse_args(argv)
    assert parser.parse_args(["inspect", "--root", "/opt/example"]).namespace == "omb"


def test_the_managed_unit_constant_is_the_neutral_default():
    result = python_in("from codex_harness.delivery.domain import host_delivery as d; print(d.MANAGED_SYSTEMD_UNIT)")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "omb-managed-fleet"


def test_the_live_name_is_derived_from_the_configured_namespace():
    code = ("from codex_harness.delivery.domain import host_delivery as d\n"
            "from codex_harness.delivery.adapters import host_migration as m\n"
            "print(d.MANAGED_SYSTEMD_UNIT, m.SWITCH_UNITS, bool(m.UNIT.fullmatch('lab-fleet')), "
            "bool(m.UNIT.fullmatch('omb-fleet')))")
    result = python_in(code, OMB_DEPLOY_NAMESPACE="lab")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ("lab-managed-fleet ('lab-fleet.service', 'lab-managed-fleet.service', "
                                     "'lab-host-delivery.service') True False")


def test_an_invalid_namespace_setting_refuses_to_load_the_policy():
    result = python_in("from codex_harness.delivery.domain import host_delivery", OMB_DEPLOY_NAMESPACE="Not Valid")
    assert result.returncode != 0 and "deploy_namespace_invalid" in result.stderr


def test_the_default_protected_list_names_no_other_project(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    monkeypatch.delenv("OMB_HOST_DATA_PROTECTED", raising=False)
    from host_data import gates
    assert gates.protected_markers({}) == gates.PROTECTED
    assert gates.protected_markers() == gates.PROTECTED
    assert not gates._protected("/data/example-project/runtime")
    assert gates._protected("/home/example/.claude/settings")  # user configuration stays protected


def test_a_configured_protected_list_is_honoured(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from host_data import gates
    configured = {"OMB_HOST_DATA_PROTECTED": "example-project, example-db ,"}
    assert gates.protected_markers(configured) == gates.PROTECTED + ("example-project", "example-db")
    monkeypatch.setenv("OMB_HOST_DATA_PROTECTED", "example-project")
    assert gates._protected("/data/example-project/runtime")
    assert not gates._protected("/data/another/runtime")


def test_the_monitored_services_name_no_other_project_by_default(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "src"))
    monkeypatch.delenv("OMB_DEPLOY_MONITORED_SERVICES", raising=False)
    from codex_harness.delivery.adapters import deployment
    assert deployment.monitored_services({}) == frozenset(deployment.MONITORED_SERVICES)
    assert deployment.monitored_services() == frozenset(deployment.MONITORED_SERVICES)
    configured = deployment.monitored_services({"OMB_DEPLOY_MONITORED_SERVICES": "example-worker, ,other"})
    assert configured == frozenset(deployment.MONITORED_SERVICES) | {"example-worker", "other"}
