from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class VisionEvaluateRequest(BaseModel):
    image_path: Optional[str] = Field(
        None,
        description='Absolute path under PAPER1_ROOT or upload cache (debug only)',
    )


class VisionEvaluateResponse(BaseModel):
    q_img: float
    flags: List[str] = Field(default_factory=list)
    t_iqa_ms: float
    threshold_tau: float = 0.55
    meta: Dict[str, str] = Field(default_factory=dict)
