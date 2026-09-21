# -*- encoding=utf8 -*-
"""오딘 화면 전체를 log/<이름>.png 로 저장한다. 템플릿을 만들 때 이 파일에서 잘라 쓴다.

    python tools/capture.py            → log/capture.png
    python tools/capture.py gift_open  → log/gift_open.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import client  # noqa: E402

name = sys.argv[1] if len(sys.argv) > 1 else "capture"
client.connect(clear_log=False)  # 이전 캡처를 지우지 않는다
filename = client.snap(name)
print(os.path.join(client.LOG_DIR, filename))
