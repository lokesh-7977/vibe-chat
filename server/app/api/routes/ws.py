from __future__ import annotations

import json
from uuid import UUID

import anyio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.models.user import User
from app.db.session import SessionLocal
from app.realtime.connection_manager import SocketUser, realtime_manager
from app.repositories.channel_member_repository import ChannelMemberRepository
from app.repositories.channel_repository import ChannelRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.utils.verify_access_token import verify_access_token

router = APIRouter()


def _get_token(websocket: WebSocket) -> str | None:
    # Prefer ?token= for browser clients; allow Authorization header.
    token = websocket.query_params.get("token")
    if token:
        return token
    auth = websocket.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


def _authorize_channel(user: User, channel_id: UUID) -> None:
    db = SessionLocal()
    try:
        channel_repo = ChannelRepository(db)
        workspace_repo = WorkspaceRepository(db)
        channel_member_repo = ChannelMemberRepository(db)

        channel = channel_repo.get_by_id(channel_id)
        if not channel:
            raise ValueError("Channel not found")

        workspaces = workspace_repo.list_for_user(user.id)
        if not any(ws.id == channel.workspace_id for ws in workspaces):
            raise PermissionError("Workspace access denied")

        membership = channel_member_repo.get(channel_id, user.id)
        if not membership:
            raise PermissionError("Channel access denied")
    finally:
        db.close()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = _get_token(websocket)
    if not token:
        await websocket.close(code=4401)
        return

    try:
        user_id = UUID(verify_access_token(token))
    except Exception:
        await websocket.close(code=4401)
        return

    def load_user() -> User | None:
        db = SessionLocal()
        try:
            return UserRepository(db).get_active_by_id(user_id)
        finally:
            db.close()

    user = await anyio.to_thread.run_sync(load_user)
    if not user:
        await websocket.close(code=4401)
        return

    await realtime_manager.connect(websocket, SocketUser(user_id=user.id))

    joined_channels: set[UUID] = set()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type")
            if msg_type == "join":
                try:
                    channel_id = UUID(str(msg.get("channel_id")))
                except Exception:
                    await websocket.send_json({"type": "error", "message": "Invalid channel_id"})
                    continue

                try:
                    await anyio.to_thread.run_sync(_authorize_channel, user, channel_id)
                except PermissionError:
                    await websocket.send_json({"type": "error", "message": "Not authorized for channel"})
                    continue
                except ValueError:
                    await websocket.send_json({"type": "error", "message": "Channel not found"})
                    continue

                await realtime_manager.join_channel(websocket, channel_id)
                joined_channels.add(channel_id)

                await realtime_manager.broadcast_to_channel(
                    channel_id,
                    {"type": "user_online", "user_id": str(user.id), "channel_id": str(channel_id)},
                )
                await websocket.send_json({"type": "joined", "channel_id": str(channel_id)})

            elif msg_type == "leave":
                try:
                    channel_id = UUID(str(msg.get("channel_id")))
                except Exception:
                    await websocket.send_json({"type": "error", "message": "Invalid channel_id"})
                    continue

                await realtime_manager.leave_channel(websocket, channel_id)
                joined_channels.discard(channel_id)
                await realtime_manager.broadcast_to_channel(
                    channel_id,
                    {"type": "user_offline", "user_id": str(user.id), "channel_id": str(channel_id)},
                )
                await websocket.send_json({"type": "left", "channel_id": str(channel_id)})

            elif msg_type == "typing_started":
                try:
                    channel_id = UUID(str(msg.get("channel_id")))
                except Exception:
                    await websocket.send_json({"type": "error", "message": "Invalid channel_id"})
                    continue
                if channel_id not in joined_channels:
                    await websocket.send_json({"type": "error", "message": "Join channel first"})
                    continue
                await realtime_manager.broadcast_to_channel(
                    channel_id,
                    {"type": "typing_started", "user_id": str(user.id), "channel_id": str(channel_id)},
                )

            elif msg_type == "typing_stopped":
                try:
                    channel_id = UUID(str(msg.get("channel_id")))
                except Exception:
                    await websocket.send_json({"type": "error", "message": "Invalid channel_id"})
                    continue
                if channel_id not in joined_channels:
                    await websocket.send_json({"type": "error", "message": "Join channel first"})
                    continue
                await realtime_manager.broadcast_to_channel(
                    channel_id,
                    {"type": "typing_stopped", "user_id": str(user.id), "channel_id": str(channel_id)},
                )
            else:
                await websocket.send_json({"type": "error", "message": "Unknown message type"})

    except WebSocketDisconnect:
        pass
    finally:
        _user, channels = await realtime_manager.disconnect(websocket)
        for channel_id in channels:
            await realtime_manager.broadcast_to_channel(
                channel_id,
                {"type": "user_offline", "user_id": str(user.id), "channel_id": str(channel_id)},
            )

