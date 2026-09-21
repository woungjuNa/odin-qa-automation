import types

import pytest

import run
from core import context, errors


def scenario(name, body):
    mod = types.ModuleType(name)
    mod.NAME, mod.TITLE, mod.run = name, f"{name} 제목", body
    return mod


@pytest.fixture
def harness(monkeypatch, tmp_path):
    calls = {"connect": 0, "sent": []}
    monkeypatch.setattr(run.client, "connect", lambda: calls.__setitem__("connect", calls["connect"] + 1))
    monkeypatch.setattr(run.client, "LOG_DIR", str(tmp_path))
    monkeypatch.setattr(run.sheets, "send", lambda ctx: calls["sent"].append((ctx.name, ctx.passed, ctx.failure_stage())))
    monkeypatch.setattr(context.client, "snap", lambda name: None)
    return calls


def test_runs_selected_scenarios_in_order(harness, monkeypatch):
    order = []
    monkeypatch.setattr(run, "SCENARIOS", {
        "smoke": scenario("smoke", lambda ctx: order.append("smoke")),
        "top_menu": scenario("top_menu", lambda ctx: order.append("top_menu")),
    })
    assert run.main(["smoke", "top_menu"]) == 0
    assert order == ["smoke", "top_menu"]
    assert harness["connect"] == 1
    assert harness["sent"] == [("smoke", True, ""), ("top_menu", True, "")]


def test_failed_smoke_blocks_later_scenarios(harness, monkeypatch):
    ran = []

    def failing_smoke(ctx):
        raise errors.TestFailure("verify", "스플래시 화면이 나타나지 않았습니다.")
    monkeypatch.setattr(run, "SCENARIOS", {
        "smoke": scenario("smoke", failing_smoke),
        "top_menu": scenario("top_menu", lambda ctx: ran.append("top_menu")),
    })
    assert run.main(["smoke", "top_menu"]) == 1
    assert ran == []
    assert harness["sent"] == [("smoke", False, "verify"), ("top_menu", False, "precondition")]


def test_connect_failure_marks_every_scenario_setup_failed(harness, monkeypatch):
    def bad_connect():
        raise errors.TestFailure("setup", "오딘 창이 2개 열려 있습니다.")
    monkeypatch.setattr(run.client, "connect", bad_connect)
    monkeypatch.setattr(run, "SCENARIOS", {"smoke": scenario("smoke", lambda ctx: None)})
    assert run.main(["smoke"]) == 1
    assert harness["sent"] == [("smoke", False, "setup")]


def test_unknown_scenario_name_is_rejected(monkeypatch):
    monkeypatch.setattr(run, "SCENARIOS", {"smoke": scenario("smoke", lambda ctx: None)})
    with pytest.raises(SystemExit):
        run.parse_names(["nope"])


def test_all_expands_to_every_scenario(monkeypatch):
    monkeypatch.setattr(run, "SCENARIOS", {"smoke": None, "top_menu": None})
    assert run.parse_names(["all"]) == ["smoke", "top_menu"]
    assert run.parse_names(["top_menu"]) == ["top_menu"]


def test_registered_scenarios_and_order():
    assert list(run.SCENARIOS) == ["smoke", "top_menu"]
    for mod in run.SCENARIOS.values():
        assert callable(mod.run) and mod.TITLE
