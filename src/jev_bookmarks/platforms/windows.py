"""Windows: Chromeはレジストリに登録したパスからマニフェストを読み、履歴接続は名前付きパイプを使う。"""

import hashlib
import os
import secrets
import subprocess
import sys
import threading
from collections.abc import Callable
from multiprocessing import AuthenticationError
from multiprocessing.connection import Client, Listener
from pathlib import Path

HOST_KEY = r"Software\Google\Chrome\NativeMessagingHosts\ai.jevbookmarks.history"


def data_dir() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "JevBookmarks"


def manifest_dir() -> Path:
    from ..paths import data_dir as configured

    return configured() / "native-messaging"


def host_executable(root: Path) -> Path:
    if not (root / ".venv" / "Scripts" / "python.exe").is_file():
        raise RuntimeError("プロジェクトの .venv がありません。uv sync --locked を実行してください")
    return root / "bin" / "native-host.cmd"


def register_host(manifest: Path) -> None:
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, HOST_KEY) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest))


def prepare_process() -> None:
    # 既定の文字コード（cp932）ではなくUTF-8で動かし、ハーネスへ返すJSONや読み書きするファイルをUTF-8にそろえる。
    if not sys.flags.utf8_mode:
        completed = subprocess.run([sys.executable, "-X", "utf8", "-m", "jev_bookmarks.cli", *sys.argv[1:]])
        sys.exit(completed.returncode)


def browser_runtime_dir() -> Path:
    from ..paths import data_dir as configured

    return configured() / "browser-harness" / "runtime"


def chrome_executable() -> Path:
    roots = [os.environ.get(name) for name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    for root in roots:
        if not root:
            continue
        candidate = Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe"
        if candidate.is_file():
            return candidate
    raise RuntimeError("Google Chromeがありません。公式インストーラーで導入してください")


def launch_chrome(executable: Path, arguments: list[str]) -> None:
    subprocess.Popen(
        [str(executable), *arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
    )


def _identity() -> str:
    from ..paths import data_dir as configured

    return hashlib.sha256(str(configured().resolve()).encode()).hexdigest()[:12]


def _address() -> str:
    user = hashlib.sha256(os.environ.get("USERNAME", "").encode()).hexdigest()[:8]
    return rf"\\.\pipe\jev-bookmarks-{user}-{_identity()}"


def _key_path() -> Path:
    """名前付きパイプの相互認証鍵。ホストの稼働中だけ存在する。"""
    from ..paths import data_dir as configured

    return configured() / "run" / "bridge.key"


def _write_key() -> bytes:
    """同じユーザーのコマンドだけが読める場所へ、この起動限りの鍵を置く。"""
    path = _key_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            with Client(_address(), family="AF_PIPE", authkey=path.read_bytes()):
                pass
        except (OSError, EOFError, AuthenticationError):
            path.unlink()
        else:
            raise RuntimeError("Chrome履歴のホストが既に稼働しています")
    authkey = secrets.token_bytes(32)
    with open(path, "xb") as handle:
        handle.write(authkey)
    return authkey


def _serve_client(answer: Callable[[bytes], bytes], connection) -> None:
    with connection:
        try:
            raw = connection.recv_bytes(64_000)
        except (OSError, EOFError):
            return
        try:
            connection.send_bytes(answer(raw))
        except OSError:
            pass


def _accept(answer: Callable[[bytes], bytes], listener: Listener, closing: threading.Event) -> None:
    while not closing.is_set():
        try:
            connection = listener.accept()
        except (OSError, EOFError, AuthenticationError):
            continue
        threading.Thread(target=_serve_client, args=(answer, connection), daemon=True).start()


def serve(answer: Callable[[bytes], bytes], pump: Callable[[], None]) -> None:
    authkey = _write_key()
    closing = threading.Event()
    try:
        listener = Listener(_address(), family="AF_PIPE", authkey=authkey)
        threading.Thread(target=_accept, args=(answer, listener, closing), daemon=True).start()
        try:
            pump()
        finally:
            closing.set()
            listener.close()
    finally:
        _key_path().unlink(missing_ok=True)


def ask(request: bytes) -> str:
    try:
        authkey = _key_path().read_bytes()
    except FileNotFoundError as exc:
        raise ConnectionError("Chrome履歴のホストが起動していません") from exc
    try:
        with Client(_address(), family="AF_PIPE", authkey=authkey) as connection:
            connection.send_bytes(request)
            if not connection.poll(45):
                raise TimeoutError("Chrome履歴のホストが応答しませんでした")
            return connection.recv_bytes(4_000_000).decode("utf-8")
    except (EOFError, AuthenticationError) as exc:
        raise ConnectionError(str(exc) or type(exc).__name__) from exc


def available() -> bool:
    return _key_path().exists()
