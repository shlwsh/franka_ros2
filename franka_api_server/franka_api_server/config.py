import os

class Settings:
    def __init__(self):
        self.host = os.getenv("FRANKA_API_HOST", "0.0.0.0")
        self.port = int(os.getenv("FRANKA_API_PORT", "8080"))
        self.auth_enabled = os.getenv("FRANKA_API_AUTH_ENABLED", "true").lower() == "true"
        self.api_key = os.getenv("FRANKA_API_KEY", "franka-api-default-key")
        self.ws_publish_rate = float(os.getenv("FRANKA_API_WS_PUBLISH_RATE", "30.0"))
        self.joint_states_topic = os.getenv("FRANKA_API_JOINT_STATES_TOPIC", "/joint_states")
        self.robot_state_topic = os.getenv("FRANKA_API_ROBOT_STATE_TOPIC", "/franka_robot_state_broadcaster/robot_state")
        self.max_velocity_scaling = float(os.getenv("FRANKA_API_MAX_VELOCITY_SCALING", "0.5"))

settings = Settings()
