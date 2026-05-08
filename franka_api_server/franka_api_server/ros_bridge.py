import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from sensor_msgs.msg import JointState
from franka_msgs.msg import FrankaRobotState
from franka_msgs.action import PTPMotion, Grasp, Move, Homing, ErrorRecovery
import threading
from .config import settings
import asyncio

class RosBridge(Node):
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            rclpy.init()
            cls._instance = RosBridge()
            cls._instance._start_spin_thread()
        return cls._instance

    def __init__(self):
        super().__init__('franka_api_bridge')
        self.cb_group = ReentrantCallbackGroup()
        
        # State variables
        self.joint_state = None
        self.robot_state = None
        
        # Subscribers
        self.joint_sub = self.create_subscription(
            JointState, 
            settings.joint_states_topic, 
            self._joint_state_callback, 
            10,
            callback_group=self.cb_group
        )
        self.robot_state_sub = self.create_subscription(
            FrankaRobotState, 
            settings.robot_state_topic, 
            self._robot_state_callback, 
            10,
            callback_group=self.cb_group
        )
        
        # Action Clients
        self.ptp_client = ActionClient(self, PTPMotion, '/ptp_motion', callback_group=self.cb_group)
        self.grasp_client = ActionClient(self, Grasp, '/franka_gripper/grasp', callback_group=self.cb_group)
        self.move_client = ActionClient(self, Move, '/franka_gripper/move', callback_group=self.cb_group)
        self.homing_client = ActionClient(self, Homing, '/franka_gripper/homing', callback_group=self.cb_group)
        self.error_recovery_client = ActionClient(self, ErrorRecovery, '/error_recovery', callback_group=self.cb_group)
        
    def _start_spin_thread(self):
        self.spin_thread = threading.Thread(target=self._spin, daemon=True)
        self.spin_thread.start()
        
    def _spin(self):
        try:
            rclpy.spin(self)
        except Exception as e:
            self.get_logger().error(f"ROS Spin stopped: {e}")
            
    def _joint_state_callback(self, msg):
        self.joint_state = msg
        
    def _robot_state_callback(self, msg):
        self.robot_state = msg

    # --- Actions API ---
    async def send_ptp_motion(self, req_data):
        if not self.ptp_client.wait_for_server(timeout_sec=2.0):
            return False, "PTP Action Server not available"
            
        goal_msg = PTPMotion.Goal()
        goal_msg.goal_joint_configuration = req_data.goal_joint_configuration
        if req_data.maximum_joint_velocities:
            goal_msg.maximum_joint_velocities = req_data.maximum_joint_velocities
        goal_msg.goal_tolerance = req_data.goal_tolerance
        
        future = self.ptp_client.send_goal_async(goal_msg)
        # We just return success that the goal was sent for async execution
        # A full implementation would track the task ID
        return True, "Goal sent"

    async def send_grasp(self, req_data):
        if not self.grasp_client.wait_for_server(timeout_sec=2.0):
            return False, "Grasp Action Server not available", 0.0
            
        goal_msg = Grasp.Goal()
        goal_msg.width = req_data.width
        goal_msg.speed = req_data.speed
        goal_msg.force = req_data.force
        goal_msg.epsilon.inner = req_data.epsilon_inner
        goal_msg.epsilon.outer = req_data.epsilon_outer
        
        future = self.grasp_client.send_goal_async(goal_msg)
        # For simplification, we just fire and forget here or wait using a loop
        # In a real async bridge, we should use a concurrent.futures.Future adapter
        return True, "Grasp command sent", 0.0

    async def send_gripper_move(self, req_data):
        if not self.move_client.wait_for_server(timeout_sec=2.0):
            return False, "Move Action Server not available"
        goal_msg = Move.Goal()
        goal_msg.width = req_data.width
        goal_msg.speed = req_data.speed
        self.move_client.send_goal_async(goal_msg)
        return True, "Move command sent"

    async def send_homing(self):
        if not self.homing_client.wait_for_server(timeout_sec=2.0):
            return False, "Homing Action Server not available"
        goal_msg = Homing.Goal()
        self.homing_client.send_goal_async(goal_msg)
        return True, "Homing command sent"
        
    async def send_error_recovery(self):
        if not self.error_recovery_client.wait_for_server(timeout_sec=2.0):
            return False, "Error Recovery Action Server not available"
        goal_msg = ErrorRecovery.Goal()
        self.error_recovery_client.send_goal_async(goal_msg)
        return True, "Error recovery command sent"
