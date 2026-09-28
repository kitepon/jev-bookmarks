"""macOSとLinuxが共有するUnixソケットの履歴接続。"""

import hashlib
import os
import socket
import socketserver
import stat
import threading
from collections.abc import Callable
from pathlib import Path


# 0.2系のhost（普段のChromeに残った旧拡張が起動したもの）と待受先を分ける。
CHANNEL = "dedicated-chrome"


def socket_path(data_dir: Path) -> Path:
    identity = hashlib.sha256(f"{data_dir.resolve()}\0{CHANNEL}".encode()).hexdigest()[:12]
    return Path("/tmp") / f"jev-bookmarks-{os.getuid()}-{identity}" / "bridge.sock"


def browser_runtime_dir(data_dir: Path) -> Path:
    return socket_path(data_dir).parent / "browser-harness"


def _prepare_socket(path: Path) -> str:
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


def serve(path: Path, answer: Callable[[bytes], bytes], pump: Callable[[], None]) -> None:
    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True

    class Handler(socketserver.StreamRequestHandler):
        def handle(self) -> None:
            self.wfile.write(answer(self.rfile.readline(64_000)) + b"\n")

    address = _prepare_socket(path)
    with Server(address, Handler) as server:
        os.chmod(address, 0o600)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            pump()
        finally:
            server.shutdown()
            worker.join()
            os.unlink(address)


def ask(path: Path, request: bytes) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(45)
        connection.connect(str(path))
        connection.sendall(request + b"\n")
        with connection.makefile("r", encoding="utf-8") as stream:
            return stream.readline(4_000_000)
