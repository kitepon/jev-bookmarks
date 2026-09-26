import hashlib
import os
import sys
from pathlib import Path


def data_dir() -> Path:
    override = os.environ.get("JEV_BOOKMARKS_HOME")
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "JevBookmarks"
    if sys.platform == "win32":
        return Path(os.environ["LOCALAPPDATA"]) / "JevBookmarks"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "jev-bookmarks"


def socket_path() -> Path:
    if sys.platform == "win32":
        return data_dir() / "run" / "bridge.sock"
    identity = hashlib.sha256(str(data_dir().resolve()).encode()).hexdigest()[:12]
    return Path("/tmp") / f"jev-bookmarks-{os.getuid()}-{identity}" / "bridge.sock"


def phonebook_path() -> Path:
    return data_dir() / "bookmarks.json"
