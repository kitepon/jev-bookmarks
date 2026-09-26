import json
import socket

from .paths import socket_path


class HistoryError(RuntimeError):
    pass


def search(goal: str) -> list[dict]:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(45)
            connection.connect(str(socket_path()))
            connection.sendall((json.dumps({"type": "search", "goal": goal}, ensure_ascii=False) + "\n").encode())
            with connection.makefile("r", encoding="utf-8") as stream:
                reply = stream.readline(4_000_000)
    except (OSError, TimeoutError) as exc:
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
