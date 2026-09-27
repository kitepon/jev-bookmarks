# 変更履歴

## 0.2.1 — 入口選びの修正

- 目的のページそのものが候補に無くても、そこへたどれる同じサイトの入口を選ぶようにした。これまでは候補が少ないと、たどれる入口があっても `no_entry` で止まることがあった。Jevへの問いに「数回のクリックでたどり着けるか」という入口の定義を明記し、`none` は目的と関係するサイトの候補が一つも無い時だけにした。
- 8つの試験ケース（たどれる入口だけがある3件、目的のページや関係するサイトの入口がある3件、関係するサイトが無い2件）で、旧版は5件、新版は3回とも8件すべて期待どおりに選んだ。

## 0.2.0 — Windows・Linux・4ハーネス対応

- WindowsでNative Messaging hostをHKCUへ登録し、起動ごとの鍵で相互認証する名前付きパイプで履歴を往復する。
- Windowsでは上流 `jev-ultrafast` の文字コードの都合でCLIをUTF-8モードで起動し直す。
- LinuxのNative Messagingマニフェストを `XDG_CONFIG_HOME` に従って置く。
- `jev-bookmarks harness install` / `harness status` を加え、Claude Code・Codex・Cursor・Grok Buildへ `run` の呼び方をスキルとして入れる。`status` にもスキルの状態を出す。
- 共通コード、OS適合（`platforms/`）、ハーネス適合（`harnesses/`）をファイル単位で分けた。
- CIをmacOS・Windows・Linuxで回す。
- Windowsで実Chrome履歴の往復、Linuxで試験用プロファイルの往復、3 OSで4ハーネスのスキル認識を確認した。WindowsとLinuxでの `run` 全体は未確認。

## 0.1.0 — macOSプレビュー

- 親AIから目的を一回受け取り、電話帳またはChrome履歴で開始URLを選び、上流Browser Useを実行する。
- 操作後のページを再観測し、Jevが役立つと判定したURLだけを記録する。
- 電話帳をGitプロジェクトごとの `jev-bookmark/bookmarks.json` に保存する。`list` と `forget` を提供する。
- Chrome履歴の全件コピーを作らず、要求中に候補を最大80件へ絞る。
- macOSで実履歴、MFクラウド会計の2画面、電話帳の再利用、プロジェクト間の分離を確認した。
- 開発用 `pytest` を9.0.3へ更新し、[一時ディレクトリ処理の脆弱性](https://github.com/advisories/GHSA-6w46-j5rx-g56g)に対応した。
- MITライセンスで公開した。

WindowsのNative Messaging登録と名前付きパイプは未実装。Linuxと新しい端末での導入は未検証。
