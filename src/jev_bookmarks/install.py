import base64
import hashlib
import json
import os
import tempfile
from pathlib import Path

from . import platforms
from .paths import data_dir

HOST_NAME = "ai.jevbookmarks.history"
DEDICATED_EXTENSION_KEY = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA8lL7Vy5YHSr1TPdqsi4GgBvZvp8XSQREJa6siyYkU83qFtQo7iREDyr448C8HNpqM/zEI2MNo2cGZUYfVCEmpdX3qaRS+RoAPxV7W/E4+m446kqZ7FWZxyFq+HlJVI+dCzNFAqmHKDtdOFm9jBSppCFvkwnGUvl1lkT9Yf/W4tis9YrrIoScQrn9PkedMdmxr91WkPrqU8YTN/cxfAJ5ao6+Kd9Edoij67HOP6aFffEzc0MP1ADUkFIiuSH3Lo49rCGzzdB56QAY/xjbizbi1vlKhZQKuG/Kf4n453UbU/R6Mbt6UlC+9bUOFPH8iGbZ887kCtKvbDnFLAD7zBVJXwIDAQAB"
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def extension_id() -> str:
    digest = hashlib.sha256(base64.b64decode(DEDICATED_EXTENSION_KEY)).digest()[:16]
    return "".join(chr(ord("a") + value) for byte in digest for value in (byte >> 4, byte & 15))


def extension_directory() -> Path:
    return data_dir() / "extension"


def _write(path: Path, content: str) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def install_extension() -> Path:
    source = project_root() / "extension"
    target = extension_directory()
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(target, 0o700)
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    manifest["key"] = DEDICATED_EXTENSION_KEY
    manifest["name"] = "Jev Bookmarks 専用Chrome履歴接続"
    _write(target / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    _write(target / "background.js", (source / "background.js").read_text(encoding="utf-8"))
    return target


def install_native_host() -> Path:
    system = platforms.current()
    directory = system.manifest_dir()
    directory.mkdir(parents=True, exist_ok=True)
    host = system.host_executable(project_root())
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
    system.register_host(target)
    return target
