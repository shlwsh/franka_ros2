from fastapi import APIRouter, Depends
from ..auth import get_api_key
from ..ros_bridge import RosBridge

router = APIRouter(tags=["status"])

@router.get("/status/joints")
async def get_joints(api_key: str = Depends(get_api_key)):
    bridge = RosBridge.get_instance()
    if bridge.joint_state:
        return {
            "joint_positions": list(bridge.joint_state.position),
            "joint_velocities": list(bridge.joint_state.velocity),
            "joint_efforts": list(bridge.joint_state.effort),
            "joint_names": list(bridge.joint_state.name)
        }
    return {"message": "No joint state received yet"}

@router.get("/status/robot")
async def get_robot_state(api_key: str = Depends(get_api_key)):
    bridge = RosBridge.get_instance()
    if bridge.robot_state:
        # Simplification for demo purposes. 
        # A full implementation would serialize all fields of FrankaRobotState.
        return {
            "robot_mode": bridge.robot_state.robot_mode,
            "current_errors": bridge.robot_state.current_errors.errors if hasattr(bridge.robot_state.current_errors, 'errors') else "N/A"
        }
    return {"message": "No robot state received yet"}
