# 開発への参加

不具合や改善案は [Issues](https://github.com/kitepon/jev-bookmarks/issues) へ。再現手順には公開ページか架空データを使い、閲覧履歴、実際の口座ページ、完全な私用URL、APIキーを貼らないでください。脆弱性は [SECURITY.md](SECURITY.md) の経路で非公開報告してください。

## 開発環境

Python 3.12、`uv`、Node.js、Gitを使います。

```sh
uv sync --locked
uv run pytest -q
node --test tests/extension.test.mjs
uv run ruff check .
```

Windowsでは上流の都合で `PYTHONUTF8=1` を付けてテストを実行してください（CLIは自動でUTF-8モードに切り替えます）。

通常のテストは公開の `example.com` と一時Gitプロジェクトを使い、Chromeの実履歴やTypeSafeのAPIキーを必要としません。実機確認を行う場合は [README](README.md#導入) の設定を使い、結果に私用URLやページ本文を載せないでください。

## OSとハーネス

共通コードに `sys.platform` の分岐や特定ハーネスの事情を書かないでください。OSの違いは `src/jev_bookmarks/platforms/<os>.py`、ハーネスの違いは `src/jev_bookmarks/harnesses/<harness>.py` に閉じます。守る約束は各 `__init__.py` にあり、`tests/test_adapters.py` が確かめます。

## 変更の境界

- Chrome履歴は拡張の正規APIから要求時だけ取得します。ブラウザ内部の履歴DBを直接読みません。
- URLは実際の電話帳または履歴候補から選び、推測で作りません。
- 操作と操作後の判定は一回の `run` に収め、役立たないページは記録しません。
- 電話帳はプロジェクト内のローカルデータです。`jev-bookmark/bookmarks.json` やenvファイルをコミットしません。

変更に関連するテストを通し、公開動作を変える場合はREADME、設計書、変更履歴を同じPull Requestで更新してください。
