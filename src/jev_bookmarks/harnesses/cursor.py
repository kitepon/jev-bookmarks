"""Cursor（エディターとcursor-agent）: ユーザーのスキルは ~/.cursor/skills から読む。"""

import shutil
from pathlib import Path

NAME = "cursor"
LABEL = "Cursor"
NOTES = """## Cursorでの実行

- `run` はネットワークとChromeを使う。ターミナルがサンドボックス内で動いている時は、サンドボックスの外での実行を求める。
- ページ選択とブラウザ操作で数分かかることがある。途中で打ち切らず、終了まで待つ。
"""


def detect() -> bool:
    return shutil.which("cursor-agent") is not None or (Path.home() / ".cursor").is_dir()


def skill_dir() -> Path:
    return Path.home() / ".cursor" / "skills" / "jev-bookmarks"
