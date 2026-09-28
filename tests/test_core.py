import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from jev_bookmarks import browser, history_bridge, phonebook, runner, settings, typesafe
from jev_bookmarks.install import DEDICATED_EXTENSION_KEY, extension_id, install_extension, project_root
from jev_bookmarks.paths import ProjectHomeError, phonebook_path


def test_phonebook_records_only_confirmed_page(tmp_path: Path):
    path = tmp_path / "bookmarks.json"
    phonebook.remember("口座一覧を開く", "https://example.com/accounts", "口座一覧", path)
    phonebook.remember("口座一覧を開く", "https://example.com/accounts", "口座一覧", path)
    assert len(phonebook.read(path)) == 1
    assert phonebook.read(path)[0]["url"] == "https://example.com/accounts"
    assert phonebook.forget("https://example.com/accounts", path) == 1
    assert phonebook.read(path) == []


def test_install_builds_a_dedicated_extension_identity(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("JEV_BOOKMARKS_HOME", str(tmp_path))
    target = install_extension()
    installed = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    source = json.loads((project_root() / "extension" / "manifest.json").read_text(encoding="utf-8"))
    assert installed["key"] == DEDICATED_EXTENSION_KEY
    assert installed["key"] != source["key"]
    assert browser._id_from_key(installed["key"]) == extension_id()
    assert (target / "background.js").read_bytes() == (project_root() / "extension" / "background.js").read_bytes()


def test_browser_owns_profile_endpoint_and_harness_runtime(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("JEV_BOOKMARKS_HOME", str(tmp_path))
    monkeypatch.setenv("BU_CDP_WS", "ws://wrong.example")
    install_extension()
    state = {"endpoint": None}
    launched = []

    class Platform:
        @staticmethod
        def browser_runtime_dir():
            return tmp_path / "runtime"

        @staticmethod
        def chrome_executable():
            return tmp_path / "chrome"

        @staticmethod
        def launch_chrome(executable, arguments):
            launched.append(arguments)
            state["endpoint"] = "http://127.0.0.1:9333"

    monkeypatch.setattr(browser.platforms, "current", lambda: Platform)
    monkeypatch.setattr(browser, "_endpoint", lambda: state["endpoint"])
    monkeypatch.setattr(history_bridge, "available", lambda: True)
    result = browser.prepare(history_timeout=0)
    assert result["browser_running"] and result["history_connected"]
    assert f"--user-data-dir={browser.profile_directory()}" in launched[0]
    assert not any(argument.startswith("--load-extension=") for argument in launched[0])
    assert os.environ["BU_NAME"] == "jev-bookmarks"
    assert os.environ["BU_CDP_URL"] == "http://127.0.0.1:9333"
    assert os.environ["BH_RUNTIME_DIR"] == str(tmp_path / "runtime")
    assert "BU_CDP_WS" not in os.environ


def test_install_opens_setup_without_claiming_history_connection(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("JEV_BOOKMARKS_HOME", str(tmp_path))
    install_extension()
    launched = []

    class Platform:
        @staticmethod
        def browser_runtime_dir():
            return tmp_path / "runtime"

        @staticmethod
        def chrome_executable():
            return tmp_path / "chrome"

        @staticmethod
        def launch_chrome(executable, arguments):
            launched.append(arguments)

    monkeypatch.setattr(browser.platforms, "current", lambda: Platform)
    monkeypatch.setattr(browser, "_endpoint", lambda: None if not launched else "http://127.0.0.1:9333")
    monkeypatch.setattr(browser, "_open_setup_page", lambda endpoint: launched.append([endpoint, "chrome://extensions/"]))
    monkeypatch.setattr(history_bridge, "available", lambda: False)
    result = browser.install()
    assert result["history_connected"] is False
    assert launched[1] == ["http://127.0.0.1:9333", "chrome://extensions/"]


def test_browser_env_cannot_override_owned_chrome(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("JEV_BOOKMARKS_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("TEXT_MODEL", raising=False)
    monkeypatch.delenv("BU_CDP_URL", raising=False)
    typesafe_env = tmp_path / "typesafe.env"
    browser_env = tmp_path / "browser.env"
    typesafe_env.write_text("TYPESAFE_API_KEY=test\n", encoding="utf-8")
    browser_env.write_text("TEXT_MODEL=test-model\nBU_CDP_URL=http://127.0.0.1:9999\n", encoding="utf-8")
    settings.save_env_paths(typesafe_env, browser_env)
    settings.load_environment()
    assert os.environ["TEXT_MODEL"] == "test-model"
    assert "BU_CDP_URL" not in os.environ


def test_phonebook_write_failure_keeps_previous_entry(tmp_path: Path, monkeypatch):
    path = tmp_path / "bookmarks.json"
    phonebook.remember("最初の目的", "https://example.com/first", "最初", path)

    def fail_replace(*_args):
        raise OSError("保存先を更新できません")

    monkeypatch.setattr(phonebook.os, "replace", fail_replace)
    with pytest.raises(phonebook.PhonebookError, match="保存先を更新できません"):
        phonebook.remember("次の目的", "https://example.com/next", "次", path)
    assert [entry["url"] for entry in phonebook.read(path)] == ["https://example.com/first"]


def test_phonebook_is_scoped_to_git_project(tmp_path: Path, monkeypatch):
    first = tmp_path / "first"
    second = tmp_path / "second"
    for project in (first, second):
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)

    nested = first / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    phonebook.remember("口座を見る", "https://example.com/accounts", "口座", None)
    saved = first / "jev-bookmark" / "bookmarks.json"
    assert phonebook_path() == saved
    assert saved.is_file()
    assert phonebook.read()[0]["url"] == "https://example.com/accounts"
    subprocess.run(["git", "-C", str(first), "check-ignore", "-q", str(saved)], check=True)

    monkeypatch.chdir(second)
    assert phonebook.read() == []
    assert phonebook_path() == second / "jev-bookmark" / "bookmarks.json"


def test_phonebook_requires_project_home(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ProjectHomeError, match="Git管理のプロジェクト"):
        phonebook.read()


def test_native_bridge_round_trip_with_extension_response(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("JEV_BOOKMARKS_HOME", str(tmp_path))
    process = subprocess.Popen(
        [sys.executable, "-m", "jev_bookmarks.native_host"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "JEV_BOOKMARKS_HOME": str(tmp_path)},
    )
    try:
        deadline = time.monotonic() + 5
        while not history_bridge.available() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert history_bridge.available()

        received = []

        def query():
            received.append(history_bridge.search("口座一覧"))

        worker = threading.Thread(target=query)
        worker.start()
        header = process.stdout.read(4)
        length = int.from_bytes(header, sys.byteorder)
        request = json.loads(process.stdout.read(length))
        assert request["type"] == "search"
        assert request["goal"] == "口座一覧"
        response = {"id": request["id"], "candidates": [{"url": "https://example.com/accounts", "title": "口座一覧"}]}
        raw = json.dumps(response, ensure_ascii=False).encode("utf-8")
        process.stdin.write(len(raw).to_bytes(4, sys.byteorder) + raw)
        process.stdin.flush()
        worker.join(timeout=5)
        assert not worker.is_alive()
        assert received[0][0]["url"] == "https://example.com/accounts"
    finally:
        process.stdin.close()
        process.wait(timeout=5)
        assert process.returncode == 0, process.stderr.read().decode()
    assert not history_bridge.available()


def test_unhelpful_page_returns_to_parent_without_saving(monkeypatch):
    page = {"url": "https://example.com/", "title": "Example Domain", "text": "Example Domain"}

    class Browser:
        def observe(self, screenshot=False):
            return page

    class Agent:
        browser = Browser()

        def __init__(self, url, goal):
            assert url == "https://example.com/"
            assert goal == "口座残高を見る"

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def snapshot(self):
            return {"status": "ready", "history": []}

        def run(self):
            yield {"status": "blocked", "history": []}

    monkeypatch.setattr(runner, "_agent", Agent)
    monkeypatch.setattr(runner, "_phonebook_candidates", lambda goal: [])
    monkeypatch.setattr(history_bridge, "search", lambda goal: [{"url": "https://example.com/", "title": "Example"}])
    monkeypatch.setattr(
        typesafe,
        "choose",
        lambda goal, candidates: candidates[0] if candidates else None,
    )
    monkeypatch.setattr(typesafe, "usefulness", lambda goal, observed: (False, 0.02))
    monkeypatch.setattr(phonebook, "remember", lambda *_args: (_ for _ in ()).throw(AssertionError("保存された")))
    result = runner.run("口座残高を見る")
    assert result["operation_status"] == "blocked"
    assert result["page"]["url"] == "https://example.com/"
    assert result["useful"] is False
    assert result["saved"] is False


def test_browser_failure_is_reported_as_external_error(monkeypatch):
    class FailedAgent:
        def __init__(self, *_args):
            raise RuntimeError("Chromeに接続できません")

    monkeypatch.setattr(runner, "_agent", FailedAgent)
    monkeypatch.setattr(
        runner,
        "_phonebook_candidates",
        lambda goal: [{"url": "https://example.com/", "title": "Example"}],
    )
    monkeypatch.setattr(typesafe, "choose", lambda goal, candidates: candidates[0])
    with pytest.raises(runner.BrowserUseError, match="Chromeに接続できません"):
        runner.run("Example Domainを開く")


def test_entry_choice_asks_for_a_reachable_start_not_only_the_target(monkeypatch):
    asked = {}

    def evaluate(state, questions):
        asked.update(questions["page"])
        return {"page": {"choice": "c0"}}

    monkeypatch.setattr(typesafe, "_evaluate", evaluate)
    intro = {"url": "https://docs.example.com/introduction", "title": "Introduction"}
    assert typesafe.choose("Noulの説明ページを開く", [intro]) == intro
    # 目的のページが候補に無くても、同じサイトの入口は選べるように問う。noneは関係するサイトが無い時だけ。
    assert "たどり着けるか" in asked["instructions"]
    assert "同じサイトやサービスの入口" in asked["instructions"]
    assert asked["criteria"]["none"] == "どの候補も、目的と関係するサイトやサービスのページではない"

    monkeypatch.setattr(typesafe, "_evaluate", lambda state, questions: {"page": {"choice": "none"}})
    assert typesafe.choose("Amazonで電池を注文する", [intro]) is None
