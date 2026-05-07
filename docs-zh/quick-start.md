# Franka ROS 2 快速启动与测试指南（ROS 2 Jazzy）

本文档总结了在 Ubuntu 24.04 + ROS 2 Jazzy 环境中，启动 Franka FR3 机械臂可视化、配置 MoveIt 运动规划，以及在 RViz 中进行轨迹设计的完整流程。

> **重要声明：** franka_ros2 官方仅支持 ROS 2 Humble。本文档描述的是在 Jazzy 上的适配方案，运行前请参考 [安装指南](./install-guide-jazzy.md) 完成环境搭建。

---

## 1. 环境变量加载（每次必做）

**每次新开终端时**，必须先加载 ROS 2 和工作空间的环境变量，否则会报 `Package not found` 错误：

```bash
source /opt/ros/jazzy/setup.bash
source ~/robotic_ws/install/setup.bash
```

> **💡 推荐：** 将上述两行追加到 `~/.bashrc` 中，实现终端自动加载：
> ```bash
> echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
> echo 'source ~/robotic_ws/install/setup.bash' >> ~/.bashrc
> ```

---

## 2. 基础依赖编译

在首次启动或修改了配置文件后，需要重新编译相关包：

```bash
cd ~/robotic_ws

# 编译核心包（含 Jazzy 兼容层）
colcon build --packages-select franka_jazzy_compat franka_fr3_moveit_config franka_gripper

# 编译完成后务必重新加载
source install/setup.bash
```

---

## 3. 机械臂静态可视化（仅 RViz）

如果只需查看机械臂 3D 模型、调整各关节角度，无需启动 MoveIt 或控制器：

```bash
ros2 launch franka_description visualize_franka.launch.py robot_type:=fr3
```

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `robot_type` | — | 机型选择：`fer`, `fr3`, `fp3`, `fr3v2`, `fr3v2_1`, `tmrv0_2` |
| `load_gripper` | `true` | 是否加载 Franka Hand 末端夹爪 |
| `ee_id` | `franka_hand` | 末端执行器类型：`none`, `franka_hand`, `cobot_pump` |

---

## 4. MoveIt 假硬件启动（推荐测试方式）

当没有真实物理机械臂时，通过假硬件接口启动完整的 MoveIt 运动规划环境。

### 4.1 一键测试脚本（最推荐）

我们在 `scripts` 目录下提供了一个自动化的启动脚本，它会**自动清理卡死的进程**、**自动加载所有必需的环境变量**，并启动假硬件测试：

```bash
cd ~/robotic_ws/src/franka_ros2
./scripts/start.sh
```

### 4.2 手动启动方式

如果您希望手动启动，请执行以下命令：

```bash
ros2 launch franka_fr3_moveit_config moveit.launch.py \
  robot_ip:=dont-care \
  use_fake_hardware:=true
```

成功启动后，系统将同时开启以下核心节点：

| 节点 | 说明 |
|------|------|
| `ros2_control_node` | 假硬件控制器管理器，模拟底层状态反馈和控制命令 |
| `move_group` | MoveIt 运动规划引擎，提供逆运动学求解和路径规划 |
| `rviz2` | 可视化界面，内置 MotionPlanning 插件 |
| `joint_state_publisher` | 关节状态发布器 |
| `robot_state_publisher` | TF 坐标变换发布器 |

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `robot_ip` | — | 机器人 IP（假硬件模式下填 `dont-care`） |
| `use_fake_hardware` | `false` | 是否使用假硬件接口 |
| `load_gripper` | `true` | 是否加载末端夹爪 |
| `ee_id` | `franka_hand` | 末端执行器类型 |
| `namespace` | `''` | 命名空间（多机协作时使用） |

---

## 5. 在 RViz 中使用 MoveIt 设计轨迹

启动假硬件模式后，RViz 中会自动加载 MoveIt MotionPlanning 插件。以下是完整的轨迹规划操作流程：

### 5.1 拖拽交互式标记（Interactive Markers）

在 RViz 3D 视图中，机械臂末端会显示一组交互式控件（箭头 + 圆环）：
- **拖动箭头** → 改变末端目标位置（沿 X/Y/Z 轴平移）
- **拖动圆环** → 改变末端目标姿态（绕轴旋转）
- 拖动后会出现一个 **橙色半透明残影**，代表您设定的 **目标位姿（Goal State）**

### 5.2 规划轨迹

1. 在 RViz 左侧面板中找到 **MotionPlanning → Planning** 选项卡
2. 确认 **Planning Group** 选择的是 `fr3_arm`
3. 确认 **Start State** 为 `<current>`（从当前位置出发）
4. 确认 **Goal State** 为交互标记拖拽到的位置
5. 点击 **Plan** 按钮
6. 规划成功后，3D 视图中会 **自动播放轨迹动画**

### 5.3 执行轨迹

- 若轨迹符合预期，点击 **Execute** 按钮，机械臂将沿轨迹移动到目标位置
- 也可以直接点击 **Plan & Execute** 一键规划并执行

### 5.4 进阶选项

| 功能 | 位置 | 说明 |
|------|------|------|
| 速度缩放 | Planning 选项卡 → Velocity Scaling | 调整轨迹执行速度（0.0 ~ 1.0） |
| 加速度缩放 | Planning 选项卡 → Acceleration Scaling | 调整轨迹加速度（0.0 ~ 1.0） |
| 添加障碍物 | Scene Objects 选项卡 | 可添加虚拟立方体/圆柱体，MoveIt 会自动避障 |
| 预设姿态 | Planning 选项卡 → Goal State 下拉框 | 可选择预定义的命名姿态 |

---

## 6. Jazzy 适配：关键修改记录

在 ROS 2 Jazzy 环境下，原版 Humble 配置无法直接使用。以下是本次适配过程中对项目做出的关键修改：

### 6.1 运动学求解器（kinematics.yaml）

**文件**：`franka_fr3_moveit_config/config/kinematics.yaml`

原版使用的 LMA 求解器在 Jazzy 中不可用，需替换为 KDL：

```diff
 fr3_arm:
-  kinematics_solver: lma_kinematics_plugin/LMAKinematicsPlugin
+  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
   kinematics_solver_search_resolution: 0.005
   kinematics_solver_timeout: 0.005
```

**原因**：Jazzy 的 `ros-jazzy-moveit-kinematics` 仅自带 KDL 和 CachedKDL 求解器，不包含 LMA 插件。

### 6.2 规划管道参数格式（moveit.launch.py）

**文件**：`franka_fr3_moveit_config/launch/moveit.launch.py`

Jazzy MoveIt 2 (v2.12) 对规划管道的参数结构做了不兼容变更：

```diff
-# 旧 Humble 格式（单字符串）
-ompl_planning_pipeline_config = {
-    'move_group': {
-        'planning_plugin': 'ompl_interface/OMPLPlanner',
-        'request_adapters': 'adapter1 adapter2 adapter3...',
-    }
-}
+# 新 Jazzy 格式（列表式 + 管道注册）
+ompl_planning_pipeline_config = {
+    'planning_pipelines': ['ompl'],
+    'default_planning_pipeline': 'ompl',
+    'ompl': {
+        'planning_plugins': ['ompl_interface/OMPLPlanner'],
+        'request_adapters': [
+            'default_planning_request_adapters/ResolveConstraintFrames',
+            'default_planning_request_adapters/ValidateWorkspaceBounds',
+            'default_planning_request_adapters/CheckStartStateBounds',
+            'default_planning_request_adapters/CheckStartStateCollision',
+        ],
+        'response_adapters': [
+            'default_planning_response_adapters/AddTimeOptimalParameterization',
+            'default_planning_response_adapters/ValidateSolution',
+            'default_planning_response_adapters/DisplayMotionPath',
+        ],
+    },
+}
```

同时，运动学参数的传递方式也需要修改：

```diff
-kinematics_yaml = load_yaml(...)
+kinematics_yaml = load_yaml(...)
+robot_description_kinematics = {'robot_description_kinematics': kinematics_yaml}
```

### 6.3 OMPL 规划组名修正（ompl_planning.yaml）

**文件**：`franka_fr3_moveit_config/config/ompl_planning.yaml`

原配置文件沿用了 Panda 的规划组名，需修正为 FR3：

```diff
-panda_arm:
+fr3_arm:
   planner_configs:
     - RRTConnectkConfigDefault
     ...
-panda_arm_hand:
+fr3_arm_hand:
   planner_configs:
     ...
```

---

## 7. 常见问题排查

### 7.1 `Package 'franka_fr3_moveit_config' not found`

**原因**：未加载工作空间环境变量。  
**解决**：
```bash
source /opt/ros/jazzy/setup.bash
source ~/robotic_ws/install/setup.bash
```

### 7.2 `move_group` 启动即崩溃（exit code -6）

**原因**：规划管道参数格式不兼容 Jazzy。  
**解决**：按照第 6.2 节修改 `moveit.launch.py`，然后重新编译：
```bash
colcon build --packages-select franka_fr3_moveit_config
source install/setup.bash
```

### 7.3 `Failed loading controller joint_state_broadcaster`

**原因**：上一次启动未完全退出，残留的 `ros2_control_node` 僵尸进程占用了端口。  
**解决**：先杀死所有残留进程再重新启动：
```bash
killall -9 ros2_control_node move_group rviz2 joint_state_publisher robot_state_publisher
# 等待 1-2 秒后再重新启动
ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true
```

### 7.4 `No kinematics plugins defined` / `LMAKinematicsPlugin failed to load`

**原因**：Jazzy 不包含 LMA 运动学插件。  
**解决**：按照第 6.1 节修改 `kinematics.yaml`，将 `lma_kinematics_plugin` 替换为 `kdl_kinematics_plugin`。

### 7.5 RViz 窗口无法最大化（WSL2 环境）

**原因**：WSL2 使用 WSLg（Weston 合成器），其窗口管理功能有限。  
**解决**：
- 手动拖拽窗口边缘调整大小
- 或安装独立 X Server（如 VcXsrv），使用 Windows 原生窗口管理器

### 7.6 `Overrun detected! controller manager missed its desired rate of 1000 Hz`

**原因**：非实时内核下，1000Hz 的控制循环偶尔有微秒级超时。  
**影响**：仅为警告，**不影响功能使用**。仿真和规划测试不受影响。如需消除，需配置 Linux 实时内核（Real-time kernel）。

---

## 8. 连接真实机械臂

如果部署了真实的 Franka 机器人，请确保：

1. **网络连接**：通过网线直连计算机与机器人控制器
2. **实时内核**：宿主机配置 Linux 实时内核，避免 UDP 通信超时
3. **IP 配置**：在启动参数中填写正确的机械臂 IP 地址

启动示例控制器（以关节阻抗控制为例）：

```bash
ros2 launch franka_bringup example.launch.py controller_name:=joint_impedance_example_controller
```

有关多机协作和移动机器人（TMR）控制，请参考 [README 主文档](./README.md)。
