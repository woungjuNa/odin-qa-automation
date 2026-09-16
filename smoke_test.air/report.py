# -*- encoding=utf8 -*-
"""오딘 스모크 테스트용 리포트 생성기.

Airtest 기본 리포트 대신, 이 스크립트 자체가 기록한 단계(step)들로
가독성 좋은 단일 HTML 파일을 만든다.
"""
import datetime
import html

_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  :root {{
    --bg: #f7f7f8;
    --card: #ffffff;
    --border: #e5e5e8;
    --text: #1c1c1f;
    --muted: #6b6b74;
    --pass: #1a9e5c;
    --pass-bg: #e8f7ef;
    --fail: #d64545;
    --fail-bg: #fceaea;
    --info: #4a5cff;
    --info-bg: #eef0ff;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 32px 16px;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;
  }}
  .wrap {{ max-width: 720px; margin: 0 auto; }}
  header {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
  }}
  h1 {{ font-size: 20px; margin: 0 0 4px; }}
  .meta {{ color: var(--muted); font-size: 13px; }}
  .badge {{
    display: inline-block;
    margin-top: 12px;
    padding: 6px 14px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 14px;
  }}
  .badge.pass {{ background: var(--pass-bg); color: var(--pass); }}
  .badge.fail {{ background: var(--fail-bg); color: var(--fail); }}
  .steps {{ display: flex; flex-direction: column; gap: 10px; }}
  .step {{
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 4px solid var(--info);
    border-radius: 10px;
    padding: 14px 16px;
  }}
  .step.pass {{ border-left-color: var(--pass); }}
  .step.fail {{ border-left-color: var(--fail); }}
  .step-head {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
  }}
  .step-name {{ font-weight: 600; font-size: 14px; }}
  .step-time {{ color: var(--muted); font-size: 12px; white-space: nowrap; }}
  .step-tag {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.03em;
    padding: 2px 8px;
    border-radius: 999px;
    margin-right: 8px;
  }}
  .step.info .step-tag {{ background: var(--info-bg); color: var(--info); }}
  .step.pass .step-tag {{ background: var(--pass-bg); color: var(--pass); }}
  .step.fail .step-tag {{ background: var(--fail-bg); color: var(--fail); }}
  .step img {{
    margin-top: 10px;
    max-width: 100%;
    border-radius: 8px;
    border: 1px solid var(--border);
    display: block;
  }}
  .compare {{
    display: flex;
    gap: 10px;
    margin-top: 10px;
    flex-wrap: wrap;
  }}
  .compare figure {{
    margin: 0;
    flex: 1;
    min-width: 140px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .compare img {{
    width: 100%;
    border-radius: 8px;
    border: 1px solid var(--border);
    display: block;
  }}
  .compare figcaption {{
    font-size: 11px;
    color: var(--muted);
    text-align: center;
  }}
  .diff-percent {{
    font-size: 12px;
    color: var(--muted);
    margin-top: 8px;
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{title}</h1>
    <div class="meta">{run_at} · 총 소요 {duration:.1f}초</div>
    <div class="badge {result_class}">{result_text}</div>
  </header>
  <div class="steps">
    {steps_html}
  </div>
</div>
</body>
</html>
"""

_STEP_TEMPLATE = """<div class="step {status}">
  <div class="step-head">
    <div><span class="step-tag">{status_label}</span><span class="step-name">{name}</span></div>
    <div class="step-time">{time}</div>
  </div>
  {image_html}
</div>"""

_STATUS_LABEL = {"info": "STEP", "pass": "PASS", "fail": "FAIL"}


class Reporter:
    def __init__(self, title):
        self.title = title
        self.started_at = datetime.datetime.now()
        self.steps = []

    def step(self, name, status="info", screenshot=None, compare=None, diff_percent=None):
        """단계를 기록한다. status: info / pass / fail.
        screenshot: 단일 이미지 파일명 (log 폴더 기준 상대 경로)
        compare: [(caption, 파일명), ...] 형태로 여러 이미지를 나란히 표시 (기준/현재/차이 비교용)
        diff_percent: UI 회귀 테스트에서 계산한 차이 비율(%)
        """
        self.steps.append({
            "name": name,
            "status": status,
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "screenshot": screenshot,
            "compare": compare,
            "diff_percent": diff_percent,
        })
        print(f"[{_STATUS_LABEL.get(status, 'STEP')}] {name}")

    def render(self, output_path, passed):
        duration = (datetime.datetime.now() - self.started_at).total_seconds()
        steps_html = "\n".join(self._render_step(s) for s in self.steps)
        result_class = "pass" if passed else "fail"
        result_text = "테스트 통과" if passed else "테스트 실패"
        html_content = _TEMPLATE.format(
            title=html.escape(self.title),
            run_at=self.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            duration=duration,
            result_class=result_class,
            result_text=result_text,
            steps_html=steps_html,
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    @staticmethod
    def _render_step(s):
        image_html = ""
        if s.get("compare"):
            figures = "".join(
                f'<figure><img src="{html.escape(path)}" alt="{html.escape(caption)}">'
                f'<figcaption>{html.escape(caption)}</figcaption></figure>'
                for caption, path in s["compare"]
            )
            image_html = f'<div class="compare">{figures}</div>'
            if s.get("diff_percent") is not None:
                image_html += f'<div class="diff-percent">차이 비율: {s["diff_percent"]:.2f}%</div>'
        elif s["screenshot"]:
            image_html = f'<img src="{html.escape(s["screenshot"])}" alt="screenshot">'
        return _STEP_TEMPLATE.format(
            status=s["status"],
            status_label=_STATUS_LABEL.get(s["status"], "STEP"),
            name=html.escape(s["name"]),
            time=s["time"],
            image_html=image_html,
        )
