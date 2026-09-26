import json
import socket
import sys
from multiprocessing import AuthenticationError
from multiprocessing.connection import Client

from .paths import pipe_address, pipe_key_path, socket_path


class HistoryError(RuntimeError):
    pass


def _ask_unix(request: bytes) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(45)
        connection.connect(str(socket_path()))
        connection.sendall(request + b"\n")
        with connection.makefile("r", encoding="utf-8") as stream:
            return stream.readline(4_000_000)


def _ask_pipe(request: bytes) -> str:
    try:
        authkey = pipe_key_path().read_bytes()
    except FileNotFoundError as exc:
        raise ConnectionError("Chrome履歴のホストが起動していません") from exc
    with Client(pipe_address(), family="AF_PIPE", authkey=authkey) as connection:
        connection.send_bytes(request)
        if not connection.poll(45):
            raise TimeoutError("Chrome履歴のホストが応答しませんでした")
        return connection.recv_bytes(4_000_000).decode("utf-8")


def available() -> bool:
    """履歴接続のホストが待ち受けているかの目安。"""
    if sys.platform == "win32":
        return pipe_key_path().exists()
    return socket_path().exists()


def search(goal: str) -> list[dict]:
    request = json.dumps({"type": "search", "goal": goal}, ensure_ascii=False).encode("utf-8")
    try:
        reply = _ask_pipe(request) if sys.platform == "win32" else _ask_unix(request)
    except (OSError, EOFError, TimeoutError, AuthenticationError) as exc:
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
