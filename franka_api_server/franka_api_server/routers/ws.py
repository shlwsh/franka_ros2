from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import asyncio
from ..config import settings
from ..ros_bridge import RosBridge

router = APIRouter(tags=["websocket"])

async def get_ws_api_key(websocket: WebSocket, api_key: str = None):
    if not settings.auth_enabled:
        return True
    if api_key == settings.api_key:
        return True
    await websocket.close(code=1008)
    return False

@router.websocket("/ws/robot_state")
async def websocket_robot_state(websocket: WebSocket, api_key: str = None):
    if not await get_ws_api_key(websocket, api_key):
        return
    
    await websocket.accept()
    bridge = RosBridge.get_instance()
    
    sleep_time = 1.0 / settings.ws_publish_rate
    
    try:
        while True:
            if bridge.robot_state:
                data = {
                    "type": "robot_state",
                    "mode": bridge.robot_state.robot_mode
                }
                # Simplification for demo
                await websocket.send_json(data)
            await asyncio.sleep(sleep_time)
    except WebSocketDisconnect:
        pass

@router.websocket("/ws/joint_states")
async def websocket_joint_states(websocket: WebSocket, api_key: str = None):
    if not await get_ws_api_key(websocket, api_key):
        return
        
    await websocket.accept()
    bridge = RosBridge.get_instance()
    sleep_time = 1.0 / settings.ws_publish_rate
    
    try:
        while True:
            if bridge.joint_state:
                data = {
                    "type": "joint_states",
                    "data": {
                        "positions": list(bridge.joint_state.position),
                        "velocities": list(bridge.joint_state.velocity)
                    }
                }
                await websocket.send_json(data)
            await asyncio.sleep(sleep_time)
    except WebSocketDisconnect:
        pass
