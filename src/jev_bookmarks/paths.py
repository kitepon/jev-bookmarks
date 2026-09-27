import os
from pathlib import Path

from . import platforms


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
    return platforms.current().data_dir()


def phonebook_path() -> Path:
    return project_home() / "jev-bookmark" / "bookmarks.json"
