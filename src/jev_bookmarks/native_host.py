import json
import sys
import threading
import uuid

from . import platforms


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


def _read_exact(length: int) -> bytes | None:
    parts = bytearray()
    while len(parts) < length:
        chunk = sys.stdin.buffer.read(length - len(parts))
        if not chunk:
            return None
        parts.extend(chunk)
    return bytes(parts)


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


def main() -> None:
    bridge = Bridge()
    platforms.current().serve(lambda raw: answer(bridge, raw), lambda: _read_native_messages(bridge))


if __name__ == "__main__":
    main()
