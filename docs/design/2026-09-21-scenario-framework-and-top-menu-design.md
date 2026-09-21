# 시나리오 확장 구조와 상단 메뉴 테스트 설계

## 목적

스모크 테스트 하나뿐이던 프로젝트를 여러 시나리오를 담을 수 있는 구조로 바꾸고, 그 위에 두 번째
시나리오인 **상단 메뉴 진입/복귀 테스트**를 올립니다. 앞으로 설정 메뉴, 기타 인게임 기능 테스트가
같은 방식으로 추가됩니다.

## 지금의 문제

`smoke_test.py` 한 파일에 성격이 다른 코드가 함께 있습니다.

| 덩어리 | 성격 |
|---|---|
| 창 찾기·연결·전면화·스크린샷 | 어떤 테스트든 똑같이 필요 |
| 스플래시 → 캐릭터 선택 → 게임하기 → 인게임 | 스모크의 검증 대상이자, 다른 테스트의 사전 조건 |
| 리포터·시트 전송·오류 한글화 | 어떤 테스트든 똑같이 필요 |
| `__main__` 실행 하네스 | 어떤 테스트든 똑같이 필요 |

`reporter`가 모듈 전역이고 제목이 스모크 전용이라, 이 상태로는 두 번째 시나리오를 만들 수 없습니다.

## 검토한 방식

- **스모크에 이어 붙이기** — 스모크가 끝없이 길어지고, 중간 실패 시 뒤를 못 봅니다. 메뉴만 따로
  돌릴 수도 없습니다. "가장 빠르게 실행 여부만 거른다"는 스모크의 정의가 무너집니다.
- **완전히 별도 스크립트** — 진입 로직을 복사하거나, 사람이 인게임까지 넣어두는 수동 사전 조건에
  기대게 됩니다. 후자는 "누가 언제 돌려도 같은 기준"이라는 재현성을 깨뜨립니다.
- **공통 모듈 + 시나리오 분리 + 단일 진입점 (채택)** — 진입 로직을 한 곳에 두고, 스모크는 그것을
  *검증*하고 메뉴 테스트는 *사전 조건*으로 씁니다. 실행 하네스는 하나만 둡니다.

## 구조

```
odin_qa/                       # smoke_test.air 에서 이름 변경
├── run.py                     # 진입점: python run.py smoke | top_menu | all
├── core/
│   ├── client.py              # 창 찾기·연결·전면화·스크린샷·템플릿 로더·대기 헬퍼
│   ├── flows.py               # pass_splash(), enter_game(), ensure_ingame(), open_menu(), close_menu()
│   ├── context.py             # Context: 시나리오 1회 실행의 상태 (리포터, 단계, 케이스, 결과)
│   ├── reporter.py            # 기존 report.py
│   ├── sheets.py              # 기존 _send_to_sheet
│   └── errors.py              # TestFailure(stage, message), describe_error()
├── scenarios/
│   ├── smoke.py               # TITLE, run(ctx)
│   └── top_menu.py            # TITLE, MENUS, run(ctx)
├── templates/
│   ├── common/                # splash_logo, character_select_title, play_button, ingame_hud, ingame_topmenu
│   └── top_menu/              # <메뉴>_icon.png, <메뉴>_opened.png
├── sheets_config.example.py
└── log/                       # 실행 시 자동 생성
```

`.air` 폴더명은 `airtest run` CLI로 리포트를 만들 때만 필요한 규칙입니다. 직접 만든 리포터를 쓰고
`python`으로 실행하므로 이 제약은 없어졌고, 여러 시나리오가 들어가는 폴더에 `smoke_test.air`라는
이름은 오해를 만들어 `odin_qa/`로 바꿉니다.

## 각 층의 역할

**시나리오**는 "무엇을 검증하는가"만 적습니다. 연결, 스크린샷, 리포트, 시트는 전혀 모릅니다.

```python
# scenarios/top_menu.py
TITLE = "상단 메뉴: 각 메뉴 진입 및 복귀"

MENUS = [
    # (이름,     클릭할 아이콘,                  열렸는지 판정할 고정 요소)
    ("이벤트",  T("top_menu/event_icon"),   T("top_menu/event_opened")),
    ("선물",    T("top_menu/gift_icon"),    T("top_menu/gift_opened")),
    ("BM 상점", T("top_menu/shop_icon"),    T("top_menu/shop_opened")),
    ("가방",    T("top_menu/bag_icon"),     T("top_menu/bag_opened")),
    ("메뉴",    T("top_menu/menu_icon"),    T("top_menu/menu_opened")),
]

def run(ctx):
    flows.ensure_ingame(ctx)
    for name, icon, opened in MENUS:
        with ctx.case(name):
            flows.open_menu(ctx, name, icon, opened)
            flows.close_menu(ctx, name)
```

메뉴가 늘어나면 `MENUS` 표에 한 줄과 템플릿 두 장을 추가합니다. 코드는 바뀌지 않습니다.

**플로우**는 게임 화면을 다루는 재사용 단위입니다. 스모크의 `pass_splash`, `enter_game`은 지금
`run_smoke_test` 안의 코드를 그대로 옮긴 것이고, 새로 추가되는 것은 셋입니다.

- `ensure_ingame(ctx)` — 이미 인게임(레벨 표시 + 상단 메뉴 둘 다 보임)이면 아무것도 안 함.
  스플래시면 `pass_splash` → `enter_game`, 캐릭터 선택 화면이면 `enter_game`. 어느 화면도 아니면
  `TestFailure("precondition")`.
- `open_menu(ctx, name, icon, opened)` — 아이콘을 클릭하고 `opened` 템플릿이 나타날 때까지 대기.
  아이콘 자체를 못 찾으면 `action`, 클릭 후 `opened`가 안 나오면 `verify` 실패.
- `close_menu(ctx, name)` — ESC를 보내고 레벨 표시 + 상단 메뉴가 다시 보일 때까지 대기. 안 돌아오면
  `verify` 실패. (오딘 메뉴는 ESC와 상단 뒤로가기 버튼 둘 다로 닫히는 것을 확인함. ESC가 안 먹는
  메뉴가 나오면 그 메뉴만 뒤로가기 템플릿을 추가로 두는 것으로 대응.)

**Context**는 시나리오 1회 실행의 상태입니다. `ctx.step()`으로 단계를 기록하고, `ctx.snap()`으로
스크린샷을 찍고, `ctx.case(name)`으로 항목 하나의 성공/실패를 감쌉니다. `case` 안에서 예외가 나면
그 항목만 FAIL로 기록하고 다음 항목으로 진행합니다. 시나리오 전체 결과는 모든 항목이 통과했을 때만
PASS입니다.

**run.py**는 유일한 진입점입니다. 창 확인 → 연결 → 시나리오 순서대로 실행 → 시나리오마다 리포트
1개 + 시트 1행 → 하나라도 실패하면 종료 코드 1. `all`에서 스모크가 실패하면 뒤 시나리오는 실행하지
않고 `precondition` 실패로 기록합니다.

## 실패 단계 구분

```python
class TestFailure(Exception):
    def __init__(self, stage, message): ...   # stage: setup | precondition | action | verify
```

| stage | 뜻 | 예 |
|---|---|---|
| `setup` | 테스트를 시작할 수 없음 | 오딘 창 없음, 중복 실행 |
| `precondition` | 시나리오의 전제가 안 갖춰짐 | 메뉴 테스트인데 인게임 진입 실패 |
| `action` | 조작이 안 됨 | 아이콘을 못 찾음 |
| `verify` | 조작은 됐는데 기대한 화면이 아님 | 클릭 후 메뉴 화면이 안 보임, ESC 후 HUD 복귀 안 됨 |

라이브러리 예외는 지금처럼 `describe_error()`가 한글로 바꾸고, stage는 `setup`으로 분류합니다.

## 리포트와 시트

- HTML 리포트: 시나리오마다 `log/<시나리오>_report.html`. 항목별 결과가 있는 시나리오는 항목 하나가
  카드 하나.
- Google Sheets: 컬럼을 `실행 시각 | 시나리오 | 결과 | 소요시간(초) | 실패 단계 | 실패 사유`로
  확장. 여러 시나리오가 한 시트에 쌓이므로 시나리오 컬럼이 필요하고, 실패 단계는 위 stage를 그대로
  넣습니다. 항목별 실패는 실패 사유에 `선물: verify — 메뉴 화면이 10초 안에 나타나지 않음`처럼
  항목 이름을 앞에 붙여 한 칸에 모읍니다. Apps Script 재배포가 필요합니다.

## 템플릿 원칙 (기존과 동일)

- 계정·위치·시간에 따라 바뀌지 않는 요소만 씁니다. 메뉴의 "열림" 판정은 그 메뉴 화면의 제목이나
  고정 탭처럼 내용과 무관한 부분으로 잡습니다. 이벤트 배너, 상점 상품 이미지 같은 건 쓰지 않습니다.
- 빨간 알림 점(N)이 붙는 아이콘은 점이 없는 영역만 남기도록 잘라, 알림 유무에 따라 매칭이 흔들리지
  않게 합니다.

## 진행 순서

1. **리팩터링만** — `smoke_test.py`를 위 구조로 옮기고 `python run.py smoke`가 지금과 동일하게
   동작하는지 확인. 이 단계는 코드 이동만 하고 동작을 바꾸지 않습니다.
2. `ensure_ingame`, `TestFailure(stage)`, `ctx.case()`, 시트 컬럼 확장.
3. 상단 메뉴 5개 템플릿 캡처 → `top_menu.py`.
4. README, 포트폴리오 페이지, 기존 설계 문서의 파일 구조 갱신.

## 범위 밖

- 햄버거 메뉴 안의 그리드(약 20개 항목) — 구조가 안정된 뒤 `MENUS` 표에 추가하는 것으로 확장.
- pytest 도입 — 시나리오가 4~5개 되고 구조가 안정된 뒤 검토. 위 구조의 `run(ctx)`는 그대로 pytest
  테스트로 감쌀 수 있게 되어 있습니다.
