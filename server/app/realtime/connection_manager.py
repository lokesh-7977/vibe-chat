from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import WebSocket


@dataclass(frozen=True)
class SocketUser:
    user_id: UUID


class RealtimeManager:
    def __init__(self) -> None:
        self._channel_sockets: dict[UUID, set[WebSocket]] = {}
        self._socket_user: dict[WebSocket, SocketUser] = {}
        self._socket_channels: dict[WebSocket, set[UUID]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user: SocketUser) -> None:
        await websocket.accept()
        async with self._lock:
            self._socket_user[websocket] = user
            self._socket_channels[websocket] = set()

    async def disconnect(self, websocket: WebSocket) -> tuple[SocketUser | None, set[UUID]]:
        async with self._lock:
            user = self._socket_user.pop(websocket, None)
            channels = self._socket_channels.pop(websocket, set())
            for channel_id in channels:
                sockets = self._channel_sockets.get(channel_id)
                if sockets:
                    sockets.discard(websocket)
                    if not sockets:
                        self._channel_sockets.pop(channel_id, None)
            return user, channels

    async def join_channel(self, websocket: WebSocket, channel_id: UUID) -> None:
        async with self._lock:
            self._socket_channels.setdefault(websocket, set()).add(channel_id)
            self._channel_sockets.setdefault(channel_id, set()).add(websocket)

    async def leave_channel(self, websocket: WebSocket, channel_id: UUID) -> None:
        async with self._lock:
            self._socket_channels.get(websocket, set()).discard(channel_id)
            sockets = self._channel_sockets.get(channel_id)
            if sockets:
                sockets.discard(websocket)
                if not sockets:
                    self._channel_sockets.pop(channel_id, None)

    async def broadcast_to_channel(self, channel_id: UUID, event: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._channel_sockets.get(channel_id, set()))

        if not sockets:
            return

        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            **event,
        }

        # Fan-out best effort; drop dead sockets.
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._socket_channels.pop(ws, None)
                    self._socket_user.pop(ws, None)
                for ws in dead:
                    for sockets_set in self._channel_sockets.values():
                        sockets_set.discard(ws)


realtime_manager = RealtimeManager()

