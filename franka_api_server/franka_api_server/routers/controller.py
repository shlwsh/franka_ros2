from fastapi import APIRouter, Depends
from ..auth import get_api_key

router = APIRouter(tags=["controller"])

@router.get("/controller/list")
async def list_controllers(api_key: str = Depends(get_api_key)):
    # Simplification: a full implementation would call controller_manager list_controllers service
    return {
        "controllers": [
            {"name": "joint_state_broadcaster", "state": "active"},
            {"name": "franka_robot_state_broadcaster", "state": "active"},
            {"name": "joint_impedance_example_controller", "state": "inactive"}
        ]
    }

@router.post("/config/joint_stiffness")
async def set_joint_stiffness(stiffness: list[float], api_key: str = Depends(get_api_key)):
    # Simplification: a full implementation would call set_joint_stiffness service
    return {"success": True, "message": "Joint stiffness updated (mock)"}
