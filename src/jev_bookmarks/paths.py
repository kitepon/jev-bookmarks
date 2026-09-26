import hashlib
import os
import sys
from pathlib import Path


class ProjectHomeError(RuntimeError):
    pass


def project_home() -> Path:
    current = Path.cwd().resolve()
    for directory in (current, *current.parents):
        if (directory / ".git").exists():
            return directory
    raise ProjectHomeError("Git管理のプロジェクト内から実行してください")


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
    return project_home() / "jev-bookmark" / "bookmarks.json"
