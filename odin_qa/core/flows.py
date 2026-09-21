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
