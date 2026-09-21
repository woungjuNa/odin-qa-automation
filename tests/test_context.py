import os

import pytest

from core import context, errors


@pytest.fixture
def ctx(monkeypatch):
    # client.snap은 오딘이 있어야 동작하므로, 파일명만 돌려주는 가짜로 바꾼다
    monkeypatch.setattr(context.client, "snap", lambda name: f"{name}.png")
    return context.Context("demo", "데모 시나리오")


def test_snap_prefixes_scenario_name(ctx):
    assert ctx.snap("01_splash") == "demo_01_splash.png"


def test_passes_when_no_failures(ctx):
    ctx.step("한 단계")
    assert ctx.passed
    assert ctx.failure_stage() == ""
    assert ctx.failure_message() == ""


def test_case_records_failure_and_continues(ctx):
    with ctx.case("이벤트"):
        pass
    with ctx.case("선물"):
        raise errors.TestFailure("verify", "메뉴 화면이 나타나지 않았습니다.")
    with ctx.case("가방"):
        pass
    assert not ctx.passed
    assert ctx.failure_stage() == "verify"
    assert ctx.failure_message() == "선물: 메뉴 화면이 나타나지 않았습니다."
    statuses = [s["status"] for s in ctx.reporter.steps]
    assert statuses.count("pass") == 2 and statuses.count("fail") == 1


def test_case_failure_takes_screenshot(ctx):
    with ctx.case("선물"):
        raise errors.TestFailure("action", "아이콘을 찾지 못했습니다.")
    fail_step = [s for s in ctx.reporter.steps if s["status"] == "fail"][0]
    assert fail_step["screenshot"] == "demo_case01_fail.png"


def test_fail_records_scenario_level_failure(ctx):
    ctx.fail(KeyError("boom"))
    assert ctx.failure_stage() == "setup"
    assert ctx.failure_message().startswith("예상하지 못한 오류")


def test_skip_records_without_screenshot(ctx):
    ctx.skip("precondition", "스모크 테스트가 실패해 실행하지 않았습니다.")
    assert not ctx.passed
    assert ctx.failure_stage() == "precondition"
    assert ctx.reporter.steps[-1]["screenshot"] is None


def test_multiple_failures_join_with_semicolon(ctx):
    with ctx.case("A"):
        raise errors.TestFailure("action", "a")
    with ctx.case("B"):
        raise errors.TestFailure("verify", "b")
    assert ctx.failure_message() == "A: a; B: b"
    assert ctx.failure_stage() == "action"  # 첫 실패의 단계


def test_render_writes_named_report(ctx, tmp_path):
    ctx.step("단계", status="pass")
    path = ctx.render(str(tmp_path))
    assert os.path.basename(path) == "demo_report.html"
    assert "테스트 통과" in open(path, encoding="utf-8").read()
