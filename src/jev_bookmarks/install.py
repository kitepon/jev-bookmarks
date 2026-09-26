import base64
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from .paths import data_dir

HOST_NAME = "ai.jevbookmarks.history"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def extension_id() -> str:
    manifest = json.loads((project_root() / "extension" / "manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(base64.b64decode(manifest["key"])).digest()[:16]
    return "".join(chr(ord("a") + value) for byte in digest for value in (byte >> 4, byte & 15))


def _manifest_directory() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"
    if sys.platform == "win32":
        # WindowsのChromeはレジストリに登録したパスからマニフェストを読む。
        return data_dir() / "native-messaging"
    return Path.home() / ".config" / "google-chrome" / "NativeMessagingHosts"


def _host_executable() -> Path:
    if sys.platform == "win32":
        host = project_root() / "bin" / "native-host.cmd"
        if not (project_root() / ".venv" / "Scripts" / "python.exe").is_file():
            raise RuntimeError("プロジェクトの .venv がありません。uv sync --locked を実行してください")
        return host
    host = project_root() / "bin" / "native-host"
    if not os.access(host, os.X_OK):
        raise RuntimeError("Native Messaging hostの実行ファイルがありません")
    return host


def _register_windows(manifest: Path) -> None:
    import winreg

    key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest))


def install_native_host() -> Path:
    directory = _manifest_directory()
    directory.mkdir(parents=True, exist_ok=True)
    host = _host_executable()
    if not host.is_file():
        raise RuntimeError("Native Messaging hostの実行ファイルがありません")
    target = directory / f"{HOST_NAME}.json"
    payload = {
        "name": HOST_NAME,
        "description": "Jev Bookmarks の履歴接続",
        "path": str(host),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{extension_id()}/"],
    }
    fd, temp_name = tempfile.mkstemp(prefix=".jev-bookmarks-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    if sys.platform == "win32":
        _register_windows(target)
    return target
