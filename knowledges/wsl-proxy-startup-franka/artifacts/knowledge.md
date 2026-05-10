# 知识库：Franka ROS 2 项目调试与网络代理总结

本文档记录了在开发 Franka ROS 2 API 服务器、前端控制面板以及自动化 Git 提交流程中积累的关键知识点和踩坑经验。

## 1. ROS 2 多节点启动与进程管理

### 1.1 脚本冲突与进程误杀
- **问题现象**：在分别运行 `start.sh`（启动 MoveIt/RViz）和 `startapi.sh`（启动 API 服务）时，前端控制面板频繁报 `Failed to fetch`，且终端提示 API 进程以 `exit code -9` 意外退出。
- **根本原因**：`start.sh` 中包含了一条大范围清理僵尸进程的指令 `killall -9 ... api_server`。当 API 服务已经启动时，再次运行硬件启动脚本会把 API 服务强制杀掉。
- **解决方案**：将不同服务脚本的 `killall` 目标严格隔离。更优的方案是编写统一启动脚本（如 `testall.sh`）。

### 1.2 统一启动与优雅退出 (testall.sh)
- **实现原理**：在一个 Bash 脚本中，可以通过 `&` 将阻塞的 `ros2 launch` 放入后台运行，并记录其 PID (`MOVEIT_PID=$!`)。
- **优雅退出**：通过让主程序（如 API Server）在前台运行，当用户按下 `Ctrl+C` 结束脚本时，脚本后续的清理命令（`kill $MOVEIT_PID` 和 `killall`）会自动执行，从而避免遗留僵尸进程。

## 2. FastAPI 与 WebSocket 依赖

- **问题现象**：API 服务器启动正常，但前端 Dashboard 无法接收实时的机器人模式和关节状态。后端日志持续报警：`No supported WebSocket library detected.` 及 `Unsupported upgrade request.`。
- **根本原因**：FastAPI 默认不包含 WebSocket 处理库。如果没有手动安装，Uvicorn 无法处理 WebSocket Upgrade 请求。
- **解决方案**：
  在 Python 环境中显式安装 WebSocket 库：
  ```bash
  pip install websockets
  # 或者安装 uvicorn 的标准完整版
  pip install "uvicorn[standard]"
  ```

## 3. WSL2 与 TUN 透明代理 (Git Push 挂起/报错)

这是在本地自动化提交流程 (`mygit.sh`) 中遇到的经典网络配置问题。

### 3.1 错误表现
- 脚本中通过 `curl` 访问大模型 API 生成提交信息完全正常。
- 但最后执行 `git push` 时瞬间报错：`Failed to connect to 127.0.0.1 port 7890 after 0 ms: Couldn't connect to server`。

### 3.2 原因深度分析
1. **WSL2 的 localhost 隔离**：在 WSL2 中，`127.0.0.1` 指向的是 WSL 这台轻量级 Linux 虚拟机本身，而不是 Windows 宿主机。Windows 上的代理软件（如 Clash 监听的 7890 端口）在 WSL 的 `127.0.0.1` 上是不可见的。
2. **TUN 透明代理机制**：用户的 Windows 代理软件开启了 **TUN 模式 (虚拟网卡)** 和 **Fake-IP**。这意味着所有去往 `github.com` 的 DNS 请求都会被劫持并返回类似 `198.18.0.x` 的伪造 IP，流量在底层会被自动捕获并代理。
3. **环境变量画蛇添足**：在 `mygit.sh` 脚本中，为了确保 `curl` 正常工作，加载了环境变量 `https_proxy=http://127.0.0.1:7890`。当 Git 读取到这个环境变量时，它会**放弃系统的底层透明代理机制**，强制去连接指定的 `127.0.0.1:7890`。由于该端口在 WSL 中未开放，导致立即拒绝连接。

### 3.3 终极解决方案
在开启了 TUN（透明代理）的网络环境下，**不要为 Git 设置显式的代理环境变量**。
在自动化脚本执行 `git push` 之前，强制清除可能存在的代理变量，让流量自然流入底层的透明代理网卡：
```bash
# 在 git push 前执行
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
git push
```
这样不仅能解决 WSL 端口映射问题，也能完美配合 Fake-IP 模式完成远程推送。
