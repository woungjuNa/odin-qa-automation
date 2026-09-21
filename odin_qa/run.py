# -*- encoding=utf8 -*-
"""오딘 QA 자동화 진입점.

    python run.py smoke            스모크 테스트만
    python run.py top_menu         상단 메뉴 테스트만 (필요하면 인게임까지 자동 진입)
    python run.py all              등록된 시나리오를 순서대로 전부

시나리오마다 log/<이름>_report.html 과 Google Sheets 한 줄이 남는다.
하나라도 실패하면 종료 코드 1.
"""
import sys

from core import client, errors, sheets
from core.context import Context
from scenarios import smoke, top_menu

# 실행 순서대로. 스모크가 실패하면 뒤 시나리오는 실행하지 않는다.
SCENARIOS = {
    smoke.NAME: smoke,
    top_menu.NAME: top_menu,
}


def parse_names(argv):
    if not argv:
        print(__doc__)
        sys.exit(2)
    if argv == ["all"]:
        return list(SCENARIOS)
    unknown = [n for n in argv if n not in SCENARIOS]
    if unknown:
        print(f"알 수 없는 시나리오: {', '.join(unknown)} (사용 가능: {', '.join(SCENARIOS)})")
        sys.exit(2)
    return argv


def main(names):
    blocked = None  # (stage, message) — 이후 시나리오를 실행하지 않는 이유
    try:
        client.connect()
    except Exception as e:
        blocked = errors.classify(e)

    results = []
    for name in names:
        mod = SCENARIOS[name]
        ctx = Context(name, mod.TITLE)
        if blocked:
            ctx.skip(*blocked)
        else:
            ctx.step("오딘 창에 연결됨")
            try:
                mod.run(ctx)
            except Exception as e:
                ctx.fail(e)
        path = ctx.render(client.LOG_DIR)
        print(f"[REPORT] {path}")
        sheets.send(ctx)
        results.append(ctx)
        if name == "smoke" and not ctx.passed and not blocked:
            blocked = ("precondition", "스모크 테스트가 실패해 실행하지 않았습니다.")

    print("\n" + "\n".join(f"{'PASS' if c.passed else 'FAIL':4}  {c.name}" for c in results))
    return 0 if all(c.passed for c in results) else 1


if __name__ == "__main__":
    sys.exit(main(parse_names(sys.argv[1:])))
