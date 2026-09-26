import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import history_bridge, phonebook, typesafe
from .install import extension_id, install_native_host, project_root
from .paths import ProjectHomeError
from .settings import load_environment, save_env_paths


def _print(payload: dict | list) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _rerun_in_utf8_mode() -> None:
    # 上流のjev-ultrafastはファイルを既定の文字コードで読むので、WindowsではUTF-8モードで動かし直す。
    if sys.platform == "win32" and not sys.flags.utf8_mode:
        completed = subprocess.run([sys.executable, "-X", "utf8", "-m", "jev_bookmarks.cli", *sys.argv[1:]])
        sys.exit(completed.returncode)


def main() -> None:
    _rerun_in_utf8_mode()
    from . import runner

    parser = argparse.ArgumentParser(prog="jev-bookmarks")
    commands = parser.add_subparsers(dest="command", required=True)
    run_command = commands.add_parser("run", help="目的を一度渡してページ選択から記録まで進める")
    run_command.add_argument("goal")
    install_command = commands.add_parser("install", help="この端末のChrome連携を設定する")
    install_command.add_argument("--typesafe-env", type=Path, required=True)
    install_command.add_argument("--browser-env", type=Path, required=True)
    commands.add_parser("status", help="Chrome履歴との接続状態を見る")
    commands.add_parser("list", help="電話帳を見る")
    forget_command = commands.add_parser("forget", help="URLを電話帳から削除する")
    forget_command.add_argument("url")
    args = parser.parse_args()

    try:
        if args.command == "install":
            settings = save_env_paths(args.typesafe_env, args.browser_env)
            host = install_native_host()
            _print({
                "status": "installed",
                "host_manifest": str(host),
                "settings": str(settings),
                "extension_directory": str(project_root() / "extension"),
                "extension_id": extension_id(),
            })
        elif args.command == "status":
            _print({"history_connected": history_bridge.available(), "extension_id": extension_id()})
        elif args.command == "list":
            _print(phonebook.read())
        elif args.command == "forget":
            _print({"removed": phonebook.forget(args.url)})
        elif args.command == "run":
            load_environment()
            _print(runner.run(args.goal))
    except (
        history_bridge.HistoryError,
        typesafe.TypeSafeError,
        phonebook.PhonebookError,
        runner.BrowserUseError,
        ProjectHomeError,
        FileNotFoundError,
    ) as exc:
        _print({"status": "error", "code": type(exc).__name__, "message": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
