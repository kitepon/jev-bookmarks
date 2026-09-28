import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import history_bridge, platforms
from .install import extension_directory, extension_id
from .paths import data_dir

DAEMON_NAME = "jev-bookmarks"


class BrowserSetupError(RuntimeError):
    pass


def profile_directory() -> Path:
    return data_dir() / "chrome-profile"


def _endpoint() -> str | None:
    active = profile_directory() / "DevToolsActivePort"
    try:
        port = active.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
        int(port)
    except (FileNotFoundError, IndexError, OSError, ValueError):
        return None
    endpoint = f"http://127.0.0.1:{port}"
    try:
        with urllib.request.urlopen(f"{endpoint}/json/version", timeout=1) as response:
            payload = json.loads(response.read())
        if not payload.get("webSocketDebuggerUrl"):
            return None
    except (OSError, ValueError, urllib.error.URLError):
        return None
    return endpoint


def _configure(endpoint: str) -> None:
    runtime = platforms.current().browser_runtime_dir()
    temporary = data_dir() / "browser-harness"
    os.environ.update(
        {
            "BU_NAME": DAEMON_NAME,
            "BU_CDP_URL": endpoint,
            "BH_RUNTIME_DIR": str(runtime),
            "BH_TMP_DIR": str(temporary),
            "BH_RUNTIME_DIR_SHARED": "0",
            "BH_TMP_DIR_SHARED": "0",
        }
    )
    os.environ.pop("BU_CDP_WS", None)
    os.environ.pop("BU_BROWSER_ID", None)


def _open_setup_page(endpoint: str) -> None:
    try:
        with urllib.request.urlopen(f"{endpoint}/json/list", timeout=5) as response:
            targets = json.loads(response.read())
        if any(target.get("url", "").startswith("chrome://extensions") for target in targets):
            return
    except (OSError, TypeError, ValueError, urllib.error.URLError) as exc:
        raise BrowserSetupError(f"専用Chromeのタブを確認できませんでした: {exc}") from exc
    url = f"{endpoint}/json/new?{urllib.parse.quote('chrome://extensions/', safe=':/')}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="PUT"), timeout=5):
            pass
    except (OSError, urllib.error.URLError) as exc:
        raise BrowserSetupError(f"専用Chromeの拡張画面を開けませんでした: {exc}") from exc


def _id_from_key(key: str) -> str:
    digest = hashlib.sha256(base64.b64decode(key)).digest()[:16]
    return "".join(chr(ord("a") + value) for byte in digest for value in (byte >> 4, byte & 15))


def _extension_files_installed() -> bool:
    manifest = extension_directory() / "manifest.json"
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return False
    return isinstance(payload.get("key"), str) and extension_id() == _id_from_key(payload["key"])


def _start(*, setup: bool, history_timeout: float) -> dict:
    if not _extension_files_installed():
        raise BrowserSetupError("専用Chrome拡張がありません。jev-bookmarks install を実行してください")
    profile = profile_directory()
    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        os.chmod(profile, 0o700)
    try:
        executable = platforms.current().chrome_executable()
    except RuntimeError as exc:
        raise BrowserSetupError(str(exc)) from exc
    endpoint = _endpoint()
    if endpoint is None:
        start_page = "chrome://extensions/" if setup else "about:blank"
        platforms.current().launch_chrome(
            executable,
            [
                "--remote-debugging-address=127.0.0.1",
                "--remote-debugging-port=0",
                f"--user-data-dir={profile}",
                "--no-first-run",
                "--no-default-browser-check",
                "--new-window",
                start_page,
            ],
        )
        deadline = time.monotonic() + 15
        while endpoint is None and time.monotonic() < deadline:
            time.sleep(0.1)
            endpoint = _endpoint()
        if endpoint is None:
            raise BrowserSetupError("Jev Bookmarks専用Chromeを起動できませんでした")
    _configure(endpoint)
    if setup and not history_bridge.available():
        _open_setup_page(endpoint)
    deadline = time.monotonic() + history_timeout
    while not history_bridge.available() and time.monotonic() < deadline:
        time.sleep(0.1)
    connected = history_bridge.available()
    return {
        "profile": str(profile),
        "chrome": str(executable),
        "extension_directory": str(extension_directory()),
        "extension_id": extension_id(),
        "browser_running": True,
        "history_connected": connected,
    }


def install() -> dict:
    return _start(setup=True, history_timeout=2)


def prepare(*, history_timeout: float = 15) -> dict:
    result = _start(setup=False, history_timeout=history_timeout)
    if not result["history_connected"]:
        raise BrowserSetupError(
            "専用Chromeに履歴拡張がありません。chrome://extensions/ でデベロッパーモードを有効にし、"
            f"「パッケージ化されていない拡張機能を読み込む」から {extension_directory()} を選んでください"
        )
    return result


def status() -> dict:
    try:
        executable = str(platforms.current().chrome_executable())
    except RuntimeError:
        executable = None
    return {
        "profile": str(profile_directory()),
        "chrome": executable,
        "extension_directory": str(extension_directory()),
        "extension_id": extension_id(),
        "extension_files_installed": _extension_files_installed(),
        "browser_running": _endpoint() is not None,
        "history_connected": history_bridge.available(),
    }
