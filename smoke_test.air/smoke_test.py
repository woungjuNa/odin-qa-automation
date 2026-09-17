# -*- encoding=utf8 -*-
import os
import re
import time

import win32con
import win32gui

from airtest.core.api import *
from report import Reporter

WINDOW_TITLE_RE = r"ODIN"
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")

# 단계별 대기 시간(초) / 재시도 횟수. 실패 메시지에도 이 값이 그대로 들어간다.
SPLASH_TIMEOUT = 15
SPLASH_CLICK_ATTEMPTS = 15
CHARACTER_SELECT_TIMEOUT = 30
PLAY_CLICK_ATTEMPTS = 20
INGAME_TIMEOUT = 60

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


def _clear_log_dir():
    """이전 실행에서 쌓인 로그(특히 Airtest가 매 동작마다 자동으로 남기는 타임스탬프
    jpg 파일들)를 지우고 새로 시작한다. 안 지우면 실행할수록 용량이 계속 늘어난다."""
    if os.path.isdir(LOG_DIR):
        for name in os.listdir(LOG_DIR):
            path = os.path.join(LOG_DIR, name)
            if os.path.isfile(path):
                os.remove(path)
    os.makedirs(LOG_DIR, exist_ok=True)


def _find_odin_windows():
    """제목이 WINDOW_TITLE_RE에 맞는, 화면에 보이는 최상위 창 핸들 목록."""
    def _collect(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and re.search(WINDOW_TITLE_RE, win32gui.GetWindowText(hwnd)):
            hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(_collect, hwnds)
    return hwnds


def _check_single_odin_window():
    """오딘 창이 정확히 하나일 때만 진행한다. 클라이언트가 중복 실행되면 pywinauto가
    ElementAmbiguousError를 내는데, 그 원문보다 어떤 상태인지 바로 알려주는 편이 낫다."""
    count = len(_find_odin_windows())
    if count == 0:
        raise Exception("오딘 창을 찾을 수 없습니다. 오딘을 실행해 스플래시 화면 상태로 띄워두고 다시 실행해주세요.")
    if count > 1:
        raise Exception(
            f"오딘 창이 {count}개 열려 있습니다. 클라이언트가 중복 실행된 상태이니 "
            f"하나만 남기고 다시 실행해주세요."
        )


def run_smoke_test():
    _clear_log_dir()
    auto_setup(__file__, logdir=True)
    _check_single_odin_window()
    connect_device(f"Windows:///?title_re={WINDOW_TITLE_RE}")
    reporter.step("오딘 창에 연결됨")

    _wait_named(SPLASH_LOGO, SPLASH_TIMEOUT, "스플래시")
    reporter.step("스플래시 화면 감지됨", screenshot=_snap("01_splash"))

    for attempt in range(SPLASH_CLICK_ATTEMPTS):
        if not exists(SPLASH_LOGO):
            break
        try:
            touch(SPLASH_LOGO)
        except TargetNotFoundError:
            break  # exists()와 touch() 사이에 화면이 이미 넘어간 경우 — 정상
        sleep(1)
    else:
        raise Exception(
            f"스플래시 화면을 {SPLASH_CLICK_ATTEMPTS}번 클릭했지만 다음 화면으로 넘어가지 않았습니다."
        )
    reporter.step("스플래시 통과 완료", screenshot=_snap("02_splash_passed"))

    _wait_named(CHARACTER_SELECT_TITLE, CHARACTER_SELECT_TIMEOUT, "캐릭터 선택")
    reporter.step("캐릭터 선택 화면 진입 확인됨", screenshot=_snap("03_character_select"))

    for attempt in range(PLAY_CLICK_ATTEMPTS):
        if not exists(CHARACTER_SELECT_TITLE):
            break
        try:
            touch(PLAY_BUTTON)
        except TargetNotFoundError:
            break
        sleep(0.4)
    else:
        raise Exception(
            f"게임하기 버튼을 {PLAY_CLICK_ATTEMPTS}번 눌렀지만 캐릭터 선택 화면을 벗어나지 못했습니다."
        )
    reporter.step("게임하기 클릭됨 (로딩 화면 진입 대기 중)", screenshot=_snap("04_play_clicked"))

    _wait_all([INGAME_HUD, INGAME_TOPMENU], timeout=INGAME_TIMEOUT)
    reporter.step(
        "인게임 진입 확인됨 (레벨 표시 + 상단 메뉴 아이콘 모두 확인)",
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
    raise Exception(f"인게임 화면(레벨 표시, 상단 메뉴)이 {timeout}초 안에 모두 나타나지 않았습니다.")


def _bring_odin_to_front():
    """다른 창에 가려진 채로 스크린샷이 찍히지 않도록, 오딘 창을 맨 앞으로 가져온다."""
    hwnds = _find_odin_windows()
    if not hwnds:
        return
    hwnd = hwnds[0]
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass  # Windows가 포커스 전환을 거부할 때가 있음 — 실패해도 스크린샷 자체는 계속 시도
    sleep(0.3)


def _snap(name):
    """오딘 창을 맨 앞으로 가져온 뒤, 스크린샷을 log 폴더에 저장하고 파일명을 돌려준다.
    연결 자체가 안 된 상태(NoDeviceError 등)에서는 None을 돌려줘서, 실패 처리 중에 또 예외가
    나서 원래 실패 원인을 덮어버리지 않도록 한다."""
    _bring_odin_to_front()
    filename = f"{name}.png"
    try:
        snapshot(filename=filename)
    except Exception as e:
        print(f"[SNAP] 스크린샷 실패 (무시하고 계속): {e}")
        return None
    return filename


def _send_to_sheet(passed, error_message=""):
    """sheets_config.py가 있으면, 실행 결과 한 줄을 Google Sheets 웹훅으로 전송한다.
    설정 파일이 없거나 전송이 실패해도 테스트 자체는 실패시키지 않는다."""
    try:
        import sheets_config
    except ImportError:
        return
    import datetime as _dt
    import requests

    payload = {
        "timestamp": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": "PASS" if passed else "FAIL",
        "duration": round(reporter.duration_seconds(), 1),
        "error": error_message,
        # Apps Script 쪽 TOKEN과 일치해야 기록됨 (양쪽 모두 비어 있으면 검사 생략)
        "token": getattr(sheets_config, "WEBHOOK_TOKEN", ""),
    }
    try:
        resp = requests.post(sheets_config.WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        # 배포 권한이 잘못되면 구글 로그인 페이지(HTML)가 200으로 오기 때문에,
        # HTTP 상태만 보지 않고 Apps Script가 돌려주는 JSON까지 확인한다.
        try:
            body = resp.json()
        except ValueError:
            raise ValueError("JSON이 아닌 응답을 받았습니다. Apps Script 배포 액세스가 '모든 사용자'인지 확인해주세요.")
        if body.get("status") != "ok":
            raise ValueError(f"Apps Script 응답: {body}")
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
        os.makedirs(LOG_DIR, exist_ok=True)
        report_path = os.path.join(LOG_DIR, "report.html")
        reporter.render(report_path, passed)
        print(f"[REPORT] {report_path}")
        _send_to_sheet(passed, error_message)
