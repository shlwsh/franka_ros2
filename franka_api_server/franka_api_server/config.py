import os
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ('1', 'true', 'yes', 'on')


def _default_paper1_root() -> str:
    # franka_ros2 workspace root: .../franka_api_server/franka_api_server/config.py -> parents[2]
    workspace = Path(__file__).resolve().parents[2]
    return str(workspace / 'doctor' / 'paper1')


class Settings:
    def __init__(self):
        self.host = os.getenv('FRANKA_API_HOST', '0.0.0.0')
        self.port = int(os.getenv('FRANKA_API_PORT', '8000'))
        self.auth_enabled = _env_bool('FRANKA_API_AUTH_ENABLED', True)
        self.api_key = os.getenv('FRANKA_API_KEY', 'franka-api-default-key')
        self.ws_publish_rate = float(os.getenv('FRANKA_API_WS_PUBLISH_RATE', '30.0'))
        self.joint_states_topic = os.getenv(
            'FRANKA_API_JOINT_STATES_TOPIC', '/joint_states'
        )
        self.robot_state_topic = os.getenv(
            'FRANKA_API_ROBOT_STATE_TOPIC',
            '/franka_robot_state_broadcaster/robot_state',
        )
        self.max_velocity_scaling = float(
            os.getenv('FRANKA_API_MAX_VELOCITY_SCALING', '0.5')
        )

        # Paper I (V19) — algorithm tree lives in this repo under doctor/paper1/
        self.paper1_mode = _env_bool('PAPER1_MODE', False)
        self.paper1_root = os.getenv('PAPER1_ROOT', _default_paper1_root())
        self.paper1_upload_dir = os.getenv(
            'PAPER1_UPLOAD_DIR',
            str(Path(__file__).resolve().parents[2] / '.cache' / 'paper1_uploads'),
        )
        self.iqa_subprocess = _env_bool('PAPER1_IQA_SUBPROCESS', True)
        self.iqa_timeout_s = float(os.getenv('PAPER1_IQA_TIMEOUT_S', '5.0'))
        self.vision_placeholder_q = float(os.getenv('PAPER1_VISION_PLACEHOLDER_Q', '0.5'))
        self.vision_threshold_tau = float(os.getenv('PAPER1_VISION_THRESHOLD_TAU', '0.55'))


settings = Settings()
