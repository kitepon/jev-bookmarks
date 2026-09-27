# Chrome拡張の `manifest.json` にある `key`

出典: [Chrome for Developers — Manifest - key](https://developer.chrome.com/docs/extensions/reference/manifest/key)
取得日: 2026-09-27
確度: 高（Chrome公式仕様と実装を照合）

Chrome拡張の `manifest.json` に置く `key` は、開発中も拡張IDを一定に保つための公開鍵である。APIキーや署名用の秘密鍵ではない。

Jev Bookmarksでは `src/jev_bookmarks/install.py` がこの公開鍵をBase64デコードし、Chromeと同じ規則で固定拡張IDを算出する。そのIDをNative Messaging hostの `allowed_origins` に使う。全Git履歴をgitleaksで検査すると `generic-api-key` として1件検出されるが、対象はこの公開鍵だけであり、秘密情報の流出ではない。
