from pathlib import Path

import pytest

from jev_bookmarks import harnesses
from jev_bookmarks.platforms import linux, macos, windows

OS_CONTRACT = {
    "data_dir", "manifest_dir", "host_executable", "register_host", "prepare_process", "serve", "ask", "available",
}


def test_every_os_adapter_fills_the_same_contract():
    for module in (linux, macos, windows):
        missing = {name for name in OS_CONTRACT if not callable(getattr(module, name, None))}
        assert not missing, (module.__name__, missing)


def test_every_harness_adapter_fills_the_same_contract():
    assert set(harnesses.ALL) == {"claude", "codex", "cursor", "grok"}
    for harness in harnesses.ALL.values():
        assert harness.NOTES.startswith("## ")
        assert callable(harness.detect) and callable(harness.skill_dir)


@pytest.fixture
def home(tmp_path: Path, monkeypatch) -> Path:
    for name in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(name, str(tmp_path))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    return tmp_path


def test_skill_install_is_repeatable_and_per_harness(home: Path):
    first = harnesses.install(list(harnesses.ALL))
    assert [item["changed"] for item in first] == [True] * 4
    assert [item["changed"] for item in harnesses.install(list(harnesses.ALL))] == [False] * 4
    claude = (home / ".claude" / "skills" / "jev-bookmarks" / "SKILL.md").read_text(encoding="utf-8")
    codex = (home / ".codex" / "skills" / "jev-bookmarks" / "SKILL.md").read_text(encoding="utf-8")
    assert claude.startswith("---\nname: jev-bookmarks\n")
    assert "## Claude Codeでの実行" in claude and "## Codexでの実行" not in claude
    assert "## Codexでの実行" in codex and "{harness_notes}" not in codex
    assert all(entry["installed"] and entry["current"] for entry in harnesses.status().values())


def test_skill_install_keeps_a_foreign_skill(home: Path):
    foreign = home / ".grok" / "skills" / "jev-bookmarks" / "SKILL.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("自作のスキル\n", encoding="utf-8")
    with pytest.raises(harnesses.HarnessError, match="別の jev-bookmarks スキル"):
        harnesses.install(["grok"])
    assert foreign.read_text(encoding="utf-8") == "自作のスキル\n"
    with pytest.raises(harnesses.HarnessError, match="未対応のハーネス"):
        harnesses.install(["vim"])
