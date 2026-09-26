# Jev Bookmarks

Chromeで実際に訪れたページから、頼みごとに合う入口を見つける製品。

## 合意した基本動作

1. 親AIが目的を一度渡す。初めての頼みごとはChromeの閲覧履歴から候補を絞り、Jevが実際に訪れたURLの中から開始URLを選ぶ。
2. Jev Bookmarksが上流Browser Useを動かし、操作後にJevが役立つと判定したページのURLを小さな電話帳へ保存する。役立たなければ保存せず親AIへ結果を返す。
3. 次回は電話帳から探し、該当がなければ閲覧履歴を探す。電話帳の記録はChrome履歴の保存期間を超えて残す。

サイト巡回や全履歴の一括保存は行わない。Jevへ履歴全件を渡さず、URLは候補の実値から選ぶ。

## 導入

Python 3.12、`uv`、Google Chromeを使う。現在の実機導入先はmacOS。拡張はChromeの通常の開発者向け画面から読み込む。

```sh
uv sync
uv tool install --editable .
jev-bookmarks install \
  --typesafe-env /path/to/typesafe.env \
  --browser-env /path/to/jev-ultrafast.env
```

Chromeで `chrome://extensions` を開き、デベロッパーモードを有効にして、このリポジトリの `extension/` を「パッケージ化されていない拡張機能」として読み込む。表示された拡張IDは `jev-bookmarks install` の出力と一致する必要がある。拡張は `history` と `nativeMessaging` の権限を使う。

```sh
jev-bookmarks status
jev-bookmarks run 'Example Domainのページを表示する'
jev-bookmarks list
```

`run` は電話帳、必要ならChrome履歴から入口を選び、上流 `jev-ultrafast` の操作後にJevが有用性を判定する。役立つと判定した時だけ、観測したページのURLを電話帳へ保存する。親AIにはページ、操作結果、有用性判定、保存有無をまとめて返す。

電話帳はユーザー専用のローカルデータに置く。Chrome履歴全件は永続コピーせず、Jevへは最大80件の候補情報だけを渡す。操作後の判定には表示情報の一部を渡すため、機密性の高いページを扱う前に送信範囲を確認する。

## 現在地

ローカルの電話帳、履歴拡張、Native Messaging、Jevの選択と判定、`jev-ultrafast` 連携を実装した。このMacのChromeに拡張を読み込み、実履歴から80件へ絞った候補の取得と、空の電話帳から履歴選択・ブラウザ操作・有用性判定・URL保存まで一回の `run` で確認した。MFクラウド会計では登録済み口座一覧と明細一覧を履歴から選び、操作後に役立つと判定できた。電話帳からの再利用は履歴検索を使わない条件でも確認した。WindowsのNative Messaging登録と名前付きパイプは未実装。

[製品設計](docs/design.md)にシーケンスと受入条件を記録している。
