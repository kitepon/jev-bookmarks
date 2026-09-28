import argparse
import json
import sys
from pathlib import Path

from . import browser, harnesses, history_bridge, phonebook, platforms, runner, typesafe
from .install import extension_id, install_extension, install_native_host
from .paths import ProjectHomeError
from .settings import load_environment, save_env_paths


def _print(payload: dict | list) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    platforms.current().prepare_process()

    parser = argparse.ArgumentParser(prog="jev-bookmarks")
    commands = parser.add_subparsers(dest="command", required=True)
    run_command = commands.add_parser("run", help="目的を一度渡してページ選択から記録まで進める")
    run_command.add_argument("goal")
    install_command = commands.add_parser("install", help="この端末のChrome連携を設定する")
    install_command.add_argument("--typesafe-env", type=Path, required=True)
    install_command.add_argument("--browser-env", type=Path, required=True)
    harness_command = commands.add_parser("harness", help="ハーネスへjev-bookmarksの呼び方を入れる")
    harness_actions = harness_command.add_subparsers(dest="action", required=True)
    harness_install = harness_actions.add_parser("install", help="スキルを入れる（省略時は検出できた全ハーネス）")
    harness_install.add_argument("names", nargs="*", metavar="harness", help=" / ".join(harnesses.ALL))
    harness_actions.add_parser("status", help="各ハーネスのスキルの状態を見る")
    commands.add_parser("status", help="Chrome履歴との接続状態を見る")
    commands.add_parser("list", help="電話帳を見る")
    forget_command = commands.add_parser("forget", help="URLを電話帳から削除する")
    forget_command.add_argument("url")
    args = parser.parse_args()

    try:
        if args.command == "install":
            settings = save_env_paths(args.typesafe_env, args.browser_env)
            extension = install_extension()
            host = install_native_host()
            dedicated_browser = browser.install()
            _print({
                "status": "installed",
                "host_manifest": str(host),
                "settings": str(settings),
                "extension_directory": str(extension),
                "extension_id": extension_id(),
                "browser": dedicated_browser,
            })
        elif args.command == "harness" and args.action == "install":
            _print({"status": "installed", "harnesses": harnesses.install(args.names)})
        elif args.command == "harness":
            _print(harnesses.status())
        elif args.command == "status":
            _print({
                "browser": browser.status(),
                "harnesses": harnesses.status(),
            })
        elif args.command == "list":
            _print(phonebook.read())
        elif args.command == "forget":
            _print({"removed": phonebook.forget(args.url)})
        elif args.command == "run":
            load_environment()
            browser.prepare()
            _print(runner.run(args.goal))
    except (
        history_bridge.HistoryError,
        typesafe.TypeSafeError,
        phonebook.PhonebookError,
        runner.BrowserUseError,
        browser.BrowserSetupError,
        harnesses.HarnessError,
        ProjectHomeError,
        FileNotFoundError,
    ) as exc:
        _print({"status": "error", "code": type(exc).__name__, "message": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
