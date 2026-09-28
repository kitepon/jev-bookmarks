"""Linux: Google ChromeはXDG設定のNativeMessagingHostsフォルダーからマニフェストを読む。"""

import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from . import posix


def data_dir() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "jev-bookmarks"


def manifest_dir() -> Path:
    from ..paths import data_dir as configured

    return configured() / "chrome-profile" / "NativeMessagingHosts"


def host_executable(root: Path) -> Path:
    host = root / "bin" / "native-host"
    if not os.access(host, os.X_OK):
        raise RuntimeError("Native Messaging hostの実行ファイルがありません")
    return host


def register_host(manifest: Path) -> None:
    pass


def prepare_process() -> None:
    pass


def browser_runtime_dir() -> Path:
    from ..paths import data_dir as configured

    return posix.browser_runtime_dir(configured())


def chrome_executable() -> Path:
    for command in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if executable := shutil.which(command):
            return Path(executable)
    raise RuntimeError("ChromeまたはChromiumがありません。OSの公式パッケージ管理で導入してください")


def launch_chrome(executable: Path, arguments: list[str]) -> None:
    subprocess.Popen(
        [str(executable), *arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _socket() -> Path:
    from ..paths import data_dir as configured

    return posix.socket_path(configured())


def serve(answer: Callable[[bytes], bytes], pump: Callable[[], None]) -> None:
    posix.serve(_socket(), answer, pump)


def ask(request: bytes) -> str:
    return posix.ask(_socket(), request)


def available() -> bool:
    return _socket().exists()
