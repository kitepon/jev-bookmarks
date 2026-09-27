"""Codex: ユーザーのスキルは $CODEX_HOME/skills（既定は ~/.codex/skills）から読む。"""

import os
import shutil
from pathlib import Path

NAME = "codex"
LABEL = "Codex"
NOTES = """## Codexでの実行

- `run` はTypeSafeとモデルのAPIへ通信し、作業ツリーの外にある履歴接続（ソケットや名前付きパイプ）とChromeを使う。
  既定のサンドボックスでは失敗するので、サンドボックスの外での実行（昇格した権限）を求めて実行する。
- ページ選択とブラウザ操作で数分かかることがある。コマンドのタイムアウトを10分（600000ミリ秒）にする。
"""


def _home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def detect() -> bool:
    return shutil.which("codex") is not None or _home().is_dir()


def skill_dir() -> Path:
    return _home() / "skills" / "jev-bookmarks"
