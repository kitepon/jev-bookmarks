import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from jev_bookmarks import history_bridge, phonebook, runner, typesafe
from jev_bookmarks.paths import socket_path


def test_phonebook_records_only_confirmed_page(tmp_path: Path):
    path = tmp_path / "bookmarks.json"
    phonebook.remember("口座一覧を開く", "https://example.com/accounts", "口座一覧", path)
    phonebook.remember("口座一覧を開く", "https://example.com/accounts", "口座一覧", path)
    assert len(phonebook.read(path)) == 1
    assert phonebook.read(path)[0]["url"] == "https://example.com/accounts"
    assert phonebook.forget("https://example.com/accounts", path) == 1
    assert phonebook.read(path) == []


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
        while not socket_path().exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert socket_path().exists()

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
    assert not socket_path().exists()


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

    monkeypatch.setattr(runner, "Agent", Agent)
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

    monkeypatch.setattr(runner, "Agent", FailedAgent)
    monkeypatch.setattr(
        runner,
        "_phonebook_candidates",
        lambda goal: [{"url": "https://example.com/", "title": "Example"}],
    )
    monkeypatch.setattr(typesafe, "choose", lambda goal, candidates: candidates[0])
    with pytest.raises(runner.BrowserUseError, match="Chromeに接続できません"):
        runner.run("Example Domainを開く")
