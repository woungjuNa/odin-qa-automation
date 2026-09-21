# -*- encoding=utf8 -*-
"""테스트 실패를 단계별로 구분하고, 라이브러리 예외를 한글 문장으로 바꾼다."""
import pywintypes
from airtest.aircv.error import FileNotExistError
from airtest.core.error import NoDeviceError, TargetNotFoundError
from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError

STAGES = ("setup", "precondition", "action", "verify")
STAGE_LABEL = {
    "setup": "실행 준비",        # 테스트를 시작할 수 없음 (오딘 창 없음/중복)
    "precondition": "사전 조건",  # 시나리오의 전제가 안 갖춰짐 (인게임 진입 실패)
    "action": "조작",            # 조작이 안 됨 (아이콘을 못 찾음)
    "verify": "화면 확인",       # 조작은 됐는데 기대한 화면이 아님
}


class TestFailure(Exception):
    """이 프로젝트가 직접 판정한 실패. stage로 어느 단계에서 실패했는지 구분한다."""

    def __init__(self, stage, message):
        if stage not in STAGES:
            raise ValueError(f"알 수 없는 stage: {stage}")
        super().__init__(message)
        self.stage = stage


def describe_error(e):
    """예외를 리포트/시트에 기록할 한글 문장으로 바꾼다. TestFailure와 이 프로젝트가 만든 Exception은
    이미 한글이라 그대로 두고, 라이브러리(pywinauto/Airtest) 예외는 원문 대신 상황을 설명한다.
    영문 원문은 콘솔 트레이스백에 그대로 남는다."""
    if isinstance(e, TestFailure):
        return str(e)
    if isinstance(e, ElementAmbiguousError):
        return "오딘 창이 여러 개 열려 있어 어느 창에 연결할지 정할 수 없습니다. 클라이언트를 하나만 남기고 다시 실행해주세요."
    if isinstance(e, ElementNotFoundError):
        return "오딘 창을 찾을 수 없습니다. 오딘을 실행해 스플래시 화면 상태로 띄워두고 다시 실행해주세요."
    if isinstance(e, NoDeviceError):
        return "오딘 창에 연결되지 않은 상태에서 화면 작업을 시도했습니다. 연결 단계가 실패했는지 확인해주세요."
    if isinstance(e, TargetNotFoundError):
        return f"화면에서 필요한 UI 요소를 찾지 못했습니다. ({e})"
    if isinstance(e, FileNotExistError):
        return f"템플릿 이미지 파일이 없습니다. templates 폴더를 확인해주세요. ({e})"
    if isinstance(e, pywintypes.error) and len(e.args) >= 2 and e.args[1] in ("SetCursorPos", "SetForegroundWindow"):
        # 오딘은 관리자 권한으로 실행되어, 일반 권한 프로세스의 입력은 Windows UIPI에 막힌다
        return "마우스/창 제어가 거부되었습니다. 오딘이 관리자 권한으로 실행 중이므로, 이 스크립트도 관리자 권한 터미널에서 실행해주세요."
    if type(e) is Exception:
        return str(e)
    return f"예상하지 못한 오류가 발생했습니다. ({type(e).__name__}: {e})"


def classify(e):
    """(stage, 한글 메시지). TestFailure가 아닌 예외는 모두 '실행 준비' 단계로 본다."""
    if isinstance(e, TestFailure):
        return e.stage, str(e)
    return "setup", describe_error(e)
