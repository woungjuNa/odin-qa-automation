# -*- encoding=utf8 -*-
from airtest.core.api import *

WINDOW_TITLE_RE = r"ODIN"

SPLASH_LOGO = Template(r"splash_logo.png")
CHARACTER_SELECT_TITLE = Template(r"character_select_title.png")


def run_smoke_test():
    auto_setup(__file__, logdir=True, devices=[f"Windows:///?title_re={WINDOW_TITLE_RE}"])
    print("[STEP] 오딘 창에 연결됨")

    print("[STEP] 스플래시 화면 대기 중...")
    wait(SPLASH_LOGO, timeout=15)

    print("[STEP] 스플래시 화면 클릭 시도 (화면이 넘어갈 때까지 반복)...")
    for attempt in range(15):
        if not exists(SPLASH_LOGO):
            break
        touch(SPLASH_LOGO)
        sleep(1)
    else:
        raise TargetNotFoundError("스플래시 화면을 15번 클릭했지만 다음 화면으로 넘어가지 않음")
    print("[STEP] 스플래시 통과 완료")

    print("[STEP] 캐릭터 선택 화면 진입 대기 중...")
    wait(CHARACTER_SELECT_TITLE, timeout=30)
    print("[PASS] 스모크 테스트 성공: 캐릭터 선택 화면 진입 확인됨")


if __name__ == "__main__":
    run_smoke_test()
