from fastapi import APIRouter, Depends
import uuid
from ..auth import get_api_key
from ..models.motion import MoveJointsRequest, MotionTaskResponse
from ..ros_bridge import RosBridge

router = APIRouter(tags=["motion"])

@router.post("/motion/move_joints", response_model=MotionTaskResponse)
async def move_joints(req: MoveJointsRequest, api_key: str = Depends(get_api_key)):
    bridge = RosBridge.get_instance()
    
    # Scale max velocities if not explicitly provided
    if not req.maximum_joint_velocities:
        # Simplified default max velocities for FR3
        default_max_vel = [2.0, 2.0, 2.0, 2.0, 2.5, 2.5, 2.5]
        req.maximum_joint_velocities = [v * req.max_velocity_scaling for v in default_max_vel]
        
    success, msg = await bridge.send_ptp_motion(req)
    task_id = f"motion_{uuid.uuid4().hex[:8]}"
    
    return MotionTaskResponse(
        task_id=task_id,
        status="accepted" if success else "failed",
        message=msg
    )

@router.post("/motion/error_recovery", response_model=MotionTaskResponse)
async def error_recovery(api_key: str = Depends(get_api_key)):
    bridge = RosBridge.get_instance()
    success, msg = await bridge.send_error_recovery()
    
    return MotionTaskResponse(
        task_id=f"recov_{uuid.uuid4().hex[:8]}",
        status="accepted" if success else "failed",
        message=msg
    )
