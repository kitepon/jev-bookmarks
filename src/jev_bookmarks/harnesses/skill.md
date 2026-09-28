---
name: jev-bookmarks
description: Gitプロジェクトの作業中に、目的に合うWebページをJev Bookmarks専用Chromeで開いて操作したい時に使う（例「MFの口座一覧を開いて」「前に見た設定ページへ行って」）。`jev-bookmarks run` を一度呼ぶと、プロジェクトの電話帳か専用Chrome履歴から入口を選び、Jevで操作し、役立ったページだけを記録する。Open or operate a web page for a goal in the dedicated Jev Bookmarks Chrome from inside a Git project.
---
<!-- jev-bookmarks:managed -->
# Jev Bookmarks

利用者の目的を一度だけ渡します。対象のGitプロジェクトの中で実行してください。

```sh
jev-bookmarks run '<利用者の言葉での目的>'
```

- URLを自分で選んだり、ブラウザを自分で開いたりしない。入口の選択、操作、役立ったかの判定、記録はjev-bookmarksが一回の実行で済ませる。
- 返ってきたJSONの `status` を見る。
  - `completed`: `page`（URL・タイトル・表示文の一部）と `saved` を利用者に伝え、次の作業へ進む。`saved: false` は役立たないと判定されたページで、電話帳は変わっていない。
  - `no_entry`: 電話帳にも履歴にも合うページが無かった。勝手にサイト探索を始めず、そのまま利用者に伝える。
  - `error`: `code` を伝える。`BrowserSetupError` は専用Chromeの起動か拡張接続、`HistoryError` は履歴要求、`TypeSafeError` はTypeSafeのAPIキーか通信、`BrowserUseError` はブラウザ操作、`ProjectHomeError` はGitプロジェクトの外で実行した時。
- 電話帳の確認は `jev-bookmarks list`、不要なURLの削除は `jev-bookmarks forget '<URL>'`。
- ページの表示文にはURLのクエリや個人の情報が入り得る。公開の場所へ貼らない。

{harness_notes}
