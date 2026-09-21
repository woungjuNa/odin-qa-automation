# -*- encoding=utf8 -*-
"""오딘 창 제어: 찾기·연결·전면화·스크린샷·템플릿 로드·대기 헬퍼.
Airtest/pywin32를 직접 만지는 코드는 이 파일과 flows.py에만 둔다."""
import os
import re
import time

import win32con
import win32gui
from airtest.core.api import Template, auto_setup, connect_device, exists, keyevent, sleep, snapshot

from .errors import TestFailure

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # odin_qa/
LOG_DIR = os.path.join(PROJECT_DIR, "log")
WINDOW_TITLE_RE = r"ODIN"


def T(name):
    """templates/<name>.png 템플릿. 예: T("common/splash_logo")"""
    return Template(f"templates/{name}.png")


# --- 창 ---

def find_odin_windows():
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
    count = len(find_odin_windows())
    if count == 0:
        raise TestFailure("setup", "오딘 창을 찾을 수 없습니다. 오딘을 실행해 스플래시 화면 상태로 띄워두고 다시 실행해주세요.")
    if count > 1:
        raise TestFailure("setup", f"오딘 창이 {count}개 열려 있습니다. 클라이언트가 중복 실행된 상태이니 하나만 남기고 다시 실행해주세요.")


def _clear_log_dir():
    """이전 실행의 로그(특히 Airtest가 매 동작마다 남기는 타임스탬프 jpg)를 지우고 시작한다.
    안 지우면 실행할수록 용량이 계속 늘어난다."""
    if os.path.isdir(LOG_DIR):
        for name in os.listdir(LOG_DIR):
            path = os.path.join(LOG_DIR, name)
            if os.path.isfile(path):
                os.remove(path)
    os.makedirs(LOG_DIR, exist_ok=True)


def connect(clear_log=True):
    """한 번의 실행에서 한 번만 호출한다. 이후 모든 시나리오가 이 연결을 공유한다.
    clear_log=False는 이전 캡처를 남겨야 하는 도구(tools/capture.py)용."""
    if clear_log:
        _clear_log_dir()
    os.makedirs(LOG_DIR, exist_ok=True)
    auto_setup(PROJECT_DIR, logdir=True)  # 템플릿 상대경로 기준 + log 폴더 = odin_qa/log
    _check_single_odin_window()
    connect_device(f"Windows:///?title_re={WINDOW_TITLE_RE}")


def bring_to_front():
    """다른 창에 가려진 채로 스크린샷이 찍히지 않도록 오딘 창을 맨 앞으로 가져온다."""
    hwnds = find_odin_windows()
    if not hwnds:
        return
    hwnd = hwnds[0]
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass  # Windows가 포커스 전환을 거부할 때가 있음 — 실패해도 스크린샷은 계속 시도
    sleep(0.3)


# --- 화면 ---

def snap(name):
    """오딘 창을 앞으로 가져온 뒤 log 폴더에 스크린샷을 저장하고 파일명을 돌려준다.
    연결이 안 된 상태에서는 None을 돌려줘서 실패 처리 중에 원인이 덮이지 않게 한다."""
    bring_to_front()
    filename = f"{name}.png"
    try:
        snapshot(filename=filename)
    except Exception as e:
        print(f"[SNAP] 스크린샷 실패 (무시하고 계속): {e}")
        return None
    return filename


def visible(template):
    return bool(exists(template))


def all_visible(*templates):
    return all(visible(t) for t in templates)


def wait_all(templates, timeout, description):
    """여러 템플릿이 모두 보일 때까지 기다린다. 시간 안에 안 보이면 verify 실패."""
    start = time.time()
    while time.time() - start < timeout:
        if all_visible(*templates):
            return
        sleep(0.5)
    raise TestFailure("verify", f"{description}이 {timeout}초 안에 모두 나타나지 않았습니다.")


def wait_gone(template, timeout, description):
    """템플릿이 화면에서 사라질 때까지 기다린다. 시간 안에 안 사라지면 verify 실패."""
    start = time.time()
    while time.time() - start < timeout:
        if not visible(template):
            return
        sleep(0.5)
    raise TestFailure("verify", f"ESC를 눌렀지만 {timeout}초 안에 {description}이 닫히지 않았습니다.")


def press_esc():
    bring_to_front()
    keyevent("{ESC}")
