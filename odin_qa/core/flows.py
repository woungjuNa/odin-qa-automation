# -*- encoding=utf8 -*-
"""게임 화면을 다루는 재사용 플로우. 스모크 테스트는 이것을 검증하고, 다른 시나리오는 사전 조건으로 쓴다."""
from airtest.core.api import sleep, touch, wait
from airtest.core.error import TargetNotFoundError

from . import client
from .client import T
from .errors import TestFailure

SPLASH_LOGO = T("common/splash_logo")
CHARACTER_SELECT_TITLE = T("common/character_select_title")
PLAY_BUTTON = T("common/play_button")
INGAME_HUD = T("common/ingame_hud")          # 좌상단 "레벨" 라벨
INGAME_TOPMENU = T("common/ingame_topmenu")  # 우상단 메뉴 (BM 상점 아이콘 등)

# 단계별 대기 시간(초) / 재시도 횟수. 실패 메시지에도 이 값이 그대로 들어간다.
SPLASH_TIMEOUT = 15
SPLASH_CLICK_ATTEMPTS = 15
CHARACTER_SELECT_TIMEOUT = 30
PLAY_CLICK_ATTEMPTS = 20
INGAME_TIMEOUT = 60


def _wait_screen(template, timeout, screen_name):
    try:
        wait(template, timeout=timeout)
    except TargetNotFoundError:
        raise TestFailure(
            "verify",
            f"{screen_name} 화면이 {timeout}초 안에 나타나지 않았습니다. "
            f"오딘을 {screen_name} 화면 상태로 띄워두고 다시 실행해주세요.",
        )


def pass_splash(ctx):
    """스플래시 로고를 인식하고, 화면이 실제로 바뀔 때까지 반복 클릭한다.
    로딩 중에도 같은 로고가 보여 클릭이 씹히는 경우가 있어서 한 번만 누르지 않는다."""
    _wait_screen(SPLASH_LOGO, SPLASH_TIMEOUT, "스플래시")
    ctx.step("스플래시 화면 감지됨", screenshot=ctx.snap("01_splash"))

    for _ in range(SPLASH_CLICK_ATTEMPTS):
        if not client.visible(SPLASH_LOGO):
            break
        try:
            touch(SPLASH_LOGO)
        except TargetNotFoundError:
            break  # visible()과 touch() 사이에 화면이 이미 넘어간 경우 — 정상
        sleep(1)
    else:
        raise TestFailure("action", f"스플래시 화면을 {SPLASH_CLICK_ATTEMPTS}번 클릭했지만 다음 화면으로 넘어가지 않았습니다.")
    ctx.step("스플래시 통과 완료", screenshot=ctx.snap("02_splash_passed"))


def enter_game(ctx):
    """캐릭터 선택 화면에서 게임하기를 눌러 인게임(레벨 표시 + 상단 메뉴)까지 들어간다."""
    _wait_screen(CHARACTER_SELECT_TITLE, CHARACTER_SELECT_TIMEOUT, "캐릭터 선택")
    ctx.step("캐릭터 선택 화면 진입 확인됨", screenshot=ctx.snap("03_character_select"))

    for _ in range(PLAY_CLICK_ATTEMPTS):
        if not client.visible(CHARACTER_SELECT_TITLE):
            break
        try:
            touch(PLAY_BUTTON)
        except TargetNotFoundError:
            break
        sleep(0.4)
    else:
        raise TestFailure("action", f"게임하기 버튼을 {PLAY_CLICK_ATTEMPTS}번 눌렀지만 캐릭터 선택 화면을 벗어나지 못했습니다.")
    ctx.step("게임하기 클릭됨 (로딩 화면 진입 대기 중)", screenshot=ctx.snap("04_play_clicked"))

    client.wait_all([INGAME_HUD, INGAME_TOPMENU], INGAME_TIMEOUT, "인게임 화면(레벨 표시, 상단 메뉴)")


# --- 메뉴 시나리오용 ---

MENU_OPEN_TIMEOUT = 10
MENU_CLOSE_TIMEOUT = 10
RECOVER_ESC_ATTEMPTS = 3


def ensure_ingame(ctx):
    """인게임 상태를 보장한다. 이미 인게임이면 아무것도 하지 않고, 스플래시/캐릭터 선택 화면이면
    진입하고, 어느 화면도 아니면 사전 조건 실패로 처리한다. 진입 도중의 실패도 사전 조건 실패다 —
    이 시나리오가 검증하려는 것이 아니기 때문."""
    if client.all_visible(INGAME_HUD, INGAME_TOPMENU):
        ctx.step("이미 인게임 상태 — 진입 생략")
        return
    try:
        if client.visible(SPLASH_LOGO):
            ctx.step("스플래시 화면 감지 — 인게임까지 진입합니다")
            pass_splash(ctx)
            enter_game(ctx)
            return
        if client.visible(CHARACTER_SELECT_TITLE):
            ctx.step("캐릭터 선택 화면 감지 — 인게임까지 진입합니다")
            enter_game(ctx)
            return
    except TestFailure as e:
        raise TestFailure("precondition", f"인게임 진입 실패: {e}")
    raise TestFailure("precondition", "인게임/스플래시/캐릭터 선택 어느 화면도 아닙니다. 오딘 상태를 확인해주세요.")


def open_menu(ctx, key, label):
    """상단 아이콘(templates/top_menu/<key>_icon)을 눌러 메뉴 화면(<key>_opened)이 나타나는지 확인한다."""
    icon = T(f"top_menu/{key}_icon")
    opened = T(f"top_menu/{key}_opened")
    if not client.visible(icon):
        raise TestFailure("action", f"{label} 아이콘을 화면에서 찾지 못했습니다.")
    touch(icon)
    try:
        wait(opened, timeout=MENU_OPEN_TIMEOUT)
    except TargetNotFoundError:
        raise TestFailure("verify", f"{label} 아이콘을 눌렀지만 {MENU_OPEN_TIMEOUT}초 안에 {label} 화면이 나타나지 않았습니다.")
    ctx.step(f"[{label}] 메뉴 열림 확인", screenshot=ctx.snap(f"{key}_opened"))


def close_menu(ctx, label):
    """ESC로 메뉴를 닫고 인게임 HUD(레벨 표시 + 상단 메뉴)가 돌아오는지 확인한다."""
    client.press_esc()
    client.wait_all([INGAME_HUD, INGAME_TOPMENU], MENU_CLOSE_TIMEOUT, f"{label} 메뉴를 닫은 뒤 인게임 화면(레벨 표시, 상단 메뉴)")
    ctx.step(f"[{label}] 닫기 후 인게임 복귀 확인")


def recover_ingame(ctx):
    """항목 하나가 실패해 메뉴가 열린 채 남았을 때, 다음 항목이 연쇄로 실패하지 않도록 ESC로 복귀를
    시도한다. 최선의 노력일 뿐이라 예외를 내지 않는다."""
    for _ in range(RECOVER_ESC_ATTEMPTS):
        if client.all_visible(INGAME_HUD, INGAME_TOPMENU):
            return
        client.press_esc()
        sleep(1)
    if not client.all_visible(INGAME_HUD, INGAME_TOPMENU):
        ctx.step(f"ESC {RECOVER_ESC_ATTEMPTS}회로도 인게임 화면으로 복귀하지 못했습니다 — 이후 항목은 사전 조건이 깨진 상태로 실행됩니다")
