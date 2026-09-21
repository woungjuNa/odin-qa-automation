# -*- encoding=utf8 -*-
from core import flows

NAME = "top_menu"
TITLE = "상단 메뉴: 각 메뉴 진입 및 복귀"

# (템플릿 키, 표시 이름). 템플릿은 templates/top_menu/<키>_icon.png, <키>_opened.png.
# 메뉴가 늘어나면 여기에 한 줄과 템플릿 두 장을 추가한다.
MENUS = [
    ("event", "이벤트"),
    ("gift", "선물"),
    ("shop", "BM 상점"),
    ("bag", "가방"),
    ("menu", "메뉴"),
]


def run(ctx):
    flows.ensure_ingame(ctx)
    for key, label in MENUS:
        with ctx.case(label):
            flows.open_menu(ctx, key, label)
            flows.close_menu(ctx, key, label)
        flows.recover_ingame(ctx)  # 실패로 메뉴가 열린 채 남았으면 다음 항목 전에 복귀 시도
