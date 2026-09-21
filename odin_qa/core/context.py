# -*- encoding=utf8 -*-
"""시나리오 1회 실행의 상태. 시나리오 코드는 이 객체를 통해서만 단계 기록·스크린샷을 남긴다."""
import os
from contextlib import contextmanager

from . import client, errors
from .reporter import Reporter


class Context:
    def __init__(self, name, title):
        self.name = name
        self.title = title
        self.reporter = Reporter(title)
        self.failures = []  # [(항목 이름 또는 None, stage, 메시지)]
        self._case_index = 0

    # --- 기록 ---

    def step(self, text, status="info", screenshot=None):
        self.reporter.step(text, status=status, screenshot=screenshot)

    def snap(self, label):
        """스크린샷 파일명에 시나리오 이름을 붙여, 한 번의 실행에서 여러 시나리오가 같은 log 폴더를
        써도 파일이 겹치지 않게 한다."""
        return client.snap(f"{self.name}_{label}")

    @contextmanager
    def case(self, name):
        """항목 하나를 감싼다. 안에서 예외가 나면 그 항목만 FAIL로 기록하고 다음 항목으로 진행한다."""
        self._case_index += 1
        index = self._case_index
        self.step(f"[{name}] 확인 시작")
        try:
            yield
        except Exception as e:
            stage, message = errors.classify(e)
            self.failures.append((name, stage, message))
            self.step(
                f"[{name}] 실패 ({errors.STAGE_LABEL[stage]}): {message}",
                status="fail",
                screenshot=self.snap(f"case{index:02d}_fail"),
            )
        else:
            self.step(f"[{name}] 통과", status="pass")

    def fail(self, e):
        """시나리오 전체를 중단시킨 예외를 기록한다."""
        stage, message = errors.classify(e)
        self.failures.append((None, stage, message))
        self.step(
            f"실패 ({errors.STAGE_LABEL[stage]}): {message}",
            status="fail",
            screenshot=self.snap("99_failure"),
        )

    def skip(self, stage, message):
        """실행하지 않고 실패로 기록한다 (앞 시나리오가 실패해 사전 조건이 깨진 경우 등)."""
        self.failures.append((None, stage, message))
        self.step(f"실행하지 않음 ({errors.STAGE_LABEL[stage]}): {message}", status="fail")

    # --- 결과 ---

    @property
    def passed(self):
        return not self.failures

    def duration_seconds(self):
        return self.reporter.duration_seconds()

    def failure_stage(self):
        return self.failures[0][1] if self.failures else ""

    def failure_message(self):
        return "; ".join(f"{name}: {msg}" if name else msg for name, _, msg in self.failures)

    def render(self, log_dir):
        os.makedirs(log_dir, exist_ok=True)
        path = os.path.join(log_dir, f"{self.name}_report.html")
        self.reporter.render(path, self.passed)
        return path
