# 調査した一次資料

出典: 下記の公式資料・上流リポジトリ。確認日: 2026-09-26。確度: リンク先の公開仕様は高、実機への適用は [製品設計](../docs/design.md) の検証記録を参照。

- [Chrome History API](https://developer.chrome.com/docs/extensions/reference/api/history): `history` 権限、`search` の返値と省略値、訪問イベント。
- [Chrome Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging): 拡張とローカルホストの接続、許可する拡張ID、メッセージの往復。
- [TypeSafe Choice](https://docs.typesafe.ai/primitives/choice): 有限集合からの選択、確率分布、`confidence` の意味。
- [TypeSafe API](https://docs.typesafe.ai/api): System Oneの `state`、`questions`、モデル指定。
- [jev-ultrafast README](https://github.com/browser-use/jev-ultrafast): `Agent(開始URL, 目的)`、自律操作ループ、`DONE` 後の独立検証が必要なこと。
- [pytestのセキュリティ情報](https://github.com/advisories/GHSA-6w46-j5rx-g56g)と[9.0.3のリリース](https://github.com/pytest-dev/pytest/releases/tag/9.0.3): 開発用依存の修正版を確認。

実装と実機接続の検証結果は [README](../README.md) と [製品設計](../docs/design.md) に記録する。公開とリリースの履歴は [CHANGELOG](../CHANGELOG.md) に記録する。
