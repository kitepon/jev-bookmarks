# 変更履歴

## 0.3.3 — 選択欄のあるページで操作が拒否される問題を直す

- 依存するjev-ultrafastのフォークを `fd1a70b` に上げた。ラベルの無い選択欄の名前に全選択肢の文字列が入り、選択肢ごとの操作ラベルもそれを含むので、TypeSafeへの要求が選択肢数の2乗で大きくなっていた。67項目の地域選択欄があるページでは約360KBになり、`max_tokens_exceeded`（HTTP 400）で拒否されて `BrowserUseError` になっていた。

## 0.3.2 — 専用ChromeをWindowsとLinuxへ適合

- Linux: SSHやハーネスの実行環境に画面の変数（`WAYLAND_DISPLAY`・`DISPLAY`）が無いと専用Chromeが起動できなかった。ログイン中の画面セッションを持つユーザーのsystemdから（`systemd-run --user`）起動する。画面セッションが無い時は、15秒待たずに理由を示して止まる。
- Windows: Grok Buildはコマンドの終了時に子孫プロセスをまとめて止めるため、`run` が終わると専用Chromeも終了していた。SSHもジョブごと止める。ChromeをWMI（`Win32_Process.Create`）から起動し、呼び出し元の子孫にもジョブにも入れない。WMIが使えない時は直接起動する。
- 普段のChromeに0.2系の履歴拡張が残っていると、そのhostが履歴接続の待受先（Unixソケット・名前付きパイプ）を握り、専用Chromeの拡張が接続できなかった（Windowsで発生）。待受先と鍵ファイルを0.2系と分け、hostは専用Chromeの拡張から起動された時だけ待ち受ける。`install` は0.2系が普段のChrome向けに置いたマニフェスト（macOS・Linux）を消す。
- Windowsで専用拡張のファイルを複製すると改行がCRLFに変わっていた。バイト列のまま複製する。
- 起動に失敗した理由を `BrowserSetupError` の本文に含める。

## 0.3.1 — 履歴拡張の自動読込

- 固定IDの履歴拡張を、専用Chromeのloopback CDP endpointから起動ごとに読み込む。初回のデベロッパーモード操作をなくし、Chrome再起動後も履歴接続を自動で復元する。
- `install` と `run` は、拡張読込とNative Messaging hostへの接続確認までを正規入口の一回で行う。読込や接続に失敗した場合は `BrowserSetupError` で停止する。

## 0.3.0 — 専用Chromeへ統一

- 通常のGoogle ChromeをJev Bookmarks専用プロファイルで起動し、履歴拡張と `jev-ultrafast` の操作先を同じプロファイルへ固定した。
- Chromeが発行したloopback CDP endpointと専用Browser Harness名 `jev-bookmarks` を製品側で設定する。モデル設定に含まれる `BU_CDP_URL`・`BU_CDP_WS` は採用せず、他ツールの `default` daemonへ混線しない。
- `install` が専用Chromeの `chrome://extensions/` を開き、固定IDの専用拡張ディレクトリを表示する。初回だけ開発者モードから読み込み、以後は同じプロファイルへ保持する。
- `status` に専用Chrome、プロファイル、拡張ファイル、ブラウザ起動、履歴接続の状態をまとめた。

## 0.2.2 — jev-ultrafastをフォークから使う

- 上流 browser-use/jev-ultrafast に私たちの修正が入るまで、フォーク quolu/jev-ultrafast の確認済みの版（`e24e14f`）をコミットで固定して使う。フォークには、同梱ファイルをUTF-8で読む修正（Windowsのcp932で落ちる問題）と、初回のBLOCKED判定後に画面の変化を確かめる修正が入っている。
- WindowsでCLIをUTF-8モードで起動し直す理由を、上流の都合から「ハーネスへ返すJSONと読み書きするファイルをUTF-8にそろえる」に改めた。動きは変わらない。

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
