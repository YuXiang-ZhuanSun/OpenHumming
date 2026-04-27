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
                }
            )
    except WebSocketDisconnect:
        return
