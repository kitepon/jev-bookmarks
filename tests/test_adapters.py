import os
from pathlib import Path

import pytest

from jev_bookmarks import harnesses
from jev_bookmarks.platforms import linux, macos, windows

OS_CONTRACT = {
    "data_dir",
    "manifest_dir",
    "legacy_manifest_dirs",
    "host_executable",
    "register_host",
    "prepare_process",
    "browser_runtime_dir",
    "chrome_executable",
    "launch_chrome",
    "serve",
    "ask",
    "available",
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


def test_native_host_install_drops_the_normal_chrome_registration(tmp_path: Path, monkeypatch):
    from jev_bookmarks import install

    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / f"{install.HOST_NAME}.json").write_text("{}", encoding="utf-8")
    (legacy / "other.host.json").write_text("{}", encoding="utf-8")
    registered = []

    class Platform:
        manifest_dir = staticmethod(lambda: tmp_path / "profile" / "NativeMessagingHosts")
        legacy_manifest_dirs = staticmethod(lambda: [legacy])
        host_executable = staticmethod(lambda root: Path(install.__file__))
        register_host = staticmethod(registered.append)

    monkeypatch.setattr(install.platforms, "current", lambda: Platform)
    target = install.install_native_host()
    assert registered == [target]
    assert not (legacy / f"{install.HOST_NAME}.json").exists()
    assert (legacy / "other.host.json").exists()


@pytest.mark.skipif(os.name == "nt", reason="Linuxの起動経路はPOSIXの端末で確かめる")
def test_linux_chrome_opens_in_the_logged_in_desktop_session(monkeypatch):
    launched = []
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setattr(linux.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(linux, "_user_manager_has_display", lambda environment: True)
    monkeypatch.setattr(linux.subprocess, "Popen", lambda command, **options: launched.append(command))
    linux.launch_chrome(Path("/usr/bin/google-chrome"), ["--user-data-dir=/p"])
    systemd = ["systemd-run", "--user", "--collect", "--quiet", "--"]
    assert launched == [[*systemd, "/usr/bin/google-chrome", "--user-data-dir=/p"]]

    launched.clear()
    monkeypatch.setattr(linux, "_user_manager_has_display", lambda environment: False)
    with pytest.raises(RuntimeError, match="画面のセッション"):
        linux.launch_chrome(Path("/usr/bin/google-chrome"), [])
    monkeypatch.setenv("DISPLAY", ":0")
    linux.launch_chrome(Path("/usr/bin/google-chrome"), [])
    assert launched == [["/usr/bin/google-chrome"]]


@pytest.mark.skipif(os.name != "nt", reason="Windowsの起動経路はWindowsの端末で確かめる")
def test_windows_chrome_is_created_outside_the_caller(monkeypatch):
    calls = []

    class Completed:
        returncode = 0

    def run(command, **options):
        calls.append(options["env"]["JEV_BOOKMARKS_CHROME"])
        return Completed()

    monkeypatch.setattr(windows.subprocess, "run", run)
    monkeypatch.setattr(windows.subprocess, "Popen", lambda *args, **options: pytest.fail("直接起動した"))
    windows.launch_chrome(Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"), ["--user-data-dir=C:\\p q"])
    assert calls == ['"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" "--user-data-dir=C:\\p q"']
