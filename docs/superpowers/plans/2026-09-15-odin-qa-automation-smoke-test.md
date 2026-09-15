# 오딘 QA 자동화 스모크 테스트 (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 오딘: 발할라 라이징 PC 클라이언트에 대해 "실행 → 로그인 → 메인화면 진입"을 자동으로 검증하고 HTML 리포트를 생성하는 스모크 테스트 스크립트를 만든다.

**Architecture:** Airtest 프레임워크로 오딘 PC 클라이언트 창에 연결하고, 이미지 템플릿 매칭으로 화면 요소(스플래시 로고, 로그인 버튼, 메인 메뉴 아이콘)를 인식·클릭한다. Airtest의 `.air` 프로젝트 규칙(`<name>.air/<name>.py`)을 따라 실행 로그와 스크린샷이 자동 기록되고, `airtest report` 명령으로 HTML 리포트를 생성한다.

**Tech Stack:** Python 3.x, Airtest (pip 패키지), pywin32, VS Code, AirtestIDE (템플릿 이미지 캡처용 GUI 툴)

**Spec:** [docs/superpowers/specs/2026-09-15-odin-qa-automation-design.md](../specs/2026-09-15-odin-qa-automation-design.md)

## Global Constraints

- 대상: 오딘: 발할라 라이징 PC 클라이언트 (Windows, 언리얼 엔진 렌더링 화면)
- 자동화 프레임워크: Airtest (이미지 템플릿 매칭 방식)
- 계정 정보(ID/PW)는 `config.py`에만 두고, `.gitignore`로 git 커밋 제외
- 오딘 클라이언트는 **창모드(windowed) 또는 테두리 없는 창모드**로 실행 — 전체화면 exclusive 모드는 Windows 화면 캡처 API로 스크린샷이 안 찍힐 수 있음
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
- Create: `config.example.py`

**Interfaces:**
- Consumes: Task 1의 Python 환경
- Produces: `venv` 가상환경, 설치된 `airtest`/`pywin32` 패키지, git에 올라가지 않는 `config.py` 규칙 — 이후 모든 코드 작업이 이 가상환경 위에서 실행됨

- [ ] **Step 1: 가상환경 생성**

VS Code에서 `File > Open Folder`로 `C:\Users\dndwn\Desktop\QA_AI` 폴더 열기. 통합 터미널에서:

```
python -m venv venv
```

- [ ] **Step 2: 가상환경 활성화**

```
venv\Scripts\activate
```

터미널 프롬프트 앞에 `(venv)`가 표시되면 성공.

- [ ] **Step 3: Airtest 및 관련 패키지 설치**

```
pip install airtest pywin32 airtest-selenium
```

(`airtest-selenium`은 불필요하면 제외 가능하지만, 최신 airtest 패키지가 일부 win 플랫폼 의존성을 함께 요구하는 경우가 있어 포함. 설치 중 에러가 나면 에러 메시지를 확인해 개별 패키지명으로 재시도)

실제로 필요한 최소 설치는:

```
pip install airtest pywin32
```

- [ ] **Step 4: 설치 확인**

```
python -c "import airtest; print(airtest.__version__)"
```

기대 결과: 버전 문자열 출력 (예: `1.3.3`). ImportError가 나면 Step 3의 가상환경이 활성화된 상태인지 확인.

- [ ] **Step 5: requirements.txt 생성**

```
pip freeze > requirements.txt
```

- [ ] **Step 6: .gitignore 작성**

`.gitignore` 파일 생성:

```
venv/
config.py
smoke_test.air/log/
smoke_test.air/report.html
__pycache__/
*.pyc
```

- [ ] **Step 7: config.example.py 작성**

```python
# config.example.py
# 이 파일을 복사해서 config.py로 저장하고, 실제 계정 정보를 입력하세요.
# config.py는 .gitignore에 등록되어 있어 git에 올라가지 않습니다.

ODIN_ACCOUNT_ID = "your_id_here"
ODIN_ACCOUNT_PW = "your_password_here"
```

- [ ] **Step 8: 실제 config.py 생성**

`config.example.py`를 복사해서 `config.py`로 저장하고, 본인의 실제 오딘 계정 정보로 값을 채워넣기.

- [ ] **Step 9: Commit**

```
git add requirements.txt .gitignore config.example.py
git commit -m "chore: set up Python venv and Airtest dependencies"
```

(`config.py`는 `.gitignore`에 있으므로 `git add`해도 반영되지 않음 — `git status`로 `config.py`가 커밋 대상에 안 뜨는지 확인)

---

## Task 3: AirtestIDE로 오딘 연결 확인 + 템플릿 이미지 캡처

**Files:**
- Create: `smoke_test.air/splash_logo.png`
- Create: `smoke_test.air/login_button.png`
- Create: `smoke_test.air/main_menu_icon.png`

**Interfaces:**
- Consumes: 없음 (독립적인 GUI 작업)
- Produces: Task 4의 스크립트가 참조할 템플릿 이미지 3개, 오딘 창의 정확한 제목(title) 문자열

- [ ] **Step 1: AirtestIDE 다운로드**

https://airtest.netease.com/ 접속 → AirtestIDE 다운로드 (Windows용 zip). 압축을 원하는 위치(예: `C:\Tools\AirtestIDE`)에 풀기. 설치 프로그램이 아니라 압축 해제 후 `AirtestIDE.exe` 실행하는 포터블 프로그램.

- [ ] **Step 2: 오딘 클라이언트를 창모드로 실행**

오딘 PC 클라이언트 실행 → 설정에서 화면 모드를 **창모드** 또는 **테두리 없는 창모드**로 변경. (전체화면 exclusive 모드는 다음 단계 캡처가 실패할 수 있음)

- [ ] **Step 3: AirtestIDE에서 오딘 창 연결**

AirtestIDE 실행 → 상단 디바이스 연결 아이콘 클릭 → "Windows" 탭 선택 → 실행 중인 창 목록에서 오딘 창 선택 → Connect.

연결되면 오른쪽 패널에 오딘 게임 화면이 실시간으로 보임. **이때 목록에 표시된 오딘 창의 정확한 제목 문자열을 메모**해두기 (Task 4에서 필요).

- [ ] **Step 4: .air 프로젝트 생성**

AirtestIDE 메뉴 `File > New` → 파일명 `smoke_test`, 저장 위치 `C:\Users\dndwn\Desktop\QA_AI`로 지정 → `smoke_test.air` 폴더가 생성됨.

- [ ] **Step 5: 스플래시 로고 템플릿 캡처**

오딘을 실행해서 스플래시 화면이 뜬 상태로 대기. AirtestIDE 왼쪽 "Common" 패널의 카메라(Snapshot) 아이콘 클릭 → 오른쪽 화면 미리보기에서 로고 또는 "터치하여 계속" 같은 고유 UI 요소 영역을 마우스로 드래그해서 선택 → 저장 파일명 `splash_logo.png`로 저장. (반드시 `smoke_test.air` 폴더 안에 저장되는지 확인)

- [ ] **Step 6: 로그인 버튼 템플릿 캡처**

로그인 화면까지 진행 → 같은 방식으로 로그인 버튼 영역 캡처 → `login_button.png`로 저장.

- [ ] **Step 7: 메인 메뉴 아이콘 템플릿 캡처**

로그인 성공 후 메인 화면 진입 → 항상 고정 위치에 있는 메뉴 아이콘(예: 하단 메뉴바의 특정 아이콘) 영역 캡처 → `main_menu_icon.png`로 저장.

- [ ] **Step 8: 확인**

파일 탐색기에서 `smoke_test.air` 폴더를 열어 `splash_logo.png`, `login_button.png`, `main_menu_icon.png` 3개 파일이 있는지 확인.

- [ ] **Step 9: Commit**

```
git add smoke_test.air/splash_logo.png smoke_test.air/login_button.png smoke_test.air/main_menu_icon.png
git commit -m "feat: capture template images for smoke test"
```

---

## Task 4: 스모크 테스트 스크립트 작성

**Files:**
- Create: `smoke_test.air/smoke_test.py`

**Interfaces:**
- Consumes: Task 3의 템플릿 이미지 3개 (`smoke_test.air/splash_logo.png`, `login_button.png`, `main_menu_icon.png`), Task 2의 `config.py` (`ODIN_ACCOUNT_ID`, `ODIN_ACCOUNT_PW`)
- Produces: `run_smoke_test()` 함수 — 실행 시 성공하면 콘솔에 `[PASS]` 출력, 실패 시 예외 발생. `smoke_test.air/log/` 폴더에 실행 로그와 스크린샷 기록

- [ ] **Step 1: 연결 코드 작성 (스크립트 뼈대)**

`smoke_test.air/smoke_test.py` 생성:

```python
from airtest.core.api import *

# Task 3에서 메모해둔 오딘 창 제목으로 필요시 수정
WINDOW_TITLE_RE = r".*[Oo]din.*"

SPLASH_LOGO = Template(r"splash_logo.png")
LOGIN_BUTTON = Template(r"login_button.png")
MAIN_MENU_ICON = Template(r"main_menu_icon.png")


def run_smoke_test():
    auto_setup(__file__, logdir=True, devices=[f"Windows:///?title_re={WINDOW_TITLE_RE}"])
    print("[STEP] 오딘 창에 연결됨")


if __name__ == "__main__":
    run_smoke_test()
```

- [ ] **Step 2: 실행해서 연결만 확인**

오딘 클라이언트를 실행해둔 상태에서, VS Code 터미널(가상환경 활성화된 상태)에서:

```
cd smoke_test.air
python smoke_test.py
```

기대 결과: 콘솔에 `[STEP] 오딘 창에 연결됨` 출력. `TargetNotFoundError` 또는 연결 관련 예외가 나면 `WINDOW_TITLE_RE`를 Task 3에서 메모한 실제 창 제목에 맞게 수정.

- [ ] **Step 3: 스플래시 통과 로직 추가**

`run_smoke_test()` 함수를 아래로 교체:

```python
def run_smoke_test():
    auto_setup(__file__, logdir=True, devices=[f"Windows:///?title_re={WINDOW_TITLE_RE}"])
    print("[STEP] 오딘 창에 연결됨")

    print("[STEP] 스플래시 화면 대기 중...")
    wait(SPLASH_LOGO, timeout=15)
    touch(SPLASH_LOGO)
    print("[STEP] 스플래시 통과 완료")
```

- [ ] **Step 4: 실행해서 스플래시 단계까지 확인**

오딘을 스플래시 화면 상태로 재실행한 뒤:

```
python smoke_test.py
```

기대 결과: `[STEP] 스플래시 통과 완료`까지 출력되고 실제로 화면이 클릭되어 다음 화면으로 넘어감. `wait` 단계에서 타임아웃 예외가 나면 `splash_logo.png` 템플릿이 현재 화면과 맞는지 AirtestIDE에서 다시 확인.

- [ ] **Step 5: 로그인 + 메인화면 진입 로직 추가**

`smoke_test.py` 맨 위에 config import 추가하고, 함수를 최종 버전으로 교체:

```python
from airtest.core.api import *
from config import ODIN_ACCOUNT_ID, ODIN_ACCOUNT_PW

WINDOW_TITLE_RE = r".*[Oo]din.*"

SPLASH_LOGO = Template(r"splash_logo.png")
LOGIN_BUTTON = Template(r"login_button.png")
MAIN_MENU_ICON = Template(r"main_menu_icon.png")


def run_smoke_test():
    auto_setup(__file__, logdir=True, devices=[f"Windows:///?title_re={WINDOW_TITLE_RE}"])
    print("[STEP] 오딘 창에 연결됨")

    print("[STEP] 스플래시 화면 대기 중...")
    wait(SPLASH_LOGO, timeout=15)
    touch(SPLASH_LOGO)
    print("[STEP] 스플래시 통과 완료")

    print("[STEP] 로그인 버튼 대기 중...")
    wait(LOGIN_BUTTON, timeout=15)
    touch(LOGIN_BUTTON)
    print(f"[STEP] 로그인 시도 (계정: {ODIN_ACCOUNT_ID})")

    print("[STEP] 메인 화면 진입 대기 중...")
    wait(MAIN_MENU_ICON, timeout=30)
    print("[PASS] 스모크 테스트 성공: 메인 화면 진입 확인됨")


if __name__ == "__main__":
    run_smoke_test()
```

(참고: 오딘의 로그인 화면 UI에 따라 ID/PW 입력 필드가 별도로 있다면, `text(ODIN_ACCOUNT_ID)` 같은 Airtest 함수로 텍스트 입력을 추가해야 할 수 있음 — 실제 로그인 화면을 보면서 Task 6에서 조정)

- [ ] **Step 6: 전체 실행 확인**

오딘을 처음 상태(스플래시)로 재실행 후:

```
python smoke_test.py
```

기대 결과: `[PASS] 스모크 테스트 성공: 메인 화면 진입 확인됨`까지 콘솔에 출력됨.

- [ ] **Step 7: Commit**

```
cd ..
git add smoke_test.air/smoke_test.py
git commit -m "feat: implement smoke test script (splash -> login -> main screen)"
```

---

## Task 5: 실패 상황 처리 + HTML 리포트 생성 확인

**Files:**
- Modify: `smoke_test.air/smoke_test.py`

**Interfaces:**
- Consumes: Task 4의 `run_smoke_test()`
- Produces: 실패 시에도 스크린샷이 남는 에러 처리, `smoke_test.air/log/` 기반 `report.html`

- [ ] **Step 1: 실패 시 스크린샷 저장 로직 추가**

`smoke_test.py`의 실행부를 아래로 교체:

```python
if __name__ == "__main__":
    try:
        run_smoke_test()
    except Exception as e:
        print(f"[FAIL] 스모크 테스트 실패: {e}")
        snapshot(filename="failure.png", msg="테스트 실패 시점 화면")
        raise
```

- [ ] **Step 2: 의도적으로 실패시켜 동작 확인**

`SPLASH_LOGO = Template(r"splash_logo.png")` 줄을 일시적으로 `SPLASH_LOGO = Template(r"nonexistent.png")`로 바꾸고 실행:

```
python smoke_test.py
```

기대 결과: `[FAIL] 스모크 테스트 실패: ...` 출력되고, `smoke_test.air/log/` 폴더 안에 `failure.png`가 저장됨.

- [ ] **Step 3: 원복**

`SPLASH_LOGO` 줄을 다시 `Template(r"splash_logo.png")`로 되돌리기.

- [ ] **Step 4: 정상 실행으로 로그 남기기**

오딘을 처음 상태로 재실행 후:

```
python smoke_test.py
```

성공까지 확인.

- [ ] **Step 5: HTML 리포트 생성**

```
airtest report smoke_test.py --log_root log --outfile log/report.html
```

- [ ] **Step 6: 리포트 확인**

파일 탐색기에서 `smoke_test.air/log/report.html`을 더블클릭해 브라우저로 열기. 단계별 스크린샷과 성공/실패 로그가 표시되는지 확인.

- [ ] **Step 7: Commit**

```
cd ..
git add smoke_test.air/smoke_test.py
git commit -m "feat: add failure screenshot handling to smoke test"
```

(`log/`, `report.html`은 `.gitignore`에 있어 커밋되지 않음 — 실행할 때마다 로컬에서 새로 생성됨)

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
"실행 → 로그인 → 메인화면 진입"을 자동으로 검증하는 스모크 테스트 시스템입니다.

## 배경

- 실제 게임 QA 실무 경험을 살려, 반복적으로 수행하던 스모크 테스트를 자동화
- 안드로이드 단말기 없이 PC 클라이언트 기반으로 구현

## 기술 스택

- Python 3.x
- Airtest (넷이즈의 게임 자동화 오픈소스 프레임워크) — 이미지 템플릿 매칭 기반 화면 인식
- AirtestIDE — 템플릿 이미지 캡처용 GUI 툴

## 동작 방식

1. 오딘 PC 클라이언트 창에 연결
2. 스플래시 화면 인식 및 통과
3. 로그인 화면 인식 및 로그인 시도
4. 메인 화면 진입 여부를 UI 요소 인식으로 검증
5. 실행 결과를 HTML 리포트로 자동 생성 (단계별 스크린샷 포함)

## 실행 방법

\`\`\`
venv\\Scripts\\activate
cd smoke_test.air
python smoke_test.py
airtest report smoke_test.py --log_root log --outfile log/report.html
\`\`\`

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
