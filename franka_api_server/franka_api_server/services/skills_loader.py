"""Load predefined poses from skills/poses.yaml for Paper I motion skills API."""

from pathlib import Path
from typing import Any, Dict

import yaml
from fastapi import HTTPException

from ..models.motion import MoveJointsRequest

SKILL_ALIASES = {
    'go_to_tongue_pose': 'tongue_pose',
    'go_to_face_pose': 'face_pose',
}

_POSES_PATH = Path(__file__).resolve().parent.parent / 'skills' / 'poses.yaml'
_cache: Dict[str, Any] | None = None


def _load_yaml() -> Dict[str, Any]:
    global _cache
    if _cache is not None:
        return _cache
    if not _POSES_PATH.is_file():
        raise HTTPException(
            status_code=500,
            detail=f'poses.yaml not found at {_POSES_PATH}',
        )
    with _POSES_PATH.open(encoding='utf-8') as f:
        _cache = yaml.safe_load(f)
    return _cache


def resolve_pose_key(skill_name: str) -> str:
    if skill_name in SKILL_ALIASES:
        return SKILL_ALIASES[skill_name]
    if skill_name in _load_yaml().get('poses', {}):
        return skill_name
    raise HTTPException(
        status_code=404,
        detail=f'unknown skill: {skill_name}',
    )


def load_move_request(skill_name: str) -> MoveJointsRequest:
    data = _load_yaml()
    pose_key = resolve_pose_key(skill_name)
    poses = data.get('poses', {})
    if pose_key not in poses:
        raise HTTPException(status_code=404, detail=f'pose not defined: {pose_key}')

    pose = poses[pose_key]
    joints = pose.get('joint_positions')
    if not joints or len(joints) != 7:
        raise HTTPException(
            status_code=500,
            detail=f'pose {pose_key} must have 7 joint_positions',
        )

    return MoveJointsRequest(
        goal_joint_configuration=list(joints),
        goal_tolerance=float(pose.get('goal_tolerance', 0.02)),
        max_velocity_scaling=float(pose.get('max_velocity_scaling', 0.3)),
        async_execution=True,
    )


def list_skills() -> Dict[str, str]:
    """Public API skill_name -> internal pose key."""
    return dict(SKILL_ALIASES)
