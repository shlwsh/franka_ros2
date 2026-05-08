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
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest, Constraints, JointConstraint,
    RobotState as MoveItRobotState
)

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
        self.traj_client = ActionClient(self, FollowJointTrajectory, '/fr3_arm_controller/follow_joint_trajectory', callback_group=self.cb_group)
        # MoveIt MoveGroup action client - 通过 MoveIt 规划并执行运动
        self.moveit_client = ActionClient(self, MoveGroup, '/move_action', callback_group=self.cb_group)
        
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
        loop = asyncio.get_event_loop()

        # 优先使用 MoveIt MoveGroup action（在 fake hardware 模式下正确工作）
        moveit_available = await loop.run_in_executor(
            None, lambda: self.moveit_client.wait_for_server(timeout_sec=2.0)
        )
        if moveit_available:
            self.get_logger().info('Using MoveIt MoveGroup for motion planning and execution')

            # 获取关节名称
            joint_names = []
            if self.joint_state and len(self.joint_state.name) >= 7:
                joint_names = [
                    name for name in self.joint_state.name
                    if 'finger' not in name
                ][:7]
            if not joint_names or len(joint_names) != 7:
                joint_names = [f'fr3_joint{i}' for i in range(1, 8)]

            # 构建 MoveGroup Goal
            goal_msg = MoveGroup.Goal()
            goal_msg.planning_options.plan_only = False  # 规划并执行
            goal_msg.planning_options.replan = True
            goal_msg.planning_options.replan_attempts = 3

            # 构建运动规划请求
            motion_request = MotionPlanRequest()
            motion_request.group_name = 'fr3_arm'
            motion_request.num_planning_attempts = 5
            motion_request.allowed_planning_time = 5.0
            motion_request.max_velocity_scaling_factor = req_data.max_velocity_scaling
            motion_request.max_acceleration_scaling_factor = req_data.max_velocity_scaling

            # 设置关节目标约束
            goal_constraints = Constraints()
            for i, (name, target_pos) in enumerate(
                zip(joint_names, req_data.goal_joint_configuration)
            ):
                jc = JointConstraint()
                jc.joint_name = name
                jc.position = target_pos
                jc.tolerance_above = req_data.goal_tolerance
                jc.tolerance_below = req_data.goal_tolerance
                jc.weight = 1.0
                goal_constraints.joint_constraints.append(jc)

            motion_request.goal_constraints.append(goal_constraints)
            goal_msg.request = motion_request

            # 发送 goal 并等待结果
            goal_handle_future = self.moveit_client.send_goal_async(goal_msg)
            goal_handle = await asyncio.wrap_future(
                asyncio.ensure_future(self._await_rclpy_future(goal_handle_future, loop))
            )

            if not goal_handle.accepted:
                self.get_logger().error('MoveIt goal was rejected')
                return False, 'MoveIt goal was rejected'

            self.get_logger().info(
                f'MoveIt goal accepted, executing motion to: '
                f'{req_data.goal_joint_configuration}'
            )

            # 异步等待执行结果
            result_future = goal_handle.get_result_async()
            asyncio.ensure_future(self._monitor_moveit_result(result_future, loop))

            return True, 'Goal accepted by MoveIt, executing motion'

        # 回退：直接使用 FollowJointTrajectory（仅在真实硬件上有效）
        traj_available = await loop.run_in_executor(
            None, lambda: self.traj_client.wait_for_server(timeout_sec=1.0)
        )
        if traj_available:
            self.get_logger().info('Using FollowJointTrajectory controller (fallback)')
            goal_msg = FollowJointTrajectory.Goal()

            joint_names = []
            if self.joint_state and len(self.joint_state.name) >= 7:
                joint_names = [
                    name for name in self.joint_state.name
                    if 'finger' not in name
                ][:7]
            if not joint_names or len(joint_names) != 7:
                joint_names = [f'fr3_joint{i}' for i in range(1, 8)]

            goal_msg.trajectory.joint_names = joint_names

            point = JointTrajectoryPoint()
            point.positions = list(req_data.goal_joint_configuration)
            point.time_from_start = Duration(sec=3, nanosec=0)
            goal_msg.trajectory.points.append(point)

            future = self.traj_client.send_goal_async(goal_msg)
            self.get_logger().info(
                f'Trajectory goal sent: {req_data.goal_joint_configuration}'
            )
            return True, 'Goal sent via FollowJointTrajectory'

        # 回退：PTP Motion (真实硬件)
        ptp_available = await loop.run_in_executor(
            None, lambda: self.ptp_client.wait_for_server(timeout_sec=0.5)
        )
        if ptp_available:
            self.get_logger().info('Using PTP Motion action server')
            goal_msg = PTPMotion.Goal()
            goal_msg.goal_joint_configuration = req_data.goal_joint_configuration
            if req_data.maximum_joint_velocities:
                goal_msg.maximum_joint_velocities = req_data.maximum_joint_velocities
            goal_msg.goal_tolerance = req_data.goal_tolerance

            self.ptp_client.send_goal_async(goal_msg)
            return True, 'Goal sent via PTP Motion'

        return False, 'No Action Server (MoveIt, Trajectory or PTP) available'

    async def _await_rclpy_future(self, rclpy_future, loop):
        """将 rclpy Future 转换为 asyncio 可等待的对象"""
        result = asyncio.Future()
        def callback(future):
            loop.call_soon_threadsafe(result.set_result, future.result())
        rclpy_future.add_done_callback(callback)
        return await result

    async def _monitor_moveit_result(self, result_future, loop):
        """后台监控 MoveIt 执行结果"""
        try:
            result = await self._await_rclpy_future(result_future, loop)
            status = result.status
            if status == 4:  # SUCCEEDED
                self.get_logger().info('MoveIt motion execution completed successfully')
            elif status == 5:  # CANCELED
                self.get_logger().warn('MoveIt motion was canceled')
            else:
                error_code = result.result.error_code.val if result.result else 'unknown'
                self.get_logger().error(
                    f'MoveIt motion failed with status {status}, error_code: {error_code}'
                )
        except Exception as e:
            self.get_logger().error(f'Error monitoring MoveIt result: {e}')

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

