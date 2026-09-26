import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .paths import phonebook_path


class PhonebookError(RuntimeError):
    pass


def _valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def read(path: Path | None = None) -> list[dict]:
    path = path or phonebook_path()
    try:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PhonebookError(f"電話帳を読めません: {exc}") from exc
    if not isinstance(data, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("goal"), str)
        or not isinstance(item.get("url"), str)
        or not _valid_url(item["url"])
        for item in data
    ):
        raise PhonebookError("電話帳の形式が不正です")
    return data


def _write(path: Path, entries: list[dict]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path.parent, 0o700)
        fd, temp_name = tempfile.mkstemp(prefix=".bookmarks-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(entries, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
    except OSError as exc:
        raise PhonebookError(f"電話帳を書けません: {exc}") from exc


def remember(goal: str, url: str, title: str, path: Path | None = None) -> dict:
    if not _valid_url(url):
        raise PhonebookError("http(s) のページURLだけ記録できます")
    path = path or phonebook_path()
    entries = read(path)
    entry = {
        "goal": goal,
        "url": url,
        "title": title,
        "useful_at": datetime.now(timezone.utc).isoformat(),
    }
    entries = [old for old in entries if not (old["goal"] == goal and old["url"] == url)]
    entries.append(entry)
    _write(path, entries)
    return entry


def forget(url: str, path: Path | None = None) -> int:
    path = path or phonebook_path()
    entries = read(path)
    kept = [item for item in entries if item["url"] != url]
    if len(kept) == len(entries):
        return 0
    _write(path, kept)
    return len(entries) - len(kept)
