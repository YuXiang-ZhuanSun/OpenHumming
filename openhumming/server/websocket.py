from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(tags=["websocket"])


@router.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            message = str(payload.get("message", ""))
            session_id = payload.get("session_id")
            result = websocket.app.state.runtime.respond(session_id, message)
            await websocket.send_json(
                {
                    "session_id": result.session_id,
                    "response": result.response,
                    "actions": result.actions,
                    "memory_updates": result.memory_updates,
                    "memory_proposals": [
                        {
                            "target": proposal.target,
                            "section": proposal.section,
                            "content": proposal.content,
                            "reason": proposal.reason,
                            "confidence": proposal.confidence,
                            "operation": proposal.operation,
                            "anchor": proposal.anchor,
                            "category": proposal.category,
                        }
                        for proposal in result.memory_proposals
                    ],
                    "applied_memory_updates": [
                        {
                            "target": update.target,
                            "section": update.section,
                            "content": update.content,
                            "path": str(update.path),
                            "operation": update.operation,
                            "replaced": update.replaced,
                        }
                        for update in result.applied_memory_updates
                    ],
                    "created_skill_draft": result.created_skill_draft,
                }
            )
    except WebSocketDisconnect:
        return
