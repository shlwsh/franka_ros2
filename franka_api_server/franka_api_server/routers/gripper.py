from fastapi import APIRouter, Depends
from ..auth import get_api_key
from ..models.gripper import GraspRequest, MoveGripperRequest, GripperResponse
from ..ros_bridge import RosBridge

router = APIRouter(tags=["gripper"])

@router.post("/gripper/grasp", response_model=GripperResponse)
async def grasp(req: GraspRequest, api_key: str = Depends(get_api_key)):
    bridge = RosBridge.get_instance()
    success, msg, cur_width = await bridge.send_grasp(req)
    
    return GripperResponse(
        success=success,
        error=msg if not success else "",
        current_width=cur_width
    )

@router.post("/gripper/move", response_model=GripperResponse)
async def move_gripper(req: MoveGripperRequest, api_key: str = Depends(get_api_key)):
    bridge = RosBridge.get_instance()
    success, msg = await bridge.send_gripper_move(req)
    
    return GripperResponse(
        success=success,
        error=msg if not success else ""
    )

@router.post("/gripper/homing", response_model=GripperResponse)
async def homing_gripper(api_key: str = Depends(get_api_key)):
    bridge = RosBridge.get_instance()
    success, msg = await bridge.send_homing()
    
    return GripperResponse(
        success=success,
        error=msg if not success else ""
    )
