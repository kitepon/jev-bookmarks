import base64
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

HOST_NAME = "ai.jevbookmarks.history"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def extension_id() -> str:
    manifest = json.loads((project_root() / "extension" / "manifest.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(base64.b64decode(manifest["key"])).digest()[:16]
    return "".join(chr(ord("a") + value) for byte in digest for value in (byte >> 4, byte & 15))


def install_native_host() -> Path:
    if sys.platform == "darwin":
        directory = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"
    elif sys.platform == "win32":
        raise RuntimeError("WindowsのNative Messaging登録は未実装です")
    else:
        directory = Path.home() / ".config" / "google-chrome" / "NativeMessagingHosts"
    directory.mkdir(parents=True, exist_ok=True)
    host = project_root() / "bin" / "native-host"
    if not host.is_file() or not os.access(host, os.X_OK):
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
    return target
