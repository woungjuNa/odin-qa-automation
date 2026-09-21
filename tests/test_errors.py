import pywintypes
from airtest.aircv.error import FileNotExistError
from airtest.core.error import NoDeviceError, TargetNotFoundError
from pywinauto.findwindows import ElementAmbiguousError, ElementNotFoundError

from core import errors


def test_test_failure_carries_stage_and_message():
    e = errors.TestFailure("verify", "메뉴 화면이 나타나지 않았습니다.")
    assert e.stage == "verify"
    assert str(e) == "메뉴 화면이 나타나지 않았습니다."


def test_classify_returns_stage_of_test_failure():
    e = errors.TestFailure("action", "아이콘을 찾지 못했습니다.")
    assert errors.classify(e) == ("action", "아이콘을 찾지 못했습니다.")


def test_classify_maps_library_errors_to_setup_with_korean_message():
    stage, message = errors.classify(ElementAmbiguousError("There are 2 elements"))
    assert stage == "setup"
    assert "여러 개" in message and "There are" not in message


def test_describe_error_translations():
    assert "찾을 수 없습니다" in errors.describe_error(ElementNotFoundError("x"))
    assert "연결되지 않은" in errors.describe_error(NoDeviceError("No devices added."))
    assert "UI 요소" in errors.describe_error(TargetNotFoundError("Picture not found"))
    assert errors.describe_error(Exception("한글 메시지")) == "한글 메시지"
    assert errors.describe_error(KeyError("boom")).startswith("예상하지 못한 오류")


def test_stage_labels_cover_all_stages():
    assert set(errors.STAGE_LABEL) == set(errors.STAGES)


def test_describe_error_uipi_cursor_block_suggests_admin():
    e = pywintypes.error(0, "SetCursorPos", "No error message is available")
    assert "관리자 권한" in errors.describe_error(e)
    assert errors.classify(e)[0] == "setup"


def test_describe_error_missing_template_file():
    e = FileNotExistError("File not exist: templates/top_menu/gift_opened.png")
    assert "템플릿 이미지 파일이 없습니다" in errors.describe_error(e)
    assert errors.classify(e)[0] == "setup"
