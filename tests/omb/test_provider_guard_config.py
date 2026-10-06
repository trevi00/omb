"""OMB-only: the provider guard's secrets directory is configuration with a neutral default (D-E2-4)."""

import importlib.util
from pathlib import Path

GUARD = Path(__file__).resolve().parents[1] / "_zeus_compare" / "guard" / "provider_guard.py"


def load(name):
    spec = importlib.util.spec_from_file_location(name, GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_secrets_dir_is_neutral(monkeypatch):
    monkeypatch.delenv("OMB_SECRETS_DIR", raising=False)
    guard = load("provider_guard_default")
    assert guard.CREDENTIAL_DIRS[0] == "~/.omb/secrets"
    assert guard.CREDENTIAL_DIRS[0].startswith("~/")


def test_configured_secrets_dir_is_guarded(monkeypatch):
    monkeypatch.setenv("OMB_SECRETS_DIR", "/example/secrets")
    guard = load("provider_guard_configured")
    assert guard.CREDENTIAL_DIRS[0] == "/example/secrets"
    assert "~/.ssh" in guard.CREDENTIAL_DIRS


def test_empty_setting_falls_back_to_the_default(monkeypatch):
    monkeypatch.setenv("OMB_SECRETS_DIR", "")
    assert load("provider_guard_empty").CREDENTIAL_DIRS[0] == "~/.omb/secrets"
