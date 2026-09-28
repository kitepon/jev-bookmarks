import json
import os
from pathlib import Path

from .paths import data_dir

KEYS = {
    "TYPESAFE_API_KEY",
    "TEXT_MODEL_API_KEY",
    "TEXT_MODEL_BASE_URL",
    "TEXT_MODEL",
    "TEXT_MODEL_REASONING",
}


def settings_path() -> Path:
    return data_dir() / "settings.json"


def save_env_paths(typesafe_env: Path, browser_env: Path) -> Path:
    for path in (typesafe_env, browser_env):
        if not path.is_file():
            raise FileNotFoundError(f"環境設定ファイルがありません: {path}")
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    payload = {"typesafe_env": str(typesafe_env.resolve()), "browser_env": str(browser_env.resolve())}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def load_environment() -> None:
    path = settings_path()
    if not path.is_file():
        raise FileNotFoundError("初期設定がありません。jev-bookmarks install を実行してください")
    settings = json.loads(path.read_text(encoding="utf-8"))
    for source in (settings["typesafe_env"], settings["browser_env"]):
        for line in Path(source).read_text(encoding="utf-8").splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#") or "=" not in clean:
                continue
            key, value = clean.split("=", 1)
            key = key.removeprefix("export ").strip()
            value = value.strip().strip('"').strip("'")
            if key in KEYS and value:
                os.environ.setdefault(key, value)
