# 오딘 QA 자동화 스모크 테스트 (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 오딘: 발할라 라이징 PC 클라이언트에 대해 "실행 → 스플래시 통과 → 캐릭터 선택 화면 진입"을 자동으로 검증하고 HTML 리포트를 생성하는 스모크 테스트 스크립트를 만든다. (게임 클라이언트 내부에 별도 로그인 화면이 없음을 구현 중 확인 — 로그인은 범위 밖)

**Architecture:** Airtest 프레임워크로 오딘 PC 클라이언트 창에 연결하고, 이미지 템플릿 매칭으로 화면 요소(스플래시 로고, 캐릭터 선택 화면 고정 타이틀)를 인식·클릭한다. Airtest의 `.air` 프로젝트 규칙(`<name>.air/<name>.py`)을 따라 실행 로그와 스크린샷이 자동 기록되고, `airtest report` 명령으로 HTML 리포트를 생성한다.

**Tech Stack:** Python 3.x, Airtest (pip 패키지), pywin32, VS Code, AirtestIDE (템플릿 이미지 캡처용 GUI 툴)

**Spec:** [docs/superpowers/specs/2026-09-15-odin-qa-automation-design.md](../specs/2026-09-15-odin-qa-automation-design.md)

## Global Constraints

- 대상: 오딘: 발할라 라이징 PC 클라이언트 (Windows, 언리얼 엔진 렌더링 화면)
- 자동화 프레임워크: Airtest (이미지 템플릿 매칭 방식)
- 로그인은 웹사이트에서 클라이언트 실행 전에 끝나 있는 상태를 전제로 함 — 스크립트는 계정 정보를 다루지 않음
- 오딘 클라이언트는 **창모드(windowed)**로 실행 — 전체화면 exclusive 모드는 Windows 화면 캡처 API로 스크린샷이 안 찍힐 수 있음
- Python 3.13에서는 airtest의 numpy<2.0 의존성이 사전빌드 wheel을 제공하지 않아 컴파일 실패함 → **Python 3.12** 사용
- 오딘은 안티치트 때문에 관리자 권한으로 실행됨 → 마우스 클릭 자동화(스크립트)도 **관리자 권한 터미널**에서 실행해야 함 (일반 권한에서는 Windows UIPI로 인해 `SetCursorPos`/`PostMessage`가 조용히 실패함)
- 프로젝트 루트: `C:\Users\dndwn\Desktop\QA_AI`

---

## Task 1: 개발 환경 설치 (Python + VS Code)

**Files:** 없음 (시스템 프로그램 설치)

**산출물:** 이후 모든 작업에서 사용할 Python 실행 환경과 코드 에디터

- [x] **Step 1: Python 설치**

https://www.python.org/downloads/ 접속 → "Download Python 3.x.x" 클릭 → 설치 파일 실행.

설치 화면 **맨 아래 "Add python.exe to PATH" 체크박스를 반드시 체크**한 후 "Install Now" 클릭. (체크 안 하면 이후 명령어들이 동작하지 않음)

- [x] **Step 2: 설치 확인**

명령 프롬프트(cmd) 또는 PowerShell을 새로 열고 실행:

```
python --version
```

기대 결과: `Python 3.x.x` 형태로 버전이 출력됨. "python은 내부 또는 외부 명령이 아닙니다" 오류가 나오면 PATH 설정이 안 된 것이므로, 설치 프로그램을 다시 실행해서 "Modify" → "Add to PATH" 체크 후 재설치.

- [x] **Step 3: VS Code 설치**

https://code.visualstudio.com 접속 → 다운로드 → 설치 파일 실행 (기본 옵션으로 계속 진행).

- [x] **Step 4: VS Code Python 확장 설치**

VS Code 실행 → 왼쪽 아이콘 모음에서 Extensions 아이콘 클릭 (또는 `Ctrl+Shift+X`) → 검색창에 "Python" 입력 → 게시자가 **Microsoft**인 확장 설치.

- [x] **Step 5: 확인**

VS Code에서 `Ctrl+`` `` (백틱)으로 통합 터미널을 열고 `python --version`을 다시 실행해 같은 버전이 나오는지 확인.

---

## Task 2: 프로젝트 구조 생성 + 가상환경 + Airtest 설치

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`

**Interfaces:**
- Consumes: Task 1의 Python 환경
- Produces: `venv` 가상환경, 설치된 `airtest`/`pywin32` 패키지 — 이후 모든 코드 작업이 이 가상환경 위에서 실행됨

**(실행 노트: 최초 Python 3.13으로 진행했으나 airtest의 numpy<2.0 의존성이 3.13용 wheel을 제공하지 않아 컴파일 에러 발생. winget으로 Python 3.12를 추가 설치하고 `py -3.12 -m venv venv`로 가상환경을 다시 만들어 해결함. 이후 단계의 `python`은 이 3.12 venv 기준.)**

- [x] **Step 1: 가상환경 생성**

VS Code에서 `File > Open Folder`로 `C:\Users\dndwn\Desktop\QA_AI` 폴더 열기. 통합 터미널에서:

```
python -m venv venv
```

- [x] **Step 2: 가상환경 활성화**

```
venv\Scripts\activate
```

터미널 프롬프트 앞에 `(venv)`가 표시되면 성공.

- [x] **Step 3: Airtest 및 관련 패키지 설치**

```
pip install airtest pywin32 airtest-selenium
```

(`airtest-selenium`은 불필요하면 제외 가능하지만, 최신 airtest 패키지가 일부 win 플랫폼 의존성을 함께 요구하는 경우가 있어 포함. 설치 중 에러가 나면 에러 메시지를 확인해 개별 패키지명으로 재시도)

실제로 필요한 최소 설치는:

```
pip install airtest pywin32
```

- [x] **Step 4: 설치 확인**

```
python -c "import airtest; print(airtest.__version__)"
```

기대 결과: 버전 문자열 출력 (예: `1.3.3`). ImportError가 나면 Step 3의 가상환경이 활성화된 상태인지 확인.

- [x] **Step 5: requirements.txt 생성**

```
pip freeze > requirements.txt
```

- [x] **Step 6: .gitignore 작성**

`.gitignore` 파일 생성:

```
venv/
smoke_test.air/log/
smoke_test.air/report.html
__pycache__/
*.pyc
```

- [x] **Step 7: Commit**

```
git add requirements.txt .gitignore
git commit -m "chore: set up Python venv and Airtest dependencies"
```

**(실행 노트: 최초에는 계정 정보를 담을 `config.py`/`config.example.py`도 만들었으나, Task 3~4 진행 중 오딘 클라이언트에 별도 로그인 화면이 없다는 걸 확인하면서 불필요해져 삭제함. 스크립트가 계정 정보를 다룰 일이 없음.)**

---

## Task 3: AirtestIDE로 오딘 연결 확인 + 템플릿 이미지 캡처

**Files:**
- Create: `smoke_test.air/splash_logo.png`
- Create: `smoke_test.air/character_select_title.png`

**Interfaces:**
- Consumes: 없음 (독립적인 GUI 작업)
- Produces: Task 4의 스크립트가 참조할 템플릿 이미지 2개, 오딘 창의 정확한 제목(title) 문자열

- [x] **Step 1: AirtestIDE 다운로드 및 실행**

https://airtest.netease.com/ 에서 다운로드 → 압축 해제 → `AirtestIDE.exe` 실행. 로그인 화면에서 계정 서버가 503으로 응답하는 경우, **"Skip"** 버튼으로 로그인 없이 진행 가능.

- [x] **Step 2: 오딘 클라이언트를 창모드로 실행**

오딘 PC 클라이언트 실행 → 화면 설정에서 **창모드**로 변경. (전체화면은 화면 캡처 실패 가능성 있음)

**(실행 노트: AirtestIDE의 "Devices" 패널(Windows App Connection의 Search Window/Select Game Frame)이 클릭해도 목록이 비어 보이는 문제가 있었고, 한 번 시도 후에는 오래된 창 핸들이 내부에 캐싱되어 이후 스크립트 실행이 `Invalid handle` 에러로 실패하는 부작용도 있었음. 그래서 Devices 패널은 사용하지 않고, 아래처럼 스크립트에서 직접 `connect_device()`를 호출하는 방식으로 우회함. 문제가 재발하면 AirtestIDE를 완전히 재시작.)**

- [x] **Step 3: 창 제목 확인 + 스크립트에서 직접 연결**

작업 표시줄에서 오딘 아이콘에 마우스를 올려 창 제목 확인 (실제 확인된 값: `ODIN`).

AirtestIDE의 Script Editor(`untitled.air`)에 아래 코드 작성 후 Run(▶):

```python
# -*- encoding=utf8 -*-
__author__ = "dndwn"

from airtest.core.api import *

auto_setup(__file__)
connect_device("Windows:///?title_re=ODIN")
```

`Ran 1 test ... OK`가 뜨면 연결 성공.

- [x] **Step 4: .air 프로젝트 폴더 준비**

`smoke_test.air` 폴더를 프로젝트 루트에 생성 (템플릿 이미지와 스크립트를 여기에 모음).

- [x] **Step 5: 스크린샷 캡처용 코드 추가**

Step 3 스크립트 마지막에 한 줄 추가 후 Run:

```python
snapshot(filename="capture.png")
```

실행 로그의 `save log in '...'` 경로에 `capture.png`가 저장됨.

- [x] **Step 6: 스플래시 로고 템플릿 만들기**

오딘을 스플래시 화면("화면을 터치해주세요") 상태로 띄운 채 Step 5 스크립트 실행 → 저장된 `capture.png`에서 "ODIN VALHALLA RISING" 로고 영역을 Python/Pillow로 크롭해서 `smoke_test.air/splash_logo.png`로 저장.

**(실행 노트: AirtestIDE의 Devices 패널로 화면을 보며 드래그 선택하는 대신, `snapshot()`으로 찍은 전체 화면 이미지를 Pillow `crop()`으로 잘라내는 방식을 사용함 — 패널 버그를 우회하면서 결과는 동일.)**

- [x] **Step 7: 캐릭터 선택 화면 템플릿 만들기**

**(설계 변경: 오딘 PC 클라이언트는 로그인을 웹사이트에서 먼저 처리하고 클라이언트를 실행하는 구조라, 클라이언트 내부에 별도 로그인 화면이 없음을 확인함. 스플래시 다음 화면은 바로 "캐릭터 선택" 화면. 캐릭터 선택 후 인게임 진입은 계정마다 보유 캐릭터가 달라 재현성이 떨어져 Phase 1 범위에서 제외 — 캐릭터 선택 화면 진입까지만 검증.)**

오딘 스플래시를 클릭해 캐릭터 선택 화면까지 진행 → Step 5 스크립트를 다시 Run → `capture.png`에서, 캐릭터 목록과 무관하게 항상 고정으로 표시되는 좌상단 **"← 캐릭터 선택"** 제목 텍스트 영역만 크롭해서 `smoke_test.air/character_select_title.png`로 저장. (캐릭터 초상화 등 계정별로 달라지는 부분은 절대 템플릿에 포함하지 않기 — 재현성 확보)

- [x] **Step 8: 확인**

파일 탐색기에서 `smoke_test.air` 폴더에 `splash_logo.png`, `character_select_title.png` 2개 파일이 있는지 확인.

- [x] **Step 9: Commit**

```
git add smoke_test.air/splash_logo.png smoke_test.air/character_select_title.png
git commit -m "feat: capture template images for smoke test"
```

---

## Task 4: 스모크 테스트 스크립트 작성

**Files:**
- Create: `smoke_test.air/smoke_test.py`

**Interfaces:**
- Consumes: Task 3의 템플릿 이미지 2개 (`smoke_test.air/splash_logo.png`, `character_select_title.png`)
- Produces: `run_smoke_test()` 함수 — 실행 시 성공하면 콘솔에 `[PASS]` 출력, 실패 시 예외 발생. `smoke_test.air/log/` 폴더에 실행 로그와 스크린샷 기록

- [x] **Step 1: 연결 코드 작성 (스크립트 뼈대)**

`smoke_test.air/smoke_test.py` 생성 (Task 3에서 확인한 창 제목 "ODIN" 사용):

```python
from airtest.core.api import *

WINDOW_TITLE_RE = r"ODIN"

SPLASH_LOGO = Template(r"splash_logo.png")
CHARACTER_SELECT_TITLE = Template(r"character_select_title.png")


def run_smoke_test():
    auto_setup(__file__, logdir=True, devices=[f"Windows:///?title_re={WINDOW_TITLE_RE}"])
    print("[STEP] 오딘 창에 연결됨")


if __name__ == "__main__":
    run_smoke_test()
```

- [x] **Step 2: 실행해서 연결만 확인**

오딘 클라이언트를 실행해둔 상태에서, VS Code 터미널(가상환경 활성화된 상태)에서:

```
cd smoke_test.air
python smoke_test.py
```

기대 결과: 콘솔에 `[STEP] 오딘 창에 연결됨` 출력.

- [x] **Step 3: 스플래시 통과 로직 추가**

`run_smoke_test()` 함수를 아래로 교체:

```python
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
```

**(실행 노트: 처음엔 `touch(SPLASH_LOGO)` 한 번만 호출했는데, 실제 게임에선 로고가 뜨는 로딩 화면과 "터치해주세요" 인터랙티브 화면이 같은 이미지로 보여서 로딩 중에 클릭이 씹히는 문제가 있었음. 화면이 실제로 넘어갈 때까지(`exists()`가 False가 될 때까지) 반복 클릭하는 방식으로 수정해서 해결함.)**

**(실행 노트 — 관리자 권한: 처음 실행했을 때 `touch()` 단계에서 `pywintypes.error: SetCursorPos` 에러가 발생함. 오딘이 안티치트 때문에 관리자 권한으로 실행 중이라, 일반 권한 터미널에서는 Windows UIPI가 커서 제어/메시지 전달을 막았기 때문. VS Code를 관리자 권한으로 재실행해서 해결함.)**

- [x] **Step 4: 실행해서 스플래시 단계까지 확인**

오딘을 스플래시 화면 상태로 재실행한 뒤:

```
python smoke_test.py
```

기대 결과: `[STEP] 스플래시 통과 완료`까지 출력되고 실제로 화면이 클릭되어 다음 화면으로 넘어감. `wait` 단계에서 타임아웃 예외가 나면 `splash_logo.png` 템플릿이 현재 화면과 맞는지 확인.

- [x] **Step 5: 캐릭터 선택 화면 진입 확인 로직 추가**

함수를 최종 버전으로 교체:

```python
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
```

- [x] **Step 6: 전체 실행 확인**

오딘을 처음 상태(스플래시)로 재실행 후:

```
python smoke_test.py
```

기대 결과: `[PASS] 스모크 테스트 성공: 캐릭터 선택 화면 진입 확인됨`까지 콘솔에 출력됨.

- [x] **Step 7: Commit**

```
cd ..
git add smoke_test.air/smoke_test.py
git commit -m "feat: implement smoke test script (splash -> character select screen)"
```

---

## Task 5: 실패 상황 처리 + 커스텀 HTML 리포트

**Files:**
- Create: `smoke_test.air/report.py`
- Modify: `smoke_test.air/smoke_test.py`

**Interfaces:**
- Consumes: Task 4의 `run_smoke_test()`
- Produces: `Reporter` 클래스 (`step()`, `render()`), 실패 시에도 스크린샷이 남는 에러 처리, `smoke_test.air/log/report.html`

**(실행 노트: 계획 원안은 Airtest 기본 `airtest report` CLI 명령으로 리포트를 생성하는 것이었으나, 실제로 보니 가독성이 떨어지고 디자인이 정리되어 있지 않아 포트폴리오용으로 부족했음. 대신 `report.py`에 직접 만든 `Reporter` 클래스로, 단계별 결과(이름/상태/스크린샷)를 모아 깔끔한 단일 HTML 페이지를 렌더링하는 방식으로 변경함. `smoke_test.py`도 각 단계마다 `reporter.step(...)`을 호출하고 스크린샷을 남기도록 재구성함. 스크린샷 촬영 전에는 다른 창이 오딘 위에 겹쳐서 찍히는 문제가 있어, `_bring_odin_to_front()`로 오딘 창을 맨 앞으로 가져온 뒤 캡처하도록 처리함.)**

- [x] **Step 1: `report.py`에 `Reporter` 클래스 작성**

`Reporter(title)`로 생성 → `reporter.step(name, status="info"|"pass"|"fail", screenshot=파일명)`으로 단계를 기록 → `reporter.render(output_path, passed)`로 카드 스타일 HTML(배지, 색상, 스크린샷 인라인)을 생성.

- [x] **Step 2: `smoke_test.py`를 Reporter 사용하도록 재구성**

각 단계(연결/스플래시 감지/스플래시 통과/캐릭터 선택 확인)마다 `reporter.step(...)` 호출 + `_snap()`으로 스크린샷 저장. 실패 시 `except` 블록에서 `status="fail"`로 기록. `finally` 블록에서 항상 `reporter.render(...)` 호출해 성공/실패 관계없이 리포트가 남도록 함.

- [x] **Step 3: 의도적으로 실패시켜 동작 확인**

`SPLASH_LOGO = Template(r"splash_logo.png")` 줄을 일시적으로 `SPLASH_LOGO = Template(r"nonexistent.png")`로 바꾸고 실행 → `log/report.html`에 "테스트 실패" 배지와 FAIL 단계가 표시되는지 확인 → 원복.

- [x] **Step 4: 정상 실행 + 리포트 확인**

오딘을 스플래시 상태로 재실행 후 `python smoke_test.py` → `log/report.html`을 브라우저로 열어 "테스트 통과" 배지, 4단계, 스크린샷 3장이 모두 깔끔하게(다른 창 안 겹치고) 표시되는지 확인.

- [x] **Step 5: Commit**

```
cd ..
git add smoke_test.air/report.py smoke_test.air/smoke_test.py .gitignore
git commit -m "feat: replace Airtest's default report with a custom clean HTML report"
```

(`log/`은 `.gitignore`에 있어 커밋되지 않음 — 실행할 때마다 로컬에서 새로 생성됨)

---

## Task 6: README 작성 (포트폴리오 문서화)

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: Task 1~5의 전체 결과물
- Produces: 포트폴리오/면접에서 프로젝트를 설명할 때 참고할 문서

- [ ] **Step 1: README.md 작성**

```markdown
# 오딘: 발할라 라이징 QA 자동화 - 스모크 테스트

모바일 MMORPG QA 경력을 바탕으로, 오딘: 발할라 라이징 PC 클라이언트를 대상으로
"실행 → 스플래시 통과 → 캐릭터 선택 화면 진입"을 자동으로 검증하는 스모크 테스트 시스템입니다.

## 배경

- 실제 게임 QA 실무 경험을 살려, 반복적으로 수행하던 스모크 테스트를 자동화
- 안드로이드 단말기 없이 PC 클라이언트 기반으로 구현
- 오딘은 로그인을 웹사이트에서 먼저 처리하고 클라이언트를 실행하는 구조라, 클라이언트 내부에는
  별도 로그인 화면이 없음 — 웹 로그인 자동화는 계정 비밀번호 노출 위험이 있어 범위에서 제외하고,
  클라이언트가 정상 실행되는지(스플래시 → 캐릭터 선택 화면)를 검증 대상으로 삼음
- 캐릭터 선택 후 인게임 진입은 계정마다 보유 캐릭터가 달라 재현성이 떨어져 Phase 1 범위 밖으로 둠

## 기술 스택

- Python 3.12 (Airtest가 의존하는 numpy<2.0이 3.13용 사전빌드 wheel을 제공하지 않아 3.12 사용)
- Airtest (넷이즈의 게임 자동화 오픈소스 프레임워크) — 이미지 템플릿 매칭 기반 화면 인식
- AirtestIDE — 템플릿 이미지 캡처 및 연결 테스트용 GUI 툴
- 직접 구현한 HTML 리포트 생성기 (`report.py`) — Airtest 기본 리포트 대신 가독성 있는 자체 리포트 제작

## 동작 방식

1. 오딘 PC 클라이언트 창에 연결
2. 스플래시 화면 인식 및 통과 (로딩 중 클릭이 씹히는 경우를 대비해, 화면이 넘어갈 때까지 반복 클릭)
3. 캐릭터 선택 화면 진입 여부를 고정 UI 요소(화면 제목) 인식으로 검증
4. 각 단계마다 오딘 창을 맨 앞으로 가져온 뒤 스크린샷 촬영
5. 성공/실패와 무관하게 직접 만든 리포터(`report.py`)로 HTML 리포트 자동 생성

## 실행 방법

오딘이 안티치트 때문에 관리자 권한으로 실행되므로, 아래 명령어도 **관리자 권한 터미널**에서
실행해야 합니다 (그렇지 않으면 Windows 권한 격리로 마우스 클릭이 조용히 실패함).

\`\`\`
venv\\Scripts\\activate
cd smoke_test.air
python smoke_test.py
\`\`\`

실행 후 `smoke_test.air/log/report.html`을 열면 결과를 확인할 수 있습니다.

## 설계 문서

전체 설계 배경과 의사결정 과정은 [docs/superpowers/specs/2026-09-15-odin-qa-automation-design.md](docs/superpowers/specs/2026-09-15-odin-qa-automation-design.md) 참고.

## 향후 확장 계획

- 반복 작업(일일퀘스트, 자동전투) 검증 자동화
- UI 회귀 테스트 (이미지 비교 기반)
- 다른 게임/플랫폼으로 확장
```

- [ ] **Step 2: Commit**

```
git add README.md
git commit -m "docs: add project README"
```
