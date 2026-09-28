"""OSごとの適合層。共通コードはここから今のOSの実装だけを受け取る。

各OSのモジュールは次を持つ。

- ``data_dir()``: 端末共通の設定を置く場所
- ``manifest_dir()``: Native Messaging hostのマニフェストを置く場所
- ``host_executable(root)``: Chromeが起動するhostの実行ファイル
- ``register_host(manifest)``: マニフェストをChromeへ知らせる（ファイル配置だけで済むOSは何もしない）
- ``prepare_process()``: CLIの起動直後にOSの都合で必要な準備
- ``browser_runtime_dir()``: Jev Bookmarks専用Browser Harnessの実行時状態を置く場所
- ``chrome_executable()``: OS標準の方法で導入されたChromeの実行ファイル
- ``launch_chrome(executable, arguments)``: Chromeを専用プロファイルと引数で起動する
- ``serve(answer, pump)``: 同じユーザーだけが使えるローカル接続を開き、``pump()`` が戻るまで要求に ``answer`` で答える
- ``ask(request)``: その接続へ要求を一つ送り、応答を返す。失敗は ``ConnectionError`` か ``TimeoutError``
- ``available()``: hostが待ち受けているかの目安
"""

import sys
from types import ModuleType


def current() -> ModuleType:
    if sys.platform == "darwin":
        from . import macos

        return macos
    if sys.platform == "win32":
        from . import windows

        return windows
    if sys.platform.startswith("linux"):
        from . import linux

        return linux
    raise RuntimeError(f"未対応のOSです: {sys.platform}")
