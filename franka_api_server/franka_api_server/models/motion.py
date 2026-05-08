from pydantic import BaseModel, Field
from typing import List, Optional

class MoveJointsRequest(BaseModel):
    goal_joint_configuration: List[float] = Field(..., description="Target joint angles in radians, array of 7 elements")
    maximum_joint_velocities: Optional[List[float]] = Field(None, description="Max joint velocities, array of 7 elements")
    goal_tolerance: float = Field(0.01, description="Acceptable goal tolerance in radians")
    max_velocity_scaling: float = Field(0.5, description="Velocity scaling factor (0.0 to 1.0)")
    async_execution: bool = Field(True, description="Whether to execute asynchronously and return immediately")

class MotionTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
