# Jev Bookmarks の開発指示

このリポジトリは、親AIが目的を一回渡すだけでURL選択、Browser Use、操作後判定、電話帳への記録まで進めるCLIを所有する。仕様と受入条件は [docs/design.md](docs/design.md) を正とする。

- 変更前に `git status` と `origin/main` を確認し、既存差分を消さない。
- 電話帳はGitプロジェクトごとの `jev-bookmark/bookmarks.json`、Chrome履歴接続の設定は端末共通に保つ。
- 履歴取得はChrome拡張の `chrome.history.search`、操作は上流 `jev-ultrafast` の正規入口を使う。ブラウザ内部DBを読まず、独自の操作ループを作らない。
- テストや公開Issueへ実履歴、私用URL、ページ本文、APIキーを持ち込まない。
- 変更に直結するテストを実行し、公開動作の変更はREADME、設計書、変更履歴へ反映する。
