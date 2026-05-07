# Franka ROS 2 机械臂启动与加载流程详解 (study001)

本文档旨在为初学者详细梳理当前 `scripts/start.sh` 脚本启动机械臂的整个过程，包括正在使用的机械臂型号、控制器类型，以及涉及的核心代码和配置文件。

## 一、 当前启动的机械臂与控制器

1. **机械臂型号**：**Franka FR3**
   - 依据：脚本中调用了 `ros2 launch franka_fr3_moveit_config ...`，加载的是针对 FR3 型号配置的 MoveIt 环境。

2. **控制器 (Controller)**：**JointTrajectoryController (关节轨迹控制器)**
   - **名称**：`fr3_arm_controller`
   - **类型**：`joint_trajectory_controller/JointTrajectoryController`
   - **作用**：接收 MoveIt 规划好的关节轨迹（包含每个时间点的关节位置、速度等），然后输出控制指令（当前配置为力矩/effort 指令）驱动机械臂运动。

## 二、 启动流程与核心文件解析

当我们运行 `scripts/start.sh` 时，系统到底做了什么？下面是按顺序的拆解：

### 1. 环境准备阶段
**涉及文件**：`scripts/start.sh` (位于项目根目录的 `scripts` 目录下)

- **清理环境**：脚本首先使用 `killall -9` 强行关闭可能残留的 ROS 2 进程（如 `ros2_control_node`, `move_group`, `rviz2` 等），防止端口冲突或状态异常。
- **加载环境变量**：执行 `source /opt/ros/jazzy/setup.bash` 和 `source install/setup.bash`。这使得系统能够识别 ROS 2 的基础命令以及我们自己编译的 `franka_ros2` 工作空间中的功能包。

### 2. 核心启动阶段
**涉及命令**：
```bash
ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true
```
这行命令是整个系统的核心。它告诉 ROS 2 启动 `franka_fr3_moveit_config` 包下的 `moveit.launch.py` 文件，并传递了两个重要参数：
- `robot_ip:=dont-care`：因为我们现在不连接真机，所以 IP 地址无关紧要。
- `use_fake_hardware:=true`：**非常关键**，它告诉系统不要去寻找真实的物理机械臂硬件，而是启动一个“假硬件”（Mock Hardware）在内存中模拟机械臂的状态，方便我们进行软件层面的测试。

### 3. Launch 文件解析 (各组件加载过程)
**涉及文件**：`franka_fr3_moveit_config/launch/moveit.launch.py` (位于项目根目录的 `franka_fr3_moveit_config` 目录下)

这个 Python 脚本编排了整个复杂的 ROS 2 系统，主要加载了以下几个核心组件：

#### (1) 加载机械臂模型 (URDF/XACRO)
- **底层文件**：`src/franka_description/robots/fr3/fr3.urdf.xacro` (该模型文件位于 `src/franka_description` 源码包下)
- **作用**：ROS 2 和 MoveIt 需要知道机械臂长什么样（连杆长度、关节旋转轴、碰撞体积等）。Launch 文件会使用 `xacro` 工具解析这个模型文件。由于传入了 `use_fake_hardware:=true`，模型在加载 `ros2_control` 硬件接口时，会自动切换为 `mock_components/GenericSystem` 虚拟硬件。

#### (2) 启动 `robot_state_publisher` (机器人状态发布器)
- **作用**：根据上面读取的机器人模型，以及当前各个关节的角度，实时计算并发布机械臂各个部件在三维空间中的精确位置关系（TF 坐标变换）。RViz 就是依靠这个才能把机械臂正确画出来的。

#### (3) 启动 `ros2_control_node` (控制器管理器)
- **配置文件**：`franka_fr3_moveit_config/config/fr3_ros_controllers.yaml` (位于 `franka_fr3_moveit_config/config` 目录下)
- **作用**：这是连接“软件（控制器）”和“硬件（不论真假）”的桥梁。
- **加载控制器**：随后，Launch 文件会使用 `spawner` 动态加载两个控制器：
  1. `joint_state_broadcaster`：负责把硬件层读取到的关节角度打包成标准消息发布出去。
  2. `fr3_arm_controller`：也就是前面提到的轨迹控制器，负责接收规划轨迹并下发执行指令。在 YAML 配置中，可以看到它使用 `effort` (力矩) 作为命令接口，使用 `position` 和 `velocity` 作为状态接口。

#### (4) 启动 `move_group` 节点 (MoveIt 运动规划核心)
- **配置文件** (均位于 `franka_fr3_moveit_config/config` 目录下)：
  - `kinematics.yaml`（运动学求解器配置）
  - `ompl_planning.yaml`（OMPL 规划算法配置）
  - `fr3_controllers.yaml`（MoveIt 与底层的接口配置）
- **作用**：MoveIt 系统的“大脑”。它负责接收 RViz 中拖拽的目标位置，考虑避障、关节限制等因素，使用 OMPL 算法规划出一条平滑的运动轨迹，然后把轨迹发送给底层的 `fr3_arm_controller` 执行。

#### (5) 启动 `rviz2` (可视化界面)
- **配置文件**：`franka_fr3_moveit_config/rviz/moveit.rviz` (位于 `franka_fr3_moveit_config/rviz` 目录下)
- **作用**：启动我们看到的 3D 可视化界面。并加载了 MoveIt 的 MotionPlanning 插件，允许我们用鼠标拖拽机械臂末端，点击 "Plan and Execute" 与后台的 `move_group` 交互。

## 三、 总结：数据流转过程

如果你在 RViz 中拖动了机械臂并点击了“执行”，背后的数据流转是这样的：

1. **用户输入**：RViz2 界面接收拖拽目标，发送给 `move_group`。
2. **轨迹规划**：`move_group` 结合机器人模型（URDF）计算避障轨迹。
3. **指令下发**：`move_group` 将轨迹点发送给 `ros2_control` 管理器下的 `fr3_arm_controller`。
4. **控制执行**：`fr3_arm_controller` 将轨迹点转化为 `effort` (力矩) 控制指令。
5. **硬件模拟**：因为启用了 `use_fake_hardware`，指令被发送到了虚拟硬件中，虚拟硬件直接更新了自身的关节状态，模拟运动完成。
6. **状态反馈**：虚拟硬件将新的关节角度传回，`joint_state_broadcaster` 将其广播出去。
7. **界面更新**：`robot_state_publisher` 收到新角度，更新 TF 坐标，最终 RViz 刷新画面，显示机械臂运动到了新位置。
