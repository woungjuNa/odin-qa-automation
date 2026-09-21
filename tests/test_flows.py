import pytest
from airtest.core.error import TargetNotFoundError

from core import context, errors, flows


@pytest.fixture
def ctx(monkeypatch):
    monkeypatch.setattr(context.client, "snap", lambda name: None)
    return context.Context("t", "테스트")


@pytest.fixture
def screen(monkeypatch):
    """화면에 보이는 템플릿 집합을 흉내 낸다. touch/wait/sleep은 게임 없이 동작하도록 바꾼다."""
    state = {"visible": set(), "touched": []}
    monkeypatch.setattr(flows.client, "visible", lambda t: t in state["visible"])
    monkeypatch.setattr(flows.client, "all_visible", lambda *ts: all(t in state["visible"] for t in ts))
    monkeypatch.setattr(flows, "sleep", lambda s: None)

    def fake_wait(t, timeout):
        if t not in state["visible"]:
            raise TargetNotFoundError("not found")
    monkeypatch.setattr(flows, "wait", fake_wait)
    monkeypatch.setattr(flows, "touch", lambda t: state["touched"].append(t))
    return state


def test_pass_splash_clicks_until_logo_gone(ctx, screen, monkeypatch):
    screen["visible"].add(flows.SPLASH_LOGO)
    clicks = []

    def touch_then_advance(t):
        clicks.append(t)
        if len(clicks) == 3:
            screen["visible"].discard(flows.SPLASH_LOGO)
    monkeypatch.setattr(flows, "touch", touch_then_advance)

    flows.pass_splash(ctx)
    assert len(clicks) == 3
    assert ctx.reporter.steps[-1]["name"] == "스플래시 통과 완료"


def test_pass_splash_fails_verify_when_logo_never_appears(ctx, screen):
    with pytest.raises(errors.TestFailure) as info:
        flows.pass_splash(ctx)
    assert info.value.stage == "verify"
    assert "스플래시 화면이" in str(info.value)


def test_pass_splash_fails_action_when_clicks_do_nothing(ctx, screen):
    screen["visible"].add(flows.SPLASH_LOGO)
    with pytest.raises(errors.TestFailure) as info:
        flows.pass_splash(ctx)
    assert info.value.stage == "action"
    assert f"{flows.SPLASH_CLICK_ATTEMPTS}번" in str(info.value)


def test_enter_game_reaches_ingame(ctx, screen, monkeypatch):
    screen["visible"].add(flows.CHARACTER_SELECT_TITLE)

    def touch_play(t):
        screen["visible"].discard(flows.CHARACTER_SELECT_TITLE)
        screen["visible"].update({flows.INGAME_HUD, flows.INGAME_TOPMENU})
    monkeypatch.setattr(flows, "touch", touch_play)

    def fake_wait_all(templates, timeout, description):
        if not all(t in screen["visible"] for t in templates):
            raise errors.TestFailure("verify", description)
    monkeypatch.setattr(flows.client, "wait_all", fake_wait_all)

    flows.enter_game(ctx)
    names = [s["name"] for s in ctx.reporter.steps]
    assert "캐릭터 선택 화면 진입 확인됨" in names
    assert "게임하기 클릭됨 (로딩 화면 진입 대기 중)" in names


def test_enter_game_fails_action_when_stuck_on_character_select(ctx, screen):
    screen["visible"].add(flows.CHARACTER_SELECT_TITLE)
    with pytest.raises(errors.TestFailure) as info:
        flows.enter_game(ctx)
    assert info.value.stage == "action"
    assert f"{flows.PLAY_CLICK_ATTEMPTS}번" in str(info.value)
