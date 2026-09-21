# sheets_config.example.py
# 이 파일을 sheets_config.py로 복사하고, Apps Script 배포로 받은 웹 앱 URL을 넣으세요.
# sheets_config.py는 .gitignore에 등록되어 있어 git에 올라가지 않습니다.

WEBHOOK_URL = "https://script.google.com/macros/s/여기에_배포된_ID/exec"

# 선택: Apps Script 쪽 TOKEN과 같은 값을 넣으면, 토큰이 일치하는 요청만 시트에 기록됩니다.
# 양쪽 모두 비워두면 검사하지 않습니다.
WEBHOOK_TOKEN = ""
