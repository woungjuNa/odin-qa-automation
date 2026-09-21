# -*- encoding=utf8 -*-
"""실행 결과 한 줄을 Google Sheets 웹훅(Apps Script)으로 보낸다."""
import datetime

import requests

from . import errors


def send(ctx):
    """sheets_config.py가 있으면 결과를 전송한다. 설정이 없거나 전송이 실패해도 테스트 결과에는
    영향을 주지 않는다."""
    try:
        import sheets_config
    except ImportError:
        return

    stage = ctx.failure_stage()
    payload = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scenario": ctx.name,
        "result": "PASS" if ctx.passed else "FAIL",
        "duration": round(ctx.duration_seconds(), 1),
        "stage": errors.STAGE_LABEL[stage] if stage else "",
        "error": ctx.failure_message(),
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
        print(f"[SHEET] {ctx.name}: Google Sheets에 결과 전송 완료")
    except Exception as e:
        print(f"[SHEET] {ctx.name}: Google Sheets 전송 실패 (무시하고 계속): {e}")
