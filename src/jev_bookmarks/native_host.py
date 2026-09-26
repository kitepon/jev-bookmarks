import json
import os
import secrets
import socket
import socketserver
import stat
import sys
import threading
import uuid
from multiprocessing import AuthenticationError
from multiprocessing.connection import Client, Listener

from .paths import pipe_address, pipe_key_path, socket_path


class Bridge:
    def __init__(self):
        self.pending: dict[str, tuple[threading.Event, list[dict]]] = {}
        self.pending_lock = threading.Lock()
        self.output_lock = threading.Lock()

    def send(self, payload: dict) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if len(encoded) > 1_000_000:
            raise ValueError("Native Messagingの送信上限を超えました")
        with self.output_lock:
            sys.stdout.buffer.write(len(encoded).to_bytes(4, sys.byteorder))
            sys.stdout.buffer.write(encoded)
            sys.stdout.buffer.flush()

    def forward(self, goal: str) -> dict:
        request_id = uuid.uuid4().hex
        event = threading.Event()
        result: list[dict] = []
        with self.pending_lock:
            self.pending[request_id] = (event, result)
        try:
            self.send({"id": request_id, "type": "search", "goal": goal})
            if not event.wait(40):
                return {"error": "Chrome拡張が履歴検索に応答しませんでした"}
            return result[0]
        finally:
            with self.pending_lock:
                self.pending.pop(request_id, None)

    def receive(self, payload: dict) -> None:
        request_id = payload.get("id")
        with self.pending_lock:
            pending = self.pending.get(request_id)
        if pending:
            event, result = pending
            result.append(payload)
            event.set()


def answer(bridge: Bridge, raw: bytes) -> bytes:
    try:
        request = json.loads(raw)
        if request.get("type") != "search" or not isinstance(request.get("goal"), str):
            raise ValueError("不正な履歴検索要求です")
        response = bridge.forward(request["goal"])
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        response = {"error": str(exc)}
    return json.dumps(response, ensure_ascii=False).encode("utf-8")


class Handler(socketserver.StreamRequestHandler):
    bridge: Bridge

    def handle(self) -> None:
        self.wfile.write(answer(self.bridge, self.rfile.readline(64_000)) + b"\n")


if sys.platform != "win32":

    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True


def _read_exact(length: int) -> bytes | None:
    parts = bytearray()
    while len(parts) < length:
        chunk = sys.stdin.buffer.read(length - len(parts))
        if not chunk:
            return None
        parts.extend(chunk)
    return bytes(parts)


def _prepare_socket() -> str:
    path = socket_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.stat().st_uid != os.getuid() or stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise RuntimeError("履歴接続ディレクトリの所有者か権限が不正です")
    os.chmod(path.parent, 0o700)
    if path.exists():
        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            probe.connect(str(path))
        except OSError:
            path.unlink()
        else:
            raise RuntimeError("Chrome履歴のホストが既に稼働しています")
        finally:
            probe.close()
    return str(path)


def _read_native_messages(bridge: Bridge) -> None:
    while True:
        header = _read_exact(4)
        if header is None:
            break
        length = int.from_bytes(header, sys.byteorder)
        if length > 64 * 1024 * 1024:
            raise RuntimeError("Native Messagingの受信上限を超えました")
        raw = _read_exact(length)
        if raw is None:
            break
        bridge.receive(json.loads(raw))


def _serve_unix(bridge: Bridge) -> None:
    path = _prepare_socket()
    Handler.bridge = bridge
    with Server(path, Handler) as server:
        os.chmod(path, 0o600)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            _read_native_messages(bridge)
        finally:
            server.shutdown()
            worker.join()
            os.unlink(path)


def _write_pipe_key() -> bytes:
    """同じユーザーのコマンドだけが読める場所へ、この起動限りの鍵を置く。"""
    path = pipe_key_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            with Client(pipe_address(), family="AF_PIPE", authkey=path.read_bytes()):
                pass
        except (OSError, EOFError, AuthenticationError):
            path.unlink()
        else:
            raise RuntimeError("Chrome履歴のホストが既に稼働しています")
    authkey = secrets.token_bytes(32)
    with open(path, "xb") as handle:
        handle.write(authkey)
    return authkey


def _serve_pipe_client(bridge: Bridge, connection) -> None:
    with connection:
        try:
            raw = connection.recv_bytes(64_000)
        except (OSError, EOFError):
            return
        try:
            connection.send_bytes(answer(bridge, raw))
        except OSError:
            pass


def _accept_pipe(bridge: Bridge, listener: Listener, closing: threading.Event) -> None:
    while not closing.is_set():
        try:
            connection = listener.accept()
        except (OSError, EOFError, AuthenticationError):
            continue
        threading.Thread(target=_serve_pipe_client, args=(bridge, connection), daemon=True).start()


def _serve_pipe(bridge: Bridge) -> None:
    authkey = _write_pipe_key()
    closing = threading.Event()
    try:
        listener = Listener(pipe_address(), family="AF_PIPE", authkey=authkey)
        worker = threading.Thread(target=_accept_pipe, args=(bridge, listener, closing), daemon=True)
        worker.start()
        try:
            _read_native_messages(bridge)
        finally:
            closing.set()
            listener.close()
    finally:
        pipe_key_path().unlink(missing_ok=True)


def main() -> None:
    bridge = Bridge()
    if sys.platform == "win32":
        _serve_pipe(bridge)
    else:
        _serve_unix(bridge)


if __name__ == "__main__":
    main()
