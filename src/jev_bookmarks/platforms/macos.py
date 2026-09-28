"""macOS: ChromeはユーザーのNativeMessagingHostsフォルダーからマニフェストを読む。"""

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from . import posix


def data_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / "JevBookmarks"


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
    candidates = (
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Google Chromeがありません。公式インストーラーで導入してください")


def launch_chrome(executable: Path, arguments: list[str]) -> None:
    subprocess.Popen(
        ["/usr/bin/open", "-na", str(executable.parents[2]), "--args", *arguments],
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
