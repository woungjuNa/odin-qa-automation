import sys
import types

import pytest

from core import context, errors, sheets


class FakeResponse:
    def __init__(self, json_body=None, text="", status=200):
        self._json = json_body
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        if self._json is None:
            raise ValueError("not json")
        return self._json


@pytest.fixture
def ctx(monkeypatch):
    monkeypatch.setattr(context.client, "snap", lambda name: None)
    return context.Context("top_menu", "상단 메뉴")


@pytest.fixture
def config(monkeypatch):
    cfg = types.ModuleType("sheets_config")
    cfg.WEBHOOK_URL = "http://example.test/exec"
    cfg.WEBHOOK_TOKEN = "secret"
    monkeypatch.setitem(sys.modules, "sheets_config", cfg)
    return cfg


def test_send_skips_without_config(monkeypatch, ctx):
    monkeypatch.setitem(sys.modules, "sheets_config", None)  # import 시 ImportError
    called = []
    monkeypatch.setattr(sheets.requests, "post", lambda *a, **k: called.append(1))
    sheets.send(ctx)
    assert called == []


def test_send_payload_has_scenario_and_stage(monkeypatch, ctx, config):
    sent = {}
    monkeypatch.setattr(
        sheets.requests, "post",
        lambda url, json, timeout: sent.update(url=url, json=json) or FakeResponse({"status": "ok"}),
    )
    with ctx.case("선물"):
        raise errors.TestFailure("verify", "메뉴 화면이 나타나지 않았습니다.")
    sheets.send(ctx)
    payload = sent["json"]
    assert sent["url"] == "http://example.test/exec"
    assert payload["scenario"] == "top_menu"
    assert payload["result"] == "FAIL"
    assert payload["stage"] == "화면 확인"
    assert payload["error"] == "선물: 메뉴 화면이 나타나지 않았습니다."
    assert payload["token"] == "secret"
    assert set(payload) == {"timestamp", "scenario", "result", "duration", "stage", "error", "token"}


def test_send_pass_has_empty_stage(monkeypatch, ctx, config):
    sent = {}
    monkeypatch.setattr(
        sheets.requests, "post",
        lambda url, json, timeout: sent.update(json=json) or FakeResponse({"status": "ok"}),
    )
    sheets.send(ctx)
    assert sent["json"]["result"] == "PASS"
    assert sent["json"]["stage"] == ""
    assert sent["json"]["error"] == ""


def test_send_reports_non_json_response(monkeypatch, ctx, config, capsys):
    monkeypatch.setattr(
        sheets.requests, "post",
        lambda url, json, timeout: FakeResponse(None, text="<html>Sign in</html>"),
    )
    sheets.send(ctx)  # 예외를 밖으로 내지 않는다
    assert "JSON이 아닌 응답" in capsys.readouterr().out


def test_send_reports_error_status(monkeypatch, ctx, config, capsys):
    monkeypatch.setattr(
        sheets.requests, "post",
        lambda url, json, timeout: FakeResponse({"status": "error", "message": "invalid token"}),
    )
    sheets.send(ctx)
    assert "invalid token" in capsys.readouterr().out
