import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from helios.core.chat.engine import ChatEngine, ChatMessage
from helios.core.agents.manager import agent_manager
from helios.infrastructure.database import async_session_maker
from helios.models.host import Host

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic model to strictly validate incoming WebSocket messages
class WSIncomingMessage(BaseModel):
    type: str = "message"
    content: str
    message_id: Optional[str] = None
    history: Optional[List[dict]] = None

async def build_recon_context() -> str:
    """Queries the database to build a concise summary of known hosts and services."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Host).options(selectinload(Host.services))
            )
            hosts = result.scalars().unique().all()
            
            if not hosts:
                return ""
                
            summary_lines = []
            for host in hosts:
                open_ports = [f"{s.port}/{s.protocol} ({s.name or 'unknown'})" for s in host.services if s.state == 'open']
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

@router.websocket("/stream")
async def chat_stream(websocket: WebSocket):
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
                await websocket.send_json({"type": "error", "error": "Invalid message format"})
                continue

            if msg.type != "message" or not msg.content.strip():
                continue

            assistant_msg_id = str(uuid.uuid4())
            
            # Format history for the engine
            history = None
            if msg.history:
                history = [
                    ChatMessage(role=m.get("role", "user"), content=m.get("content", "")) 
                    for m in msg.history
                ]

            # 1. Fetch current reconnaissance data context
            recon_context = await build_recon_context()

            # 2. Send START event (Crucial for frontend to create the message bubble)
            await websocket.send_json({
                "type": "start",
                "message_id": assistant_msg_id
            })

            # Check if this is an explicit agent/tool execution request
            is_agent_request = any(keyword in msg.content.lower() for keyword in ["execute", "run", "scan", "agent"])
            
            try:
                if is_agent_request:
                    async def update_status(status_text: str):
                        await websocket.send_json({
                            "type": "agent_status",
                            "message_id": assistant_msg_id,
                            "content": status_text
                        })
                        
                    final_result = await agent_manager.execute_task(msg.content, update_status)
                    
                    # Send the final result as the message content
                    await websocket.send_json({
                        "type": "token",
                        "message_id": assistant_msg_id,
                        "content": final_result
                    })
                else:
                    # 3. Stream tokens using standard chat engine
                    async for token in engine.generate_response(msg.content, history=history, recon_context=recon_context):
                        await websocket.send_json({
                            "type": "token",
                            "message_id": assistant_msg_id,
                            "content": token
                        })
                
                # 4. Send DONE event
                await websocket.send_json({
                    "type": "done",
                    "message_id": assistant_msg_id
                })
                
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(f"[WS {connection_id}] Error during generation: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message_id": assistant_msg_id,
                    "error": "Generation failed. Please try again."
                })

    except WebSocketDisconnect:
        logger.info(f"[WS {connection_id}] Client disconnected normally.")
    except Exception as e:
        logger.error(f"[WS {connection_id}] Unexpected WebSocket error: {e}", exc_info=True)