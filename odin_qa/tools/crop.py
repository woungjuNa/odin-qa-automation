# -*- encoding=utf8 -*-
"""캡처 이미지에서 사각형 영역을 잘라 템플릿으로 저장한다.

    python tools/crop.py log/capture.png X Y W H templates/top_menu/gift_icon.png

X, Y는 왼쪽 위 모서리, W, H는 너비/높이(픽셀). 좌표는 캡처 이미지를 그림판으로 열어
마우스를 올리면 왼쪽 아래에 표시된다.
"""
import sys

from PIL import Image

src, x, y, w, h, dst = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
Image.open(src).crop((x, y, x + w, y + h)).save(dst)
print(f"{dst} ({w}x{h})")
