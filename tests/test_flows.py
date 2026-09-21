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


# --- ensure_ingame ---

def test_ensure_ingame_skips_when_already_ingame(ctx, screen, monkeypatch):
    screen["visible"].update({flows.INGAME_HUD, flows.INGAME_TOPMENU})
    monkeypatch.setattr(flows, "pass_splash", lambda c: pytest.fail("진입하면 안 됨"))
    flows.ensure_ingame(ctx)
    assert ctx.reporter.steps[-1]["name"] == "이미 인게임 상태 — 진입 생략"


def test_ensure_ingame_enters_from_splash(ctx, screen, monkeypatch):
    screen["visible"].add(flows.SPLASH_LOGO)
    called = []
    monkeypatch.setattr(flows, "pass_splash", lambda c: called.append("splash"))
    monkeypatch.setattr(flows, "enter_game", lambda c: called.append("enter"))
    flows.ensure_ingame(ctx)
    assert called == ["splash", "enter"]


def test_ensure_ingame_enters_from_character_select(ctx, screen, monkeypatch):
    screen["visible"].add(flows.CHARACTER_SELECT_TITLE)
    called = []
    monkeypatch.setattr(flows, "pass_splash", lambda c: called.append("splash"))
    monkeypatch.setattr(flows, "enter_game", lambda c: called.append("enter"))
    flows.ensure_ingame(ctx)
    assert called == ["enter"]


def test_ensure_ingame_wraps_entry_failure_as_precondition(ctx, screen, monkeypatch):
    screen["visible"].add(flows.SPLASH_LOGO)

    def failing_splash(c):
        raise errors.TestFailure("action", "클릭 실패")
    monkeypatch.setattr(flows, "pass_splash", failing_splash)
    with pytest.raises(errors.TestFailure) as info:
        flows.ensure_ingame(ctx)
    assert info.value.stage == "precondition"
    assert "인게임 진입 실패: 클릭 실패" in str(info.value)


def test_ensure_ingame_fails_on_unknown_screen(ctx, screen):
    with pytest.raises(errors.TestFailure) as info:
        flows.ensure_ingame(ctx)
    assert info.value.stage == "precondition"


# --- open_menu / close_menu / recover_ingame ---

@pytest.fixture
def menu_templates(monkeypatch):
    """T("top_menu/x_icon") 같은 호출이 같은 키에 대해 같은 객체를 돌려주도록 한다."""
    cache = {}
    monkeypatch.setattr(flows, "T", lambda name: cache.setdefault(name, object()))
    return cache


def test_open_menu_fails_action_when_icon_missing(ctx, screen, menu_templates):
    with pytest.raises(errors.TestFailure) as info:
        flows.open_menu(ctx, "gift", "선물")
    assert info.value.stage == "action"
    assert "선물 아이콘" in str(info.value)


def test_open_menu_fails_verify_when_screen_does_not_open(ctx, screen, menu_templates):
    icon = flows.T("top_menu/gift_icon")
    screen["visible"].add(icon)
    with pytest.raises(errors.TestFailure) as info:
        flows.open_menu(ctx, "gift", "선물")
    assert info.value.stage == "verify"
    assert screen["touched"] == [icon]


def test_open_menu_passes_when_opened_template_appears(ctx, screen, menu_templates):
    icon, opened = flows.T("top_menu/gift_icon"), flows.T("top_menu/gift_opened")
    screen["visible"].update({icon, opened})
    flows.open_menu(ctx, "gift", "선물")
    assert ctx.reporter.steps[-1]["name"] == "[선물] 메뉴 열림 확인"


def test_close_menu_presses_esc_then_waits_for_menu_gone_and_hud(ctx, screen, menu_templates, monkeypatch):
    calls = []
    monkeypatch.setattr(flows.client, "press_esc", lambda: calls.append("esc"))
    monkeypatch.setattr(flows.client, "wait_gone", lambda t, timeout, d: calls.append(("gone", t, timeout)))
    monkeypatch.setattr(flows.client, "wait_all", lambda ts, timeout, d: calls.append(("hud", tuple(ts), timeout)))
    flows.close_menu(ctx, "gift", "선물")
    assert calls == [
        "esc",
        ("gone", flows.T("top_menu/gift_opened"), flows.MENU_CLOSE_TIMEOUT),
        ("hud", (flows.INGAME_HUD, flows.INGAME_TOPMENU), flows.MENU_CLOSE_TIMEOUT),
    ]
    assert ctx.reporter.steps[-1]["name"] == "[선물] 닫기 후 인게임 복귀 확인"


def test_close_menu_fails_verify_when_menu_stays_open(ctx, screen, menu_templates, monkeypatch):
    monkeypatch.setattr(flows.client, "press_esc", lambda: None)
    monkeypatch.setattr(flows, "sleep", lambda s: None)
    monkeypatch.setattr(flows.client, "sleep", lambda s: None)
    monkeypatch.setattr(flows.client, "wait_all", lambda ts, timeout, d: None)
    monkeypatch.setattr(flows, "MENU_CLOSE_TIMEOUT", 0.01)
    opened = flows.T("top_menu/gift_opened")
    screen["visible"].add(opened)
    monkeypatch.setattr(flows.client, "visible", lambda t: t in screen["visible"])
    with pytest.raises(errors.TestFailure) as info:
        flows.close_menu(ctx, "gift", "선물")
    assert info.value.stage == "verify"
    assert "닫히지 않았습니다" in str(info.value)


def test_recover_ingame_presses_esc_until_hud_returns(ctx, screen, monkeypatch):
    presses = []

    def esc():
        presses.append(1)
        if len(presses) == 2:
            screen["visible"].update({flows.INGAME_HUD, flows.INGAME_TOPMENU})
    monkeypatch.setattr(flows.client, "press_esc", esc)
    flows.recover_ingame(ctx)
    assert len(presses) == 2


def test_recover_ingame_gives_up_after_three_and_does_not_raise(ctx, screen, monkeypatch):
    presses = []
    monkeypatch.setattr(flows.client, "press_esc", lambda: presses.append(1))
    flows.recover_ingame(ctx)
    assert len(presses) == 3
    assert "복귀하지 못했습니다" in ctx.reporter.steps[-1]["name"]
