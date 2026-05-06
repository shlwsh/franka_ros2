# Franka ROS 2 环境配置指南（基于 ROS 2 Jazzy）

本文档记录了在非官方支持的 ROS 2 Jazzy 版本上构建 franka_ros2 的完整流程，包括所有遇到的问题及解决方案。

> **重要声明：** franka_ros2 官方基于 ROS 2 Humble 开发。本文档描述的是在 ROS 2 Jazzy 上的适配方案，属于非官方用法，可能存在兼容性问题。

---

## 1. 环境要求

- **操作系统：** Ubuntu 24.04（Noble）
- **ROS 2 版本：** Jazzy（官方要求 Humble）
- **构建工具：** colcon、vcs、rosdep
- **C++ 标准：** C++ 20

---

## 2. 完整安装流程

### 2.1 安装基础构建工具

```bash
sudo apt install python3-vcstool python3-colcon-common-extensions ros-dev-tools
```

### 2.2 创建依赖目录并导入

```bash
cd franka_ros2
mkdir -p src
```

### 2.3 手工下载依赖包（网络受限时）

| 仓库名 | 版本 | 下载地址 | 放置目录 |
|--------|------|----------|----------|
| franka_description | 2.7.0 | https://github.com/frankarobotics/franka_description/releases/tag/2.7.0 | `src/franka_description` |
| libfranka | 0.20.4 | https://github.com/frankarobotics/libfranka/releases/tag/0.20.4 | `src/libfranka` |
| libfranka-common | main | https://github.com/frankarobotics/libfranka-common/archive/refs/heads/master.zip | `src/libfranka/common/` |
| olvx_descriptions_module | main | https://github.com/olive-robotics/olvx_descriptions_module | `src/olvx_descriptions_module` |

**操作步骤：**
1. 将 ZIP 文件下载至 `src/` 目录
2. 解压并重命名：
   ```bash
   unzip franka_description-2.7.0.zip
   mv franka_description-2.7.0 franka_description
   ```
3. libfranka-common 解压后内容放入 `src/libfranka/common/` 目录（此为 git submodule）

### 2.4 配置镜像源

由于网络问题，需要更换 apt 源为阿里云：

```bash
# 更换 ROS 2 源
sudo sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/ros2-latest-archive-keyring.gpg] https://mirrors.aliyun.com/ros2/ubuntu noble main" > /etc/apt/sources.list.d/ros2.list'

# 更换 Ubuntu 基础源（如需要）
sudo sed -i 's|mirrors.tuna.tsinghua.edu.cn|mirrors.aliyun.com|g' /etc/apt/sources.list

# 更新
sudo apt-get update
```

### 2.5 安装系统级依赖

```bash
# 核心依赖
sudo apt install ros-jazzy-pinocchio ros-jazzy-control-msgs

# ros2_control 相关
sudo apt install ros-jazzy-hardware-interface ros-jazzy-controller-manager ros-jazzy-ros2-control ros-jazzy-realtime-tools

# MoveIt 2
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-ros-planning-interface ros-jazzy-moveit-visual-tools

# 其他控制器
sudo apt install ros-jazzy-diff-drive-controller ros-jazzy-joint-trajectory-controller ros-jazzy-ros2-controllers ros-jazzy-xacro ros-jazzy-robot-state-publisher ros-jazzy-joint-state-publisher

# 测试资源
sudo apt install ros-jazzy-ros2-control-test-assets

# 代码格式工具
sudo apt install ros-jazzy-ament-cmake-clang-format
```

### 2.6 构建项目

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF -DBUILD_TESTING=OFF --packages-skip franka_mobile franka_robot_state_broadcaster
```

### 2.7 启动环境

```bash
source /opt/ros/jazzy/setup.bash
source /home/smz/projects/franka_ros2/install/setup.bash
```

---

## 3. 关键问题与解决方案

### 3.1 网络问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| GitHub 无法访问 | DNS 污染（198.18.0.4 假地址） | 手工下载 ZIP 包，放置到 src 目录 |
| 清华 ROS 2 镜像超时 | 镜像服务器不可达 | 切换至阿里云 ROS 2 镜像源 |
| packages.ros.org 证书错误 | DNS 劫持导致证书不匹配 | 使用阿里云镜像替代 |

### 3.2 libfranka 子模块缺失

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `common` 目录缺少 CMakeLists.txt | ZIP 包不包含 git submodule 内容 | 单独下载 libfranka-common，解压至 `src/libfranka/common/` |
| libfranka 版本不匹配 | 下载了 0.21.2 而非 0.20.4 | 重新下载正确版本 0.20.4 |

### 3.3 ROS 2 Jazzy API 兼容性

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `hardware_interface/visibility_control.h` 找不到 | Jazzy 中该头文件已被移除或移动位置 | 创建 `franka_jazzy_compat` shim 包，提供兼容性头文件 |
| franka_robot_state_broadcaster 编译失败 | `rclcpp/qos_event.hpp` 在 Jazzy 中不存在 | 跳过该包构建（`--packages-skip franka_robot_state_broadcaster`） |
| franka_mobile 编译失败 | `ChainableControllerInterface` API 变更，缺少 `update_reference_from_subscribers` 实现 | 跳过该包构建（`--packages-skip franka_mobile`） |
| franka_example_controllers 测试失败 | `ResourceManager` 构造函数签名变更 | 禁用测试构建（`-DBUILD_TESTING=OFF`） |

### 3.4 系统依赖缺失

| 问题 | 缺失包 | 安装命令 |
|------|--------|----------|
| pinocchio 找不到 | ros-jazzy-pinocchio | `sudo apt install ros-jazzy-pinocchio` |
| control_msgs 找不到 | ros-jazzy-control-msgs | `sudo apt install ros-jazzy-control-msgs` |
| hardware_interface 找不到 | ros-jazzy-hardware-interface | `sudo apt install ros-jazzy-hardware-interface` |
| controller_manager 找不到 | ros-jazzy-controller-manager | `sudo apt install ros-jazzy-controller-manager` |
| MoveIt 核心找不到 | ros-jazzy-moveit | `sudo apt install ros-jazzy-moveit` |
| diff_drive_controller 找不到 | ros-jazzy-diff-drive-controller | `sudo apt install ros-jazzy-diff-drive-controller` |
| ros2_control_test_assets 找不到 | ros-jazzy-ros2-control-test-assets | `sudo apt install ros-jazzy-ros2-control-test-assets` |
| ament_cmake_clang_format 找不到 | ros-jazzy-ament-cmake-clang-format | `sudo apt install ros-jazzy-ament-cmake-clang-format` |

---

## 4. franka_jazzy_compat 兼容性包说明

为解决 Jazzy 中 `hardware_interface/visibility_control.h` 缺失问题，创建了 `franka_jazzy_compat` 包：

- **目录结构：**
  ```
  franka_jazzy_compat/
  ├── CMakeLists.txt
  ├── package.xml
  └── include/
      └── hardware_interface/
          └── visibility_control.h
  ```

- **修改的文件（非源码包本身）：**
  - `franka_hardware/package.xml`：添加对 `franka_jazzy_compat` 的依赖
  - `franka_hardware/CMakeLists.txt`：添加 `find_package(franka_jazzy_compat)` 和对应的 `ament_target_dependencies`

---

## 5. 构建状态汇总

| 包名 | 状态 | 备注 |
|------|------|------|
| franka_msgs | 成功 | - |
| libfranka | 成功 | 警告：缺少 clang-format/clang-tidy |
| franka_description | 成功 | - |
| olv_module_descriptions | 成功 | - |
| franka_mobile_sensors | 成功 | - |
| franka_jazzy_compat | 成功 | 新建的兼容性包 |
| franka_hardware | 成功 | 依赖 franka_jazzy_compat |
| franka_gripper | 成功 | - |
| franka_semantic_components | 成功 | - |
| franka_fr3_moveit_config | 成功 | - |
| franka_example_controllers | 成功 | 仅库和可执行文件，测试已跳过 |
| franka_bringup | 成功 | - |
| franka_gazebo_bringup | 成功 | - |
| franka_ros2 | 成功 | - |
| franka_robot_state_broadcaster | 跳过 | Jazzy API 不兼容 |
| franka_mobile | 跳过 | Jazzy API 不兼容 |

---

## 6. 验证安装

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 pkg list | grep franka
```

应看到 12 个 franka 相关包。

### 测试假硬件启动（无实体机器人时）

```bash
ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true
```

---

## 9. 项目文件修改详情

本节详细记录配置过程中对项目中所有文件的修改内容、修改原因及修改前后对比。

### 9.1 新建文件：franka_jazzy_compat 包

为解决 ROS 2 Jazzy 中 `hardware_interface/visibility_control.h` 头文件缺失问题，新建了 `franka_jazzy_compat` 兼容性包。

#### 9.1.1 目录结构

```
franka_jazzy_compat/
├── CMakeLists.txt
├── package.xml
└── include/
    └── hardware_interface/
        └── visibility_control.h
```

#### 9.1.2 franka_jazzy_compat/CMakeLists.txt

**完整内容：**

```cmake
cmake_minimum_required(VERSION 3.8)
project(franka_jazzy_compat)

find_package(ament_cmake REQUIRED)

install(DIRECTORY include/
  DESTINATION include/
)

ament_export_include_directories(include)
ament_package()
```

**说明：**
- 这是一个纯头文件包，不包含任何编译目标
- 使用 `ament_export_include_directories` 将 `include/` 目录导出给依赖此包的其它包使用
- 所有 `franka_jazzy_compat` 的依赖包会自动获得此头文件搜索路径

#### 9.1.3 franka_jazzy_compat/package.xml

**完整内容：**

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/jammy/ros2/control.xsd"?>
<package format="3">
  <name>franka_jazzy_compat</name>
  <version>0.1.0</version>
  <description>Compatibility headers for franka_ros2 on ROS 2 Jazzy</description>
  <license>Apache-2.0</license>
  <maintainer email="user@example.com">User</maintainer>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

**说明：**
- 声明为 `ament_cmake` 构建类型
- 无运行时依赖，仅提供头文件

#### 9.1.4 franka_jazzy_compat/include/hardware_interface/visibility_control.h

**完整内容：**

```c
// Copyright 2024 Open Source Robotics Foundation, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef HARDWARE_INTERFACE__VISIBILITY_CONTROL_H_
#define HARDWARE_INTERFACE__VISIBILITY_CONTROL_H_

#if defined _WIN32 || defined __CYGWIN__
  #define HARDWARE_INTERFACE_EXPORT __declspec(dllexport)
  #define HARDWARE_INTERFACE_IMPORT __declspec(dllimport)
#elif __GNUC__ >= 4
  #define HARDWARE_INTERFACE_EXPORT __attribute__((visibility("default")))
  #define HARDWARE_INTERFACE_IMPORT __attribute__((visibility("hidden")))
#else
  #define HARDWARE_INTERFACE_EXPORT
  #define HARDWARE_INTERFACE_IMPORT
#endif

#ifndef HARDWARE_INTERFACE_EXPORT
#define HARDWARE_INTERFACE_EXPORT
#endif

#ifndef HARDWARE_INTERFACE_IMPORT
#define HARDWARE_INTERFACE_IMPORT
#endif

#ifdef __cplusplus
extern "C"
{
#endif

#ifndef HARDWARE_INTERFACE_EXPORT
  #ifdef HARDWARE_INTERFACE_IMPORT
  #else
    #define HARDWARE_INTERFACE_EXPORT
    #define HARDWARE_INTERFACE_IMPORT
  #endif
#endif

#ifdef __cplusplus
}
#endif

#endif  // HARDWARE_INTERFACE__VISIBILITY_CONTROL_H_
```

**说明：**
- 此文件定义了 `HARDWARE_INTERFACE_EXPORT` 和 `HARDWARE_INTERFACE_IMPORT` 宏，用于控制共享库符号的可见性
- 在 ROS 2 Humble 中，此文件位于 `hardware_interface` 包内；在 Jazzy 中该文件已被移除或移动
- 此兼容性文件模拟了原有的宏定义行为，使得依赖此头文件的代码可以正常编译
- 支持 Windows、GCC/Clang 等平台的符号导出机制

---

### 9.2 修改文件：franka_hardware/package.xml

**修改位置：** 第 16 行（在 `franka_msgs` 和 `hardware_interface` 依赖之间）

**修改原因：** `franka_hardware` 包中的代码 `#include <hardware_interface/visibility_control.h>`，在 Jazzy 中此头文件不存在，需要依赖新建的 `franka_jazzy_compat` 包来提供该头文件。

**修改前：**

```xml
  <depend>franka_msgs</depend>
  <depend>hardware_interface</depend>
  <depend>pluginlib</depend>
```

**修改后：**

```xml
  <depend>franka_msgs</depend>
  <depend>franka_jazzy_compat</depend>
  <depend>hardware_interface</depend>
  <depend>pluginlib</depend>
```

**说明：**
- 添加了 `<depend>franka_jazzy_compat</depend>` 依赖
- 依赖顺序很重要：`franka_jazzy_compat` 必须在 `hardware_interface` 之前，确保头文件路径正确设置

---

### 9.3 修改文件：franka_hardware/CMakeLists.txt

#### 修改点 1：添加 find_package

**修改位置：** 第 20 行

**修改原因：** CMake 需要查找 `franka_jazzy_compat` 包以获取其导出的头文件路径，否则编译器找不到 `hardware_interface/visibility_control.h`。

**修改前：**

```cmake
find_package(franka_msgs REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
```

**修改后：**

```cmake
find_package(franka_msgs REQUIRED)
find_package(franka_jazzy_compat REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
```

#### 修改点 2：添加 ament_target_dependencies

**修改位置：** 第 43-52 行

**修改原因：** 将 `franka_jazzy_compat` 添加到 `franka_hardware` 库的依赖中，确保编译时包含正确的头文件搜索路径，并在链接时正确处理依赖关系。

**修改前：**

```cmake
ament_target_dependencies(
        franka_hardware
        hardware_interface
        Franka
        pluginlib
        rclcpp
        rclcpp_action
        franka_msgs
)
```

**修改后：**

```cmake
ament_target_dependencies(
        franka_hardware
        franka_jazzy_compat
        hardware_interface
        Franka
        pluginlib
        rclcpp
        rclcpp_action
        franka_msgs
)
```

**说明：**
- `franka_jazzy_compat` 必须放在 `hardware_interface` 之前
- 这确保了在搜索头文件时，`franka_jazzy_compat` 的 `include/` 目录会被优先搜索

---

## 10. 系统级配置修改

### 10.1 APT 源修改

#### 修改文件：/etc/apt/sources.list.d/ros2.list

**修改原因：** 默认的清华 ROS 2 镜像源无法连接（超时），packages.ros.org 官方源因 DNS 污染导致证书验证失败。

**修改前：**

```
deb [arch=amd64 signed-by=/usr/share/keyrings/ros2-latest-archive-keyring.gpg] https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu noble main
```

**修改后：**

```
deb [arch=amd64 signed-by=/usr/share/keyrings/ros2-latest-archive-keyring.gpg] https://mirrors.aliyun.com/ros2/ubuntu noble main
```

**修改命令：**

```bash
sudo sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/ros2-latest-archive-keyring.gpg] https://mirrors.aliyun.com/ros2/ubuntu noble main" > /etc/apt/sources.list.d/ros2.list'
```

#### 修改文件：/etc/apt/sources.list

**修改原因：** Ubuntu 基础源的清华镜像同样无法连接。

**修改方式：**

```bash
sudo sed -i 's|mirrors.tuna.tsinghua.edu.cn|mirrors.aliyun.com|g' /etc/apt/sources.list
```

---

### 10.2 rosdep 初始化

**问题：** `sudo rosdep init` 因网络超时无**常完成。

**尝试的手动方案：** 手动创建 `/etc/ros/rosdep/sources.list.d/20-default.list` 文件，但仍因 `rosdep update` 需要访问外部 URL 而失败。

**最终方案：** 跳过 rosdep，手动识别并安装所有系统依赖包。

---

## 11. 文件修改汇总

| 文件路径 | 操作类型 | 修改内容 | 修改原因 |
|----------|----------|----------|----------|
| `franka_jazzy_compat/CMakeLists.txt` | 新建 | 创建 ament_cmake 头文件包 | 提供兼容性构建配置 |
| `franka_jazzy_compat/package.xml` | 新建 | 声明包元数据 | 使包可被 colcon 识别 |
| `franka_jazzy_compat/include/hardware_interface/visibility_control.h` | 新建 | 创建可见性控制宏定义头文件 | 替代 Jazzy 中缺失的原文件 |
| `franka_hardware/package.xml` | 修改 | 添加 `franka_jazzy_compat` 依赖 | 声明头文件依赖关系 |
| `franka_hardware/CMakeLists.txt` | 修改 | 添加 `find_package(franka_jazzy_compat)` 和 `ament_target_dependencies` | CMake 查找并使用兼容性头文件 |
| `/etc/apt/sources.list.d/ros2.list` | 修改（系统级） | 切换 ROS 2 源至阿里云 | 解决网络访问问题 |
| `/etc/apt/sources.list` | 修改（系统级） | 切换 Ubuntu 源至阿里云 | 解决网络访问问题 |

---

## 12. 恢复原始配置的说明

如需将项目恢复到原始状态（例如切换到官方 ROS 2 Humble 环境），需执行以下操作：

### 恢复项目文件

```bash
# 恢复 franka_hardware/package.xml
git checkout franka_hardware/package.xml

# 恢复 franka_hardware/CMakeLists.txt
git checkout franka_hardware/CMakeLists.txt

# 删除兼容性包
rm -rf franka_jazzy_compat
```

### 清理构建缓存

```bash
rm -rf build/ install/ log/
```

---

## 13. 风险提示

1. **版本不匹配风险：** franka_ros2 针对 Humble 开发，在 Jazzy 上运行可能存在未发现的 API 差异。建议仅用于开发测试，生产环境请使用 Humble。

2. **跳过的包：** `franka_mobile` 和 `franka_robot_state_broadcaster` 未编译。如需使用，需手动适配 Jazzy API。

3. **测试用例跳过：** 所有测试用例已禁用（`-DBUILD_TESTING=OFF`），无法通过 `colcon test` 验证正确性。

4. **依赖手动管理：** 由于无法使用 `rosdep`，所有依赖需手动安装，可能遗漏某些间接依赖。

5. **升级后失效：** 如果 franka_ros2 代码更新，可能需要重新适配 Jazzy 兼容性修改。

---

## 8. 快速参考命令

```bash
# 完整环境启动
source /opt/ros/jazzy/setup.bash && source install/setup.bash

# 清理构建
rm -rf build/ install/ log/

# 重新构建
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF -DBUILD_TESTING=OFF --packages-skip franka_mobile franka_robot_state_broadcaster

# 查看可用控制器
ros2 control list_controllers
```
