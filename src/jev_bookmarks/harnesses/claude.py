"""Claude Code: ユーザーのスキルは ~/.claude/skills から読む。"""

import shutil
from pathlib import Path

NAME = "claude"
LABEL = "Claude Code"
NOTES = """## Claude Codeでの実行

- `run` はページ選択とブラウザ操作で数分かかることがある。
  Bashツールの `timeout` を600000（10分）にして一回で待つ。バックグラウンド実行にしない。
"""


def detect() -> bool:
    return shutil.which("claude") is not None or (Path.home() / ".claude").is_dir()


def skill_dir() -> Path:
    return Path.home() / ".claude" / "skills" / "jev-bookmarks"
