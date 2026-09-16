# -*- encoding=utf8 -*-
import os
import re
import time

import win32con
import win32gui

from airtest.core.api import *
from report import Reporter

WINDOW_TITLE_RE = r"ODIN"

SPLASH_LOGO = Template(r"splash_logo.png")
CHARACTER_SELECT_TITLE = Template(r"character_select_title.png")
PLAY_BUTTON = Template(r"play_button.png")
INGAME_HUD = Template(r"ingame_hud.png")
INGAME_TOPMENU = Template(r"ingame_topmenu.png")

reporter = Reporter("오딘 스모크 테스트: 실행 → 스플래시 통과 → 캐릭터 선택 → 인게임 진입")


def run_smoke_test():
    auto_setup(__file__, logdir=True)
    connect_device(f"Windows:///?title_re={WINDOW_TITLE_RE}")
    reporter.step("오딘 창에 연결됨")

    wait(SPLASH_LOGO, timeout=15)
    reporter.step("스플래시 화면 감지됨", screenshot=_snap("01_splash"))

    for attempt in range(15):
        if not exists(SPLASH_LOGO):
            break
        touch(SPLASH_LOGO)
        sleep(1)
    else:
        raise TargetNotFoundError("스플래시 화면을 15번 클릭했지만 다음 화면으로 넘어가지 않음")
    reporter.step("스플래시 통과 완료", screenshot=_snap("02_splash_passed"))

    wait(CHARACTER_SELECT_TITLE, timeout=30)
    reporter.step("캐릭터 선택 화면 진입 확인됨", screenshot=_snap("03_character_select"))

    for attempt in range(10):
        if not exists(CHARACTER_SELECT_TITLE):
            break
        touch(PLAY_BUTTON)
        sleep(1)
    else:
        raise TargetNotFoundError("게임하기 버튼을 10번 눌렀지만 캐릭터 선택 화면을 벗어나지 못함")
    reporter.step("게임하기 클릭됨 (로딩 화면 진입 대기 중)", screenshot=_snap("04_play_clicked"))

    _wait_all([INGAME_HUD, INGAME_TOPMENU], timeout=60)
    reporter.step(
        "인게임 진입 확인됨 (AUTO 버튼 + 상단 메뉴 아이콘 모두 확인)",
        status="pass",
        screenshot=_snap("05_ingame"),
    )


def _wait_all(templates, timeout):
    """여러 템플릿이 모두 화면에 나타날 때까지 기다린다 (둘 다 있어야 통과, 오탐 방지용)."""
    start = time.time()
    while time.time() - start < timeout:
        if all(exists(t) for t in templates):
            return
        sleep(0.5)
    raise TargetNotFoundError(f"{timeout}초 안에 모든 템플릿이 동시에 발견되지 않음")


def _bring_odin_to_front():
    """다른 창에 가려진 채로 스크린샷이 찍히지 않도록, 오딘 창을 맨 앞으로 가져온다."""
    def _find(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and re.search(WINDOW_TITLE_RE, win32gui.GetWindowText(hwnd)):
            hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(_find, hwnds)
    if not hwnds:
        return
    hwnd = hwnds[0]
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    sleep(0.3)


def _snap(name):
    """오딘 창을 맨 앞으로 가져온 뒤, 스크린샷을 log 폴더에 저장하고 파일명을 돌려준다."""
    _bring_odin_to_front()
    filename = f"{name}.png"
    snapshot(filename=filename)
    return filename


if __name__ == "__main__":
    passed = False
    try:
        run_smoke_test()
        passed = True
    except Exception as e:
        reporter.step(f"스모크 테스트 실패: {e}", status="fail", screenshot=_snap("99_failure"))
        raise
    finally:
        log_dir = os.path.join(os.path.dirname(__file__), "log")
        os.makedirs(log_dir, exist_ok=True)
        reporter.render(os.path.join(log_dir, "report.html"), passed)
        print(f"[REPORT] {os.path.join(log_dir, 'report.html')}")
