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


def _wait_named(template, timeout, step_name):
    """wait()를 감싸서, 실패 시 Airtest 원문 대신 한글로 어떤 단계에서 실패했는지 알려준다.
    일반 Exception을 쓰는 이유: TargetNotFoundError는 메시지를 따옴표로 감싸서 출력하기 때문."""
    try:
        wait(template, timeout=timeout)
    except TargetNotFoundError:
        raise Exception(
            f"{step_name} 화면이 {timeout}초 안에 나타나지 않았습니다. "
            f"오딘을 {step_name} 화면 상태로 띄워두고 다시 실행해주세요."
        )


def run_smoke_test():
    auto_setup(__file__, logdir=True)
    connect_device(f"Windows:///?title_re={WINDOW_TITLE_RE}")
    reporter.step("오딘 창에 연결됨")

    _wait_named(SPLASH_LOGO, 15, "스플래시")
    reporter.step("스플래시 화면 감지됨", screenshot=_snap("01_splash"))

    for attempt in range(15):
        if not exists(SPLASH_LOGO):
            break
        try:
            touch(SPLASH_LOGO)
        except TargetNotFoundError:
            break  # exists()와 touch() 사이에 화면이 이미 넘어간 경우 — 정상
        sleep(1)
    else:
        raise Exception("스플래시 화면을 15번 클릭했지만 다음 화면으로 넘어가지 않았습니다.")
    reporter.step("스플래시 통과 완료", screenshot=_snap("02_splash_passed"))

    _wait_named(CHARACTER_SELECT_TITLE, 30, "캐릭터 선택")
    reporter.step("캐릭터 선택 화면 진입 확인됨", screenshot=_snap("03_character_select"))

    for attempt in range(10):
        if not exists(CHARACTER_SELECT_TITLE):
            break
        try:
            touch(PLAY_BUTTON)
        except TargetNotFoundError:
            break
        sleep(1)
    else:
        raise Exception("게임하기 버튼을 10번 눌렀지만 캐릭터 선택 화면을 벗어나지 못했습니다.")
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
    raise Exception(f"인게임 화면(AUTO 버튼, 상단 메뉴)이 {timeout}초 안에 모두 나타나지 않았습니다.")


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


def _send_to_sheet(passed, error_message=""):
    """sheets_config.py가 있으면, 실행 결과 한 줄을 Google Sheets 웹훅으로 전송한다.
    설정 파일이 없거나 전송이 실패해도 테스트 자체는 실패시키지 않는다."""
    try:
        from sheets_config import WEBHOOK_URL
    except ImportError:
        return
    import datetime as _dt
    import requests

    duration = (_dt.datetime.now() - reporter.started_at).total_seconds()
    payload = {
        "timestamp": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": "PASS" if passed else "FAIL",
        "duration": round(duration, 1),
        "error": error_message,
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print("[SHEET] Google Sheets에 결과 전송 완료")
    except Exception as e:
        print(f"[SHEET] Google Sheets 전송 실패 (무시하고 계속): {e}")


if __name__ == "__main__":
    passed = False
    error_message = ""
    try:
        run_smoke_test()
        passed = True
    except Exception as e:
        error_message = str(e)
        reporter.step(f"스모크 테스트 실패: {e}", status="fail", screenshot=_snap("99_failure"))
        raise
    finally:
        log_dir = os.path.join(os.path.dirname(__file__), "log")
        os.makedirs(log_dir, exist_ok=True)
        reporter.render(os.path.join(log_dir, "report.html"), passed)
        print(f"[REPORT] {os.path.join(log_dir, 'report.html')}")
        _send_to_sheet(passed, error_message)
