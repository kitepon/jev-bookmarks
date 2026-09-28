# Chrome自動操作は専用プロファイルへ分離する

出典: [Chrome 136のremote debugging変更](https://developer.chrome.com/blog/remote-debugging-port)、[Chrome拡張の2025年6月更新](https://developer.chrome.com/blog/extension-news-june-2025)、[Chrome for Testing](https://developer.chrome.com/docs/automation-and-testing/chrome-for-testing)。取得日: 2026-09-28。確度: 公開仕様は高、Jev Bookmarksへの適用は実測済み。

Chrome 136以降、`--remote-debugging-port` と `--remote-debugging-pipe` は標準データディレクトリに対して有効にならず、既定と異なる `--user-data-dir` が必要になった。自動操作は普段使うプロファイルへ後付けするのでなく、製品専用プロファイルとして起動する。

Chrome 137以降、通常のGoogle Chromeは `--load-extension` でunpacked extensionを読み込まない。Chrome for Testingは拡張試験に使えるが、通常閲覧用としては配布されていない。Jev BookmarksはOSの標準経路で導入されたGoogle Chromeを専用プロファイルで起動し、Chrome DevTools Protocolの `Extensions.loadUnpacked` で固定IDの履歴拡張を起動ごとに読み込む。Chrome 153の通常版で、専用プロファイル再起動後の読込とNative Messaging往復を実測した。

実測では、通常Chromeの新規専用プロファイルは公開HTTPSページを表示できた。同条件のChrome for Testing 153・154はこのMacで主画面のHTTPS要求が完了しなかったため採用しない。Chrome for Testingへの自動切替や通常Chromeへのフォールバックは置かず、通常Chromeを正規の単一経路とする。
