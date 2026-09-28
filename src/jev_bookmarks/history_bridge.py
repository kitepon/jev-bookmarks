import json
from multiprocessing import AuthenticationError

from . import platforms


class HistoryError(RuntimeError):
    pass


def available() -> bool:
    """履歴接続のホストが要求へ応答できるか確認する。"""
    request = json.dumps({"type": "ping"}).encode("utf-8")
    try:
        reply = platforms.current().ask(request)
        return json.loads(reply).get("connected") is True
    except (AuthenticationError, EOFError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def search(goal: str) -> list[dict]:
    request = json.dumps({"type": "search", "goal": goal}, ensure_ascii=False).encode("utf-8")
    try:
        reply = platforms.current().ask(request)
    except OSError as exc:
        raise HistoryError(f"Chrome履歴の接続に失敗しました: {exc}") from exc
    if not reply:
        raise HistoryError("Chrome履歴の接続が閉じました")
    try:
        response = json.loads(reply)
        if response.get("error"):
            raise HistoryError(f"Chrome履歴の検索に失敗しました: {response['error']}")
        candidates = response["candidates"]
        if not isinstance(candidates, list):
            raise ValueError("候補が配列ではありません")
        return candidates
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise HistoryError("Chrome履歴の応答形式が不正です") from exc
