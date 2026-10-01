import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from helios.core.chat.engine import ChatEngine, ChatMessage
from helios.infrastructure.database import async_session_maker
from helios.models.host import Host
from helios.models.project import Project

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic model to strictly validate incoming WebSocket messages
class WSIncomingMessage(BaseModel):
    type: str = "message"
    content: str
    message_id: str | None = None
    history: list[dict] | None = None


async def build_recon_context(project_id: str) -> str:
    """Build a concise host and service summary limited to one project."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Host)
                .where(Host.project_id == project_id)
                .options(selectinload(Host.services))
            )
            hosts = result.scalars().unique().all()

            if not hosts:
                return ""

            summary_lines = []
            for host in hosts:
                open_ports = [
                    f"{s.port}/{s.protocol} ({s.name or 'unknown'})"
                    for s in host.services
                    if s.state == "open"
                ]
                if not open_ports:
                    continue

                host_str = f"- Host {host.ip}"
                if host.hostname:
                    host_str += f" ({host.hostname})"
                if host.os:
                    host_str += f" running {host.os}"

                host_str += f". Open Ports: {', '.join(open_ports)}"
                summary_lines.append(host_str)

            return "\n".join(summary_lines)
    except Exception as e:
        logger.error(f"Failed to build recon context: {e}")
        return ""


import jwt

from helios.config import get_settings
from helios.models.user import User


@router.websocket("/stream/{project_id}")
async def chat_stream(websocket: WebSocket, project_id: str):
    ticket = websocket.query_params.get("ticket")
    if not ticket:
        await websocket.close(code=1008, reason="Missing ticket")
        return

    settings = get_settings()
    try:
        payload = jwt.decode(ticket, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "ws-ticket":
            await websocket.close(code=1008, reason="Invalid ticket type")
            return
        username = payload.get("sub")
    except jwt.InvalidTokenError:
        await websocket.close(code=1008, reason="Invalid ticket")
        return

    async with async_session_maker() as session:
        user_result = await session.execute(
            select(User).where(User.username == username)
        )
        user = user_result.scalars().first()
        if not user:
            await websocket.close(code=1008, reason="Invalid user")
            return

        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalars().first()

        if not project:
            await websocket.close(code=1008, reason="A valid project is required")
            return

        if project.created_by != user.id:
            await websocket.close(
                code=1008, reason="Not authorized to access this project"
            )
            return

    await websocket.accept()
    connection_id = str(uuid.uuid4())[:8]
    logger.info(f"[WS {connection_id}] Client connected.")

    # Retrieve the pre-initialized engine from app state (saves RAM/VRAM)
    engine: ChatEngine = websocket.app.state.chat_engine

    try:
        while True:
            raw_data = await websocket.receive_text()

            # Validate incoming JSON safely
            try:
                msg = WSIncomingMessage.model_validate_json(raw_data)
            except ValidationError as e:
                logger.warning(f"[WS {connection_id}] Invalid message format: {e}")
                await websocket.send_json(
                    {"type": "error", "error": "Invalid message format"}
                )
                continue

            if msg.type != "message" or not msg.content.strip():
                continue

            assistant_msg_id = str(uuid.uuid4())

            # Format history for the engine
            history = None
            if msg.history:
                history = [
                    ChatMessage(
                        role=m.get("role", "user"), content=m.get("content", "")
                    )
                    for m in msg.history
                ]

            # 1. Fetch current reconnaissance data context
            recon_context = await build_recon_context(project_id)

            # 2. Send START event (Crucial for frontend to create the message bubble)
            await websocket.send_json({"type": "start", "message_id": assistant_msg_id})

            try:
                # 3. Stream tokens using standard chat engine
                async for token in engine.generate_response(
                    msg.content,
                    history=history,
                    recon_context=recon_context,
                    project_id=project_id,
                ):
                    await websocket.send_json(
                        {
                            "type": "token",
                            "message_id": assistant_msg_id,
                            "content": token,
                        }
                    )

                # 4. Send DONE event
                await websocket.send_json(
                    {"type": "done", "message_id": assistant_msg_id}
                )

            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(
                    f"[WS {connection_id}] Error during generation: {e}", exc_info=True
                )
                await websocket.send_json(
                    {
                        "type": "error",
                        "message_id": assistant_msg_id,
                        "error": "Generation failed. Please try again.",
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"[WS {connection_id}] Client disconnected normally.")
    except Exception as e:
        logger.error(
            f"[WS {connection_id}] Unexpected WebSocket error: {e}", exc_info=True
        )
