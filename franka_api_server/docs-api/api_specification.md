# Franka API Server 接口规范文档

本文档定义了 Franka ROS 2 Web API 服务器的接口规范。该 API 提供了对 Franka 机械臂状态获取、运动控制、夹爪控制和控制器管理等核心功能的 HTTP 与 WebSocket 访问能力。

## 基础说明

- **基础路径 (Base URL)**: `/api/v1`
- **数据格式**: 所有接口请求和响应格式均为 `application/json`。
- **认证 (Authentication)**: 
  - 所有受保护的接口都需要提供 API 密钥进行校验。
  - HTTP 请求可以通过 Query 参数 `?api_key=xxx` 或 HTTP Header `X-API-Key: xxx` 提供。
  - 默认 API 密钥：`franka-api-default-key`（可在环境或配置文件中修改）。

---

## 1. 状态获取 (Status API)

### 1.1 获取关节状态
获取机械臂当前的 7 个关节的实时状态数据。

- **URL**: `/api/v1/status/joints`
- **Method**: `GET`
- **响应参数**:
  - `joint_positions` (List[float]): 各关节的角度位置。
  - `joint_velocities` (List[float]): 各关节的运动速度。
  - `joint_efforts` (List[float]): 各关节的受力/力矩。
  - `joint_names` (List[str]): 对应的各关节名称。

### 1.2 获取机器状态
获取机器人总体的运行模式和当前错误状态。

- **URL**: `/api/v1/status/robot`
- **Method**: `GET`
- **响应参数**:
  - `robot_mode` (int): 机器人模式枚举值 (如 `IDLE`, `MOVE`, `ERROR_RECOVERY` 等)。
  - `current_errors` (string/object): 当前报告的硬件/安全错误详情。

---

## 2. 运动控制 (Motion API)

### 2.1 PTP 关节空间运动
向目标关节配置发起点对点 (PTP) 运动，由后端的 MoveIt MoveGroup 执行。

- **URL**: `/api/v1/motion/move_joints`
- **Method**: `POST`
- **请求体 (Request Body)**:
  ```json
  {
    "goal_joint_configuration": [0.0, -0.785, 0.0, -2.356, 0.0, 1.57, 0.785],
    "maximum_joint_velocities": null,
    "max_velocity_scaling": 0.5,
    "goal_tolerance": 0.01,
    "async_execution": true
  }
  ```
  - `goal_joint_configuration` (必需，长度 7): 目标关节的弧度位置数组。
  - `max_velocity_scaling` (可选，默认 0.5): 运动速度缩放比例，范围 0-1。
- **响应**:
  ```json
  {
    "task_id": "motion_abcd1234",
    "status": "accepted",
    "message": "Goal accepted by MoveIt..."
  }
  ```

### 2.2 错误恢复 (Error Recovery)
尝试重置机器人由于发生违规、越限等情况引发的错误状态并重新就绪。

- **URL**: `/api/v1/motion/error_recovery`
- **Method**: `POST`
- **响应**:
  - `task_id` (string): 恢复任务的跟踪 ID。
  - `status` (string): `accepted` 或 `failed`。
  - `message` (string): 状态说明。

---

## 3. 夹爪控制 (Gripper API)

### 3.1 抓取物体 (Grasp)
闭合夹爪，以指定的力去抓取一定宽度的物体。

- **URL**: `/api/v1/gripper/grasp`
- **Method**: `POST`
- **请求体 (Request Body)**:
  ```json
  {
    "width": 0.04,
    "speed": 0.1,
    "force": 50,
    "epsilon_inner": 0.005,
    "epsilon_outer": 0.005
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "error": "",
    "current_width": 0.041
  }
  ```

### 3.2 移动夹爪 (Move)
精确控制夹爪张开/闭合到某个指定宽度。

- **URL**: `/api/v1/gripper/move`
- **Method**: `POST`
- **请求体 (Request Body)**:
  ```json
  {
    "width": 0.08,
    "speed": 0.1
  }
  ```

### 3.3 回零初始化 (Homing)
对夹爪执行硬件初始化校准流程，寻找最大张开和最小闭合的范围边界。

- **URL**: `/api/v1/gripper/homing`
- **Method**: `POST`

---

## 4. 控制器管理 (Controller API)

### 4.1 列出控制器
获取 `controller_manager` 中当前所有挂载的控制器及运行状态。

- **URL**: `/api/v1/controller/list`
- **Method**: `GET`
- **响应**:
  ```json
  {
    "controllers": [
      {
        "name": "joint_state_broadcaster",
        "state": "active"
      }
    ]
  }
  ```

### 4.2 配置关节刚度 (Mock)
调整机器人的底层关节阻抗刚度参数（当前版本为 Mock 接口，需配合专用阻抗控制器使用）。

- **URL**: `/api/v1/config/joint_stiffness`
- **Method**: `POST`
- **请求参数**: List[float] (7个维度的刚度数组)

---

## 5. WebSocket 实时数据接口

通过 WebSocket 协议，前端应用可以低延迟订阅机器人的状态流。
*(建立连接时需在 URL Query 中提供 `?api_key=xxx`)*

### 5.1 机器人状态流
以设定频率（如 10Hz）推送整体状态变化。

- **URL**: `/ws/robot_state`
- **响应格式 (JSON)**:
  ```json
  {
    "type": "robot_state",
    "mode": 1
  }
  ```

### 5.2 关节状态流
以高频（如 30Hz）推送关节位置与速度，通常用于实时在前端驱动 Dashboard 图表或 3D 渲染模型。

- **URL**: `/ws/joint_states`
- **响应格式 (JSON)**:
  ```json
  {
    "type": "joint_states",
    "data": {
      "positions": [0.0, ...],
      "velocities": [0.0, ...]
    }
  }
  ```
