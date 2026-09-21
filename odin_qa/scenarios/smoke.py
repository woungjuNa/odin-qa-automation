# -*- encoding=utf8 -*-
from core import flows

NAME = "smoke"
TITLE = "오딘 스모크 테스트: 실행 → 스플래시 통과 → 캐릭터 선택 → 인게임 진입"


def run(ctx):
    flows.pass_splash(ctx)
    flows.enter_game(ctx)
    ctx.step(
        "인게임 진입 확인됨 (HP/MP 바 + 상단 메뉴 아이콘 모두 확인)",
        status="pass",
        screenshot=ctx.snap("05_ingame"),
    )
