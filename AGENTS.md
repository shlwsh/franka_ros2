# Repository Guidelines

## 项目结构与模块组织
本仓库是一个 ROS 2 工作区，根目录下包含多个功能包。核心包包括 `franka_hardware/`、`franka_semantic_components/`、`franka_robot_state_broadcaster/`、`franka_example_controllers/`、`franka_bringup/`、`franka_gripper/`、`franka_mobile/`、`franka_msgs/` 和 `franka_api_server/`。C++ 源码通常位于 `src/`，公开头文件位于 `include/`，Python 节点位于 `<package>/<package>/`，启动文件位于 `launch/`，测试位于各包的 `test/` 目录。公共文档在 `docs/` 与 `docs-zh/`，辅助脚本集中在 `scripts/`。

## 构建、测试与开发命令
在工作区根目录执行标准构建：

```bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

执行接近 CI 的构建检查：

```bash
colcon build --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCHECK_TIDY=ON
```

运行完整测试：

```bash
colcon test && colcon test-result --verbose
```

只测试单个包时可使用 `--packages-select franka_api_server`。常用本地脚本包括：`scripts/start.sh` 用于启动 fake hardware + MoveIt，`scripts/startapi.sh` 用于启动 API 服务，`scripts/testall.sh` 用于启动联合测试环境。运行前先加载环境：`source /opt/ros/<distro>/setup.bash && source install/setup.bash`。

## 代码风格与命名约定
C++ 遵循 `.clang-format`：基于 Chromium，使用 C++11，列宽 100，自动排序 `#include`。Python 遵循 `pyproject.toml` 中的 Ruff 配置：空格缩进、单引号、列宽 99，并保持导入排序一致。命名上遵循 ROS 2 常见约定：文件、函数、话题、参数使用 `snake_case`，C++ 类使用 `PascalCase`，功能包统一使用 `franka_` 前缀。

## 测试指南
大多数 C++ 功能包使用 `ament_cmake_gmock` 或 `ament_cmake_gtest`，Python 功能包使用 `pytest`，并配合 `ament_flake8`、`ament_pep257` 等 ament lint 工具。新增测试应放在对应包的 `test/` 目录，文件命名建议为 `test_<feature>.cpp` 或 `test_<feature>.py`。涉及真实硬件的测试不要混入默认本地测试流程，当前 CI 会通过正则排除 `test_hardware`。

## 提交与合并请求要求
最近提交记录主要使用简短的约定式前缀，例如 `fix: ...`、`chore: ...`；继续保持这种祈使句、范围明确的风格。每个提交都必须包含 DCO 签名，例如 `Signed-off-by: Your Name <email>`。提交 PR 时应说明影响的功能包、行为变化、已执行的验证命令；若改动涉及 `franka_api_server/static/` 这类前端界面，再附上截图。

## 配置说明
修改脚本前先确认 ROS 发行版假设是否一致：GitHub CI 目前仍按 ROS 2 Humble 构建，而仓库中的本地辅助脚本当前默认加载 ROS 2 Jazzy。
