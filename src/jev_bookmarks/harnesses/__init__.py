"""ハーネスへの適合。各ハーネスに `jev-bookmarks run` の呼び方をスキルとして入れる。

各ハーネスのモジュールは ``NAME``・``LABEL``・``NOTES``（そのハーネスでの実行上の注意）と
``detect()``・``skill_dir()`` を持つ。スキル本文の共通部分は ``skill.md`` にある。
"""

import os
import tempfile
from pathlib import Path
from types import ModuleType

from . import claude, codex, cursor, grok

ALL: dict[str, ModuleType] = {module.NAME: module for module in (claude, codex, cursor, grok)}
MARKER = "<!-- jev-bookmarks:managed -->"


class HarnessError(RuntimeError):
    pass


def skill_text(harness: ModuleType) -> str:
    template = (Path(__file__).with_name("skill.md")).read_text(encoding="utf-8")
    return template.replace("{harness_notes}", harness.NOTES.strip()) + "\n"


def _skill_file(harness: ModuleType) -> Path:
    return harness.skill_dir() / "SKILL.md"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".SKILL-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def install(names: list[str] | None = None) -> list[dict]:
    """指定のハーネス（省略時は検出できた全部）にスキルを入れる。何度実行しても同じ結果になる。"""
    if names:
        unknown = [name for name in names if name not in ALL]
        if unknown:
            raise HarnessError(f"未対応のハーネスです: {', '.join(unknown)}（{', '.join(ALL)} から選ぶ）")
        targets = [ALL[name] for name in names]
    else:
        targets = [harness for harness in ALL.values() if harness.detect()]
        if not targets:
            raise HarnessError("Claude Code・Codex・Cursor・Grok Buildのどれも見つかりません")
    results = []
    for harness in targets:
        path = _skill_file(harness)
        text = skill_text(harness)
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current is not None and MARKER not in current:
            raise HarnessError(f"{path} は別の jev-bookmarks スキルです。変更しませんでした")
        if current != text:
            _write(path, text)
        results.append({"harness": harness.NAME, "skill": str(path), "changed": current != text})
    return results


def status() -> dict:
    report = {}
    for harness in ALL.values():
        path = _skill_file(harness)
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        report[harness.NAME] = {
            "detected": harness.detect(),
            "skill": str(path),
            "installed": current is not None and MARKER in current,
            "current": current == skill_text(harness),
        }
    return report
