<p align="center"><img src=".github/og.png" alt="Chrome履歴から入口を選び、Jevが操作し、役立ったページをプロジェクトの電話帳に残す" width="100%"></p>

# Jev Bookmarks

[![CI](https://github.com/quolu/jev-bookmarks/actions/workflows/ci.yml/badge.svg)](https://github.com/quolu/jev-bookmarks/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> Chrome履歴から目的に合うページを選び、Jevで操作し、役立ったURLだけをGitプロジェクトごとの電話帳に残すCLI。

[English summary](README.en.md) · [設計と受入条件](docs/design.md)

**プレビュー版です。** macOS・Windows・Linuxで動き、Claude Code・Codex・Cursor・Grok Buildから呼べます。Chrome拡張は開発者モードで読み込みます。

## 使い方を30秒で

導入後、対象のGitプロジェクト内で目的を一度だけ渡します。

```sh
cd /path/to/your-project
jev-bookmarks run 'Example Domainのページを表示する'
```

```json
{
  "status": "completed",
  "source": "history",
  "page": {"url": "https://example.com/", "title": "Example Domain"},
  "operation_status": "done",
  "useful": true,
  "saved": true
}
```

上は応答の抜粋です。実際のJSONには選択したURL、操作回数、有用性の確率なども入ります。役立たないページは保存せず、ページと操作結果を返します。

```mermaid
flowchart LR
    A[目的文] --> B[プロジェクトの電話帳]
    B -->|候補がない| C[Chrome履歴]
    B -->|入口URL| E[jev-ultrafast]
    C --> D[Jevが入口URLを選ぶ]
    D --> E
    E --> F[操作後のページを再観測]
    F --> G{Jevが役立つと判定？}
    G -->|はい| H[電話帳に記録]
    G -->|いいえ| I[保存せず結果を返す]
```

| 方法 | 入口の選択 | 操作後の確認 | 履歴が消えた後 |
| --- | --- | --- | --- |
| Chrome履歴を直接開く | 利用者が探す | 利用者が判断する | 履歴の保持期間に依存 |
| 通常のブックマーク | 利用者が登録する | 利用者が判断する | 残る |
| Jev Bookmarks | 目的文からJevが選ぶ | Jevがページを判定する | 役立ったURLだけプロジェクトに残る |

## 導入

Python 3.12、`uv`、Git、Google Chrome、[TypeSafe](https://docs.typesafe.ai/)のAPIキー、[jev-ultrafast](https://github.com/browser-use/jev-ultrafast)が使うブラウザ接続とモデル設定が必要です。手順はmacOS・Windows・Linuxで同じです（Windowsは PowerShell で実行します）。

```sh
git clone https://github.com/quolu/jev-bookmarks.git
cd jev-bookmarks
uv sync --locked
uv tool install --editable .
jev-bookmarks install --typesafe-env /path/to/typesafe.env --browser-env /path/to/jev-ultrafast.env
jev-bookmarks harness install
```

`typesafe.env` には `TYPESAFE_API_KEY`、ブラウザ用のenvファイルには上流が必要とするモデル設定とChromeへの接続設定を用意します。秘密の値をこのリポジトリに置かないでください。`install` は端末共通の設定とChrome Native Messaging hostを登録し、拡張ディレクトリと固定拡張IDを表示します。Windowsではマニフェストの場所を `HKCU\Software\Google\Chrome\NativeMessagingHosts\ai.jevbookmarks.history` に登録します。

普段使うChromeの `chrome://extensions` でデベロッパーモードを有効にし、このリポジトリの `extension/` を「パッケージ化されていない拡張機能」として読み込みます。表示されたIDが `install` の出力と一致することを確認してください。拡張は `history` と `nativeMessaging` の権限を使います。上流のBrowser Useも同じChromeプロファイルへ接続する設定が必要です。

```sh
cd /path/to/your-project
jev-bookmarks status
jev-bookmarks run '探したいページで行うこと'
jev-bookmarks list
jev-bookmarks forget 'https://example.com/'
```

`run`・`list`・`forget` は、呼出し元のGitプロジェクトのルートを見つけます。`status` の `history_connected` は履歴接続のホストが待ち受けているかの目安です。実際の履歴往復は `run` で確認できます。

### ハーネスから使う

`jev-bookmarks harness install` は、見つかったハーネスへ `jev-bookmarks run` の呼び方をスキルとして入れます。以後は「MFの口座一覧を開いて」のように頼むと、ハーネスが目的を一度だけ渡します。特定のハーネスだけに入れる時は `jev-bookmarks harness install claude codex` のように名前を並べます。状態は `jev-bookmarks harness status` で見られます。

| ハーネス | スキルの置き場 | ハーネスごとの注意（スキルに書き込み済み） |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/jev-bookmarks/` | Bashのタイムアウトを10分にして待つ |
| Codex | `$CODEX_HOME/skills/jev-bookmarks/`（既定 `~/.codex`） | ネットワークと履歴接続を使うため、サンドボックスの外で実行する |
| Cursor | `~/.cursor/skills/jev-bookmarks/` | サンドボックス内なら外での実行を求める |
| Grok Build | `~/.grok/skills/jev-bookmarks/` | 終了まで待つ |

スキルは何度入れ直しても同じ結果になります。自分で置いた同名のスキルは上書きしません。

## 保存と外部送信

- 電話帳は `<プロジェクトルート>/jev-bookmark/bookmarks.json` に保存します。サブディレクトリからの呼出しも同じ電話帳を使います。生成する `.gitignore` はJSONと一時ファイルをGitの追跡対象から外します。
- 電話帳には目的文、観測ページの完全なURL、タイトル、判定時刻が残ります。URLのクエリ文字列にも情報が入り得るので、`list` で確認し、不要なURLは `forget` で削除してください。以前の端末共通の電話帳は自動移行せず、そのまま残します。
- Chrome履歴は要求時に拡張から読み、全件を永続コピーしません。JevへのURL選択では最大80件の候補のタイトル・ホスト名・パスを送ります。操作後の判定ではページの表示文の一部もTypeSafeへ送ります。
- Browser Useが扱うページ情報は、上流のモデル設定にも従います。機密ページを扱う前に、利用するモデルと送信範囲を確認してください。

## 対応状況

| 環境 | 状態 |
| --- | --- |
| macOS + Google Chrome | 実履歴とログイン済みページで一回の `run` を確認済み |
| Windows 11 + Google Chrome | 実Chrome履歴→拡張→名前付きパイプ→CLIの往復を確認済み |
| Linux (Ubuntu 26.04) + Google Chrome | 試験用プロファイルで拡張→Unixソケット→CLIの往復を確認済み |

| ハーネス | 状態 |
| --- | --- |
| Claude Code・Codex・Cursor・Grok Build | 3 OSでスキルを入れ、各ハーネスが認識することを確認済み |

WindowsとLinuxでは、TypeSafeとブラウザ操作まで含めた `run` の実機確認がまだです。

<details>
<summary>実機確認と既知の限界</summary>

このMacのChromeに拡張を読み込み、実履歴から80件へ絞った候補を取得した。空の電話帳からURL選択、ブラウザ操作、操作後の再観測、Jevの判定、URL保存まで一回の `run` で確認した。MFクラウド会計の登録済み口座一覧と明細一覧でも目的に合うページを選べた。履歴検索を使わない電話帳の再利用と、役立たないページを保存しない動作も確認した。

二つの一時Gitプロジェクトを作り、片方のサブディレクトリからの実行でそのプロジェクトだけに電話帳ができることを実機で確認した。1万件超の履歴を模した試験では、期間を分割して古い一致ページを取得し、Jevへ渡す候補を80件に制限した。

WindowsとLinuxでの `run` 全体、MFの幅広い目的での判定精度は未検証です。Chrome履歴を読むプロファイルとBrowser Useが操作するプロファイルの一致も、設定上の要件として残ります。

</details>

不具合や改善案は [Issues](https://github.com/quolu/jev-bookmarks/issues) へ。個人のURL、ページ本文、APIキーを公開Issueに貼らないでください。[開発への参加](CONTRIBUTING.md)と[セキュリティ報告](SECURITY.md)も参照してください。

## コードの構成

共通コード、OS適合、ハーネス適合をファイル単位で分けています。

| 区分 | ファイル |
| --- | --- |
| 共通 | `cli.py`、`runner.py`、`typesafe.py`、`phonebook.py`、`settings.py`、`paths.py`、`install.py`、`native_host.py`、`history_bridge.py` |
| OS適合 | `platforms/macos.py`、`platforms/windows.py`、`platforms/linux.py`（macOSとLinuxのUnixソケットは `platforms/posix.py`） |
| ハーネス適合 | `harnesses/claude.py`、`harnesses/codex.py`、`harnesses/cursor.py`、`harnesses/grok.py`（スキルの共通本文は `harnesses/skill.md`） |

各OS・各ハーネスが満たす約束は、それぞれの `__init__.py` に書いています。

## ライセンス

[MIT License](LICENSE)。
