"""Grok Build: ユーザーのスキルは ~/.grok/skills から読む。"""

import shutil
from pathlib import Path

NAME = "grok"
LABEL = "Grok Build"
NOTES = """## Grok Buildでの実行

- ページ選択とブラウザ操作で数分かかることがある。コマンドのタイムアウトを10分にして、終了まで待つ。
"""


def detect() -> bool:
    return shutil.which("grok") is not None or (Path.home() / ".grok").is_dir()


def skill_dir() -> Path:
    return Path.home() / ".grok" / "skills" / "jev-bookmarks"
