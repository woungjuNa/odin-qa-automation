# -*- encoding=utf8 -*-
"""UI 회귀 테스트.

스모크 테스트로 도달한 각 화면에서, 미리 캡처해둔 템플릿 이미지를 기준(baseline)
삼아 같은 영역을 다시 캡처해서 픽셀 단위로 비교한다. 화면이 있는지(존재 여부)만
확인하는 스모크 테스트와 달리, 그 영역이 "예전과 똑같이 보이는지"까지 확인한다.
"""
import os
import re
import time

import win32con
import win32gui
from PIL import Image, ImageChops

from airtest.core.api import *
from report import Reporter

WINDOW_TITLE_RE = r"ODIN"

SPLASH_LOGO = Template(r"splash_logo.png")
CHARACTER_SELECT_TITLE = Template(r"character_select_title.png")
PLAY_BUTTON = Template(r"play_button.png")
INGAME_HUD = Template(r"ingame_hud.png")
INGAME_TOPMENU = Template(r"ingame_topmenu.png")

# 템플릿 파일명 -> 전체 화면 캡처(1168x621 기준) 안에서의 해당 영역 좌표 (left, top, right, bottom)
# Task 3~4에서 각 템플릿을 잘라낼 때 사용한 것과 동일한 좌표.
REGIONS = {
    "character_select_title.png": (10, 35, 175, 75),
    "ingame_hud.png": (1030, 460, 1100, 530),
    "ingame_topmenu.png": (1000, 28, 1155, 72),
}

# 영역별 허용 오차(%). 원형 아이콘(AUTO 버튼 등)은 사각형으로 크롭할 때 모서리에
# 캐릭터 뒤 배경이 살짝 걸려서, 캐릭터 위치가 바뀌면 그 배경도 함께 바뀐다.
# 이건 실제 UI 결함이 아니라 크롭 방식의 특성이라 허용 오차를 넉넉하게 잡는다.
DIFF_THRESHOLD_PERCENT = {
    "character_select_title.png": 3.0,   # 완전 고정 텍스트 영역 — 엄격하게
    "ingame_hud.png": 55.0,              # 원형 버튼 + 배경 bleed — 느슨하게
    "ingame_topmenu.png": 45.0,          # 원형 아이콘 다수 + 배경 bleed — 느슨하게
}

reporter = Reporter("오딘 UI 회귀 테스트")


def _bring_odin_to_front():
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


def _compare_region(template_filename, log_dir, tag):
    """template_filename에 해당하는 영역을 현재 화면에서 잘라내 기준 이미지와 비교한다."""
    _bring_odin_to_front()
    full_shot_name = f"{tag}_full.png"
    snapshot(filename=full_shot_name)

    full_path = os.path.join(log_dir, full_shot_name)
    box = REGIONS[template_filename]

    baseline = Image.open(template_filename).convert("RGB")
    current_full = Image.open(full_path).convert("RGB")
    current_crop = current_full.crop(box).resize(baseline.size)

    diff = ImageChops.difference(baseline, current_crop)
    diff_pixels = sum(1 for px in diff.getdata() if max(px) > 30)
    total_pixels = diff.size[0] * diff.size[1]
    diff_percent = (diff_pixels / total_pixels) * 100

    current_name = f"{tag}_current.png"
    diff_name = f"{tag}_diff.png"
    current_crop.save(os.path.join(log_dir, current_name))
    diff.save(os.path.join(log_dir, diff_name))

    threshold = DIFF_THRESHOLD_PERCENT[template_filename]
    passed = diff_percent <= threshold
    reporter.step(
        f"{template_filename} 영역 UI 회귀 비교",
        status="pass" if passed else "fail",
        compare=[
            ("기준(baseline)", template_filename),
            ("현재", current_name),
            ("차이", diff_name),
        ],
        diff_percent=diff_percent,
    )
    return passed


def run_ui_regression_test():
    auto_setup(__file__, logdir=True)
    connect_device(f"Windows:///?title_re={WINDOW_TITLE_RE}")
    reporter.step("오딘 창에 연결됨")

    wait(SPLASH_LOGO, timeout=15)
    for attempt in range(15):
        if not exists(SPLASH_LOGO):
            break
        touch(SPLASH_LOGO)
        sleep(1)
    else:
        raise TargetNotFoundError("스플래시 화면을 15번 클릭했지만 다음 화면으로 넘어가지 않음")
    reporter.step("스플래시 통과 완료")

    wait(CHARACTER_SELECT_TITLE, timeout=30)

    log_dir = os.path.join(os.path.dirname(__file__), "log")
    os.makedirs(log_dir, exist_ok=True)

    ok1 = _compare_region("character_select_title.png", log_dir, "01_char_select")

    for attempt in range(10):
        if not exists(CHARACTER_SELECT_TITLE):
            break
        touch(PLAY_BUTTON)
        sleep(1)
    else:
        raise TargetNotFoundError("게임하기 버튼을 10번 눌렀지만 캐릭터 선택 화면을 벗어나지 못함")

    start = time.time()
    while time.time() - start < 60:
        if exists(INGAME_HUD) and exists(INGAME_TOPMENU):
            break
        sleep(0.5)
    else:
        raise TargetNotFoundError("60초 안에 인게임 화면에 진입하지 못함")

    ok2 = _compare_region("ingame_hud.png", log_dir, "02_ingame_hud")
    ok3 = _compare_region("ingame_topmenu.png", log_dir, "03_ingame_topmenu")

    return ok1 and ok2 and ok3


if __name__ == "__main__":
    passed = False
    try:
        passed = run_ui_regression_test()
    except Exception as e:
        reporter.step(f"UI 회귀 테스트 실패: {e}", status="fail")
        raise
    finally:
        log_dir = os.path.join(os.path.dirname(__file__), "log")
        os.makedirs(log_dir, exist_ok=True)
        reporter.render(os.path.join(log_dir, "ui_regression_report.html"), passed)
        print(f"[REPORT] {os.path.join(log_dir, 'ui_regression_report.html')}")
