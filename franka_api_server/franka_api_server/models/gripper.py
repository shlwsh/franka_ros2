from pydantic import BaseModel, Field

class GraspRequest(BaseModel):
    width: float = Field(..., description="Target grasp width [m]")
    speed: float = Field(..., description="Grasp speed [m/s]")
    force: float = Field(..., description="Grasp force [N]")
    epsilon_inner: float = Field(0.005, description="Inner epsilon [m]")
    epsilon_outer: float = Field(0.005, description="Outer epsilon [m]")

class MoveGripperRequest(BaseModel):
    width: float = Field(..., description="Target width [m]")
    speed: float = Field(..., description="Move speed [m/s]")

class GripperResponse(BaseModel):
    success: bool
    error: str = ""
    current_width: float = 0.0
