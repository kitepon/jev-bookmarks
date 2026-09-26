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


def _identity() -> str:
    return hashlib.sha256(str(data_dir().resolve()).encode()).hexdigest()[:12]


def socket_path() -> Path:
    return Path("/tmp") / f"jev-bookmarks-{os.getuid()}-{_identity()}" / "bridge.sock"


def pipe_address() -> str:
    """Windowsの履歴接続に使う名前付きパイプ。"""
    user = hashlib.sha256(os.environ.get("USERNAME", "").encode()).hexdigest()[:8]
    return rf"\\.\pipe\jev-bookmarks-{user}-{_identity()}"


def pipe_key_path() -> Path:
    """名前付きパイプの相互認証鍵。ホストの稼働中だけ存在する。"""
    return data_dir() / "run" / "bridge.key"


def phonebook_path() -> Path:
    return project_home() / "jev-bookmark" / "bookmarks.json"
