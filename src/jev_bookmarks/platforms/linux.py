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


def legacy_manifest_dirs() -> list[Path]:
    return [Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "google-chrome" / "NativeMessagingHosts"]


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


def _session_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return environment


def _user_manager_has_display(environment: dict[str, str]) -> bool:
    try:
        completed = subprocess.run(
            ["systemctl", "--user", "show-environment"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    names = {line.split("=", 1)[0] for line in completed.stdout.splitlines()}
    return completed.returncode == 0 and bool(names & {"WAYLAND_DISPLAY", "DISPLAY"})


def launch_chrome(executable: Path, arguments: list[str]) -> None:
    command = [str(executable), *arguments]
    environment = _session_environment()
    # ログイン中の画面セッションはユーザーのsystemdが持っている。そこから起動すれば、SSHやハーネスの
    # 実行環境に画面の変数が無くても開け、ハーネスのコマンドが終わってもChromeが巻き込まれない。
    if shutil.which("systemd-run") and _user_manager_has_display(environment):
        command = ["systemd-run", "--user", "--collect", "--quiet", "--", *command]
    elif not (os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")):
        raise RuntimeError("画面のセッションが見つかりません。デスクトップにログインした状態で実行してください")
    subprocess.Popen(
        command,
        env=environment,
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
