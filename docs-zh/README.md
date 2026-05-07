# Franka Robotics 科研机器人的 ROS 2 集成

[![CI](https://github.com/frankarobotics/franka_ros2/actions/workflows/ci.yml/badge.svg)](https://github.com/frankarobotics/franka_ros2/actions/workflows/ci.yml)

> **注意：** _franka_ros2_ 官方暂不支持 Windows 系统。

## 目录
- [关于](#关于)
- [注意](#注意)
- [安装与配置](#安装与配置)
  - [本机安装](#本机安装)
  - [Docker 容器安装](#docker-容器安装)
- [测试配置](#测试配置)
- [故障排除](#故障排除)
  - [libfranka: UDP receive: Timeout error](#libfranka-udp-receive-timeout-error)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [联系方式](#联系方式)

## 关于
**franka_ros2** 代码库提供了 **libfranka** 的 **ROS 2** 集成，允许在 ROS 2 框架内高效控制 Franka Robotics 机械臂。本项目旨在通过提供稳健的接口来控制科研版本的 Franka Robotics 机器人，从而促进机器人技术的研究与开发。

为了方便起见，我们提供了 `Dockerfile` 和 `docker-compose.yml` 文件。虽然可以直接在本地机器上构建 **franka_ros2**，但这需要手动安装某些依赖，而其他许多依赖会由 **ROS 2** 构建系统自动安装（例如通过 **rosdep**）。这可能会导致系统上安装大量库，潜在引发环境冲突。使用 Docker 可将这些依赖项封装在容器内，最大限度降低风险。此外，Docker 还确保了在不同系统间提供一致且可重现的构建环境。基于这些原因，我们推荐使用 Docker。

## 注意
此包正处于快速开发阶段。用户可能会遇到破坏性更改（Breaking changes），我们鼓励大家通过 [GitHub Issues 页面](https://github.com/frankarobotics/franka_ros2/issues) 报告发现的任何错误。

## 安装与配置

## Franka ROS 2 依赖项设置

此代码库包含一个 `.repos` 文件，可帮助您一次性克隆 Franka ROS 2 所需的各项依赖。

## 前置要求

## 本机安装
1. **安装 ROS 2 开发环境**

    _**franka_ros2**_ 基于 _**ROS 2 Humble**_ 构建。

    如需设置 ROS 2 环境，请遵循官方的 _**Humble**_ [**安装指南**](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html)。
    指南中讨论了两种主要的安装选项：**Desktop（桌面版）** 和 **Bare Bones（基础版）**。

    ### 请选择以下**其中一项**：
    - **ROS 2 "Desktop Install"（桌面版安装）** (`ros-humble-desktop`)
      包含完整的 ROS 2 安装，附带 GUI 工具和可视化包（如 Rviz 和 Gazebo）。
      **推荐** 需要使用仿真或可视化功能的用户选择。

    - **"ROS-Base Install (Bare Bones)"（基础版安装）** (`ros-humble-ros-base`)
      仅包含核心 ROS 2 库的最小化安装。
      适用于资源受限的环境或无头（Headless）系统。

    ```bash
    # 请将 <YOUR CHOICE> 替换为 ros-humble-desktop 或 ros-humble-ros-base
    sudo apt install <YOUR CHOICE>
    ```
    ---
    同时还需要安装 **Development Tools（开发工具）** 包：
    ```bash
    sudo apt install ros-dev-tools
    ```
    安装桌面版或基础版通常会自动加载 **ROS 2** 的环境变量，但在某些情况下，您可能需要再次手动执行此操作：
    ```bash
    source /opt/ros/humble/setup.sh
    ```

2. **创建 ROS 2 工作空间：**
   ```bash
   mkdir -p ~/franka_ros2_ws/src
   cd ~/franka_ros2_ws  # 注意是进入工作空间根目录，而不是 src 目录
   ```
3. **克隆代码库：**
   ```bash
    git clone https://github.com/frankarobotics/franka_ros2.git src
    ```
4. **安装依赖代码：**
    ```bash
    vcs import src < src/dependency.repos --recursive --skip-existing
    ```
5. **检测并安装项目依赖包：**
   ```bash
   rosdep install --from-paths src --ignore-src --rosdistro humble -y
   ```
6. **编译构建：**
   ```bash
   # 使用 --symlinks 选项可以减少磁盘占用，并方便开发时修改代码直接生效。
   colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF
   ```
7. **配置环境变量：**
   ```bash
   # 加载环境以识别新构建的 ROS 2 工作空间中的包和依赖项。
   source install/setup.sh
   ```

## Docker 容器安装
**franka_ros2** 包内含 `Dockerfile` 和 `docker-compose.yml`，使您无需手动安装 **ROS 2** 即可使用 `franka_ros2` 包。此外，还提供了对 Visual Studio Code 中 Dev Containers 的支持。

有关配置 VSCode 以使用 `.devcontainer` 的详细说明，请参考 [VSCode devcontainer 设置指南](https://code.visualstudio.com/docs/devcontainers/tutorial)。

1. **克隆代码库：**
    ```bash
    git clone https://github.com/frankarobotics/franka_ros2.git
    cd franka_ros2
    ```
    我们为在 Visual Studio Code 或命令行中使用 Docker 分别提供了说明。请选择以下选项之一：

    选项 A：从命令行设置并使用 Docker（不使用 Visual Studio Code）。

    选项 B：使用 Visual Studio Code 的 Docker 支持来设置和使用 Docker。

### 选项 A：使用 Docker Compose

  2. **将当前用户 ID 保存到文件：**
      ```bash
      echo -e "USER_UID=$(id -u $USER)\nUSER_GID=$(id -g $USER)" > .env
      ```
      这是为了在 Docker 容器内挂载文件夹时保持权限一致。

  3. **构建容器：**
      ```bash
      docker compose build
      ```
  4. **运行容器：**
      ```bash
      docker compose up -d
      ```
  5. **进入容器的 Shell：**
      ```bash
      docker exec -it franka_ros2 /bin/bash
      ```
  6. **克隆最新的依赖：**
      ```bash
      vcs import src < src/dependency.repos --recursive --skip-existing
      ```
  7. **编译工作空间：**
      ```bash
      colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
      ```
  8. **加载编译后的工作空间环境：**
      ```bash
      source install/setup.bash
      ```
  9. **完成后，您可以退出 Shell 并删除容器**：
      ```bash
      docker compose down -t 0
      ```

### 选项 B：在 Visual Studio Code 中使用 Dev Containers

  2. **打开 Visual Studio Code ...**

        然后，打开 `franka_ros2` 文件夹。

  3. **出现提示时，选择 `Reopen in container`（在容器中重新打开）。**

      容器将根据需要自动构建。

  4. **克隆最新的依赖：**
      ```bash
      vcs import src < src/dependency.repos --recursive --skip-existing
      ```

  5. **打开终端并编译工作空间：**
      ```bash
      colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
      ```
  6. **加载编译后的工作空间环境：**
      ```bash
      source install/setup.bash
      ```


# 测试构建
   ```bash
   colcon test
   ```
> 请记住，franka_ros2 仍在开发中。
> 预期会出现一些警告信息。

## 测试配置

### 运行一个示例 ROS 2 应用程序

要验证您的配置在没有实体机器人的情况下是否正常工作，您可以运行以下命令来使用虚拟（dummy）硬件：

```bash
ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true
```
您可以使用参数 `load_gripper` 来激活或停用末端执行器（夹爪），并使用 `ee_id` 来设置您想要使用的末端执行器型号。默认情况下，将激活 Franka Hand。

如果您想使用命名空间（namespaces）运行此示例，则需要使用 `namespace` 参数，并在 `moveit.rviz` 中的 `Move Group Namespace` 下手动写入您的命名空间。

### 运行 ROS 2 示例控制器

要运行任何示例控制器，请确保在 `franka.config.yaml` 中添加了您所需的配置，然后运行：

```bash
ros2 launch franka_bringup example.launch.py controller_name:=your_desired_controller
```
您可以从 `controllers.yaml` 中选择其中一个控制器。

### 为不同的机器人运行不同的控制器

如果您想为每台机器人运行特定的控制器，则必须按如下方式指定要运行的控制器（以三台机器人为例）：

```bash
ros2 launch franka_bringup example.launch.py controller_names:="cartesian_elbow_example_controller,joint_impedance_example_controller,cartesian_velocity_example_controller"
```
如果指定的控制器数量少于机器人数量，则所有机器人都将使用第一个控制器。也可以使用 TMR（移动协作机器人）的控制器。

### 移动 TMRv0.2

请务必在 `franka_bringup/config/tmr.config.yaml` 中配置您的机器人 IP，并可选择性地更改机器人的命名空间。

您可以通过以下任一方式移动 TMRv0.2：

- 使用远程 XBOX 手柄：

```bash
ros2 launch franka_bringup mobile_teleop.launch.py
```

此 launch 文件会启动用于远程控制所需的附加节点。

- 使用 PC 键盘：

在一个终端中启动：
```bash
ros2 launch franka_bringup example.launch.py controller_names:="swerve_drive_controller" robot_config_file:="tmr.config.yaml"
```
在另一个终端中启动：
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true --remap /cmd_vel:=/swerve_drive_controller/cmd_vel
```

### 运行虚拟硬件 (MoveIt 2 演示)与可视化调试

如果你目前没有连接真实机械臂，可以运行带有虚拟硬件的 MoveIt 演示：
```bash
ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true
```
> **💡 可视化调试提示 (推荐)**：
> 上述 `launch` 命令会自动配置并启动 **RViz2** 界面。在 ROS 2 (如 Jazzy) 中，建议直接使用 RViz 进行可视化控制，而**无需**额外运行 `rqt_joint_trajectory_controller`（可能因 QoS 问题导致卡死等待）：
> 1. 在界面左下角的 `MotionPlanning` 面板中点击 **`Joints`** 标签页。
> 2. 拖动 `fr3_joint1` ~ `fr3_joint7` 的各个滑块来调节期望位姿（上方 3D 视图中会有橙色预览）。
> 3. 点击面板下方的 **`Plan & Execute`**，即可下发运动轨迹并控制机械臂执行动作。

### 在 ROS 2 中运行 Gazebo 示例

如果您想使用 Gazebo 运行您的代码，可以在这里找到一些示例：[franka_gazebo](./franka_gazebo/README.md)

## 故障排除
### `libfranka: UDP receive: Timeout error`

如果在与机器人通信时遇到 UDP 接收超时错误，请避免使用 Docker Desktop。它可能无法提供与机器人可靠通信所需的实时能力。相反，使用 Docker Engine 就足以满足此目的。

实时内核对于确保正确通信和防止超时问题至关重要。有关设置实时内核的指导，请参考 [Franka 安装文档](https://frankarobotics.github.io/docs/installation_linux.html#setting-up-the-real-time-kernel)。

## 贡献指南

欢迎贡献！请参阅 [CONTRIBUTING.md](https://github.com/frankarobotics/franka_ros2/blob/humble/CONTRIBUTING.md) 以获取有关如何为本项目做出贡献的更多详细信息。

## 许可证

franka_ros2 的所有包均采用 Apache 2.0 许可证。

## 联系方式

如有疑问或需要支持，请在 [GitHub Issues](https://github.com/frankarobotics/franka_ros2/issues) 页面上提交 issue。

有关更多信息，请参阅 [Franka 控制接口 (FCI) 文档](https://frankarobotics.github.io/docs)。

[def]: #docker-container-installation
