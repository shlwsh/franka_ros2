# Franka ROS2 API 服务层技术实现方案

> **文档版本**: v1.1  
> **创建日期**: 2026-05-08  
> **最后更新**: 2026-05-08  
> **目标**: 为 Franka ROS2 项目添加 RESTful API 服务层 + 内置 Web 控制面板，允许外部客户端通过 HTTP/WebSocket 接口控制机械臂，并提供可视化前端界面验证所有 API

---

## 1. 项目背景

当前 Franka ROS2 项目通过 ROS2 原生接口（Topic、Service、Action）与机械臂交互。这种方式要求客户端必须运行在 ROS2 环境中，限制了非 ROS2 系统（如 Web 前端、手机 App、MES 系统、Python 脚本等）的接入能力。

**本方案的目标**是在 ROS2 系统之上构建一层 REST API + WebSocket 服务，作为"桥接层"，让任意支持 HTTP 协议的客户端都能控制机械臂。

---

## 2. 系统架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    外部客户端                             │
│   Web UI / 手机 App / MES 系统 / Python 脚本 / cURL      │
└──────────────┬──────────────────────┬────────────────────┘
               │ HTTP REST            │ WebSocket
               ▼                      ▼
┌─────────────────────────────────────────────────────────┐
│              franka_api_server (新增 ROS2 包)            │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ FastAPI 路由  │  │ WebSocket    │  │ 安全 & 认证    │  │
│  │ (REST 接口)  │  │ (实时数据流)  │  │ (API Key)     │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────────┘  │
│         │                 │                              │
│  ┌──────▼─────────────────▼──────┐                      │
│  │      ROS2 Bridge 层           │                      │
│  │  (rclpy Node + 客户端封装)     │                      │
│  └──────┬────────────────────────┘                      │
└─────────┼───────────────────────────────────────────────┘
          │ ROS2 Topic / Service / Action
          ▼
┌─────────────────────────────────────────────────────────┐
│              现有 Franka ROS2 系统                        │
│  controller_manager / MoveIt2 / franka_gripper 等        │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| Web 框架 | **FastAPI** (Python) | 原生 async 支持、自动生成 OpenAPI 文档、与 rclpy 同为 Python 生态 |
| 实时通信 | **WebSocket** (FastAPI 内置) | 用于实时推送机器人状态（关节角、位姿、错误信息等） |
| ROS2 客户端 | **rclpy** | ROS2 官方 Python 客户端库，可直接调用 Topic/Service/Action |
| 序列化 | **JSON** | 通用标准格式，所有客户端都能解析 |
| 认证 | **API Key** (Header) | 轻量级安全认证，适合内网环境 |
| 文档 | **Swagger UI** (自动生成) | FastAPI 自动在 `/docs` 端点提供交互式 API 文档 |

---

## 4. 新增 ROS2 包结构

```
franka_api_server/
├── package.xml                    # ROS2 包描述
├── setup.py                       # Python 包安装配置
├── setup.cfg
├── resource/
│   └── franka_api_server          # ament 资源标记
├── config/
│   └── api_server.yaml            # 服务器配置 (端口、认证等)
├── launch/
│   └── api_server.launch.py       # 启动文件
├── franka_api_server/
│   ├── __init__.py
│   ├── main.py                    # 入口：启动 FastAPI + rclpy
│   ├── app.py                     # FastAPI 应用实例
│   ├── config.py                  # 配置加载
│   ├── auth.py                    # API Key 认证中间件
│   ├── ros_bridge.py              # ROS2 桥接层 (核心)
│   ├── models/                    # Pydantic 数据模型
│   │   ├── __init__.py
│   │   ├── robot_state.py         # 机器人状态模型
│   │   ├── motion.py              # 运动指令模型
│   │   └── gripper.py             # 夹爪控制模型
│   └── routers/                   # API 路由模块
│       ├── __init__.py
│       ├── status.py              # 状态查询接口
│       ├── motion.py              # 运动控制接口
│       ├── gripper.py             # 夹爪控制接口
│       ├── controller.py          # 控制器管理接口
│       └── ws.py                  # WebSocket 实时数据
└── test/
    └── test_api.py                # 接口测试
```

---

## 5. API 接口设计

### 5.1 状态查询 (`/api/v1/status`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/status/robot` | 获取机器人完整状态 |
| GET | `/api/v1/status/joints` | 获取当前关节角度 |
| GET | `/api/v1/status/pose` | 获取末端执行器位姿 |
| GET | `/api/v1/status/errors` | 获取当前错误信息 |
| GET | `/api/v1/status/mode` | 获取机器人运行模式 |

**响应示例** (`GET /api/v1/status/joints`):
```json
{
  "timestamp": "2026-05-08T15:30:00Z",
  "joint_positions": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
  "joint_velocities": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
  "joint_efforts": [0.1, -5.2, 0.3, -1.8, 0.0, 0.5, 0.0],
  "joint_names": ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7"]
}
```

### 5.2 运动控制 (`/api/v1/motion`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/motion/move_joints` | 关节空间点对点运动 (PTP) |
| POST | `/api/v1/motion/move_to_pose` | 笛卡尔空间运动 (MoveIt2) |
| POST | `/api/v1/motion/move_to_start` | 回到初始位姿 |
| POST | `/api/v1/motion/stop` | 紧急停止当前运动 |
| POST | `/api/v1/motion/error_recovery` | 错误恢复 |

**请求示例** (`POST /api/v1/motion/move_joints`):
```json
{
  "goal_joint_configuration": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
  "max_velocity_scaling": 0.3,
  "goal_tolerance": 0.01,
  "async": true
}
```

**响应示例**:
```json
{
  "task_id": "motion_abc123",
  "status": "accepted",
  "message": "Motion command accepted and executing"
}
```

### 5.3 夹爪控制 (`/api/v1/gripper`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/gripper/grasp` | 抓取 (指定宽度、速度、力) |
| POST | `/api/v1/gripper/move` | 移动到指定宽度 |
| POST | `/api/v1/gripper/homing` | 夹爪归位 |
| GET  | `/api/v1/gripper/state` | 获取夹爪当前状态 |

**请求示例** (`POST /api/v1/gripper/grasp`):
```json
{
  "width": 0.04,
  "speed": 0.1,
  "force": 50.0,
  "epsilon_inner": 0.005,
  "epsilon_outer": 0.005
}
```

### 5.4 控制器管理 (`/api/v1/controller`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/controller/list` | 列出所有可用控制器 |
| POST | `/api/v1/controller/switch` | 切换活跃控制器 |
| GET | `/api/v1/controller/active` | 获取当前活跃控制器 |

### 5.5 参数配置 (`/api/v1/config`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/config/joint_stiffness` | 设置关节刚度 |
| POST | `/api/v1/config/cartesian_stiffness` | 设置笛卡尔刚度 |
| POST | `/api/v1/config/collision_behavior` | 设置碰撞行为阈值 |
| POST | `/api/v1/config/load` | 设置末端负载参数 |

### 5.6 WebSocket 实时数据 (`/ws`)

| 端点 | 说明 |
|------|------|
| `/ws/robot_state` | 实时推送机器人完整状态 (可配置频率) |
| `/ws/joint_states` | 实时推送关节状态 |

**WebSocket 消息格式**:
```json
{
  "type": "joint_states",
  "timestamp": "2026-05-08T15:30:00.123Z",
  "data": {
    "positions": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
    "velocities": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  }
}
```

---

## 6. 核心实现思路

### 6.1 ROS2 Bridge 层 (`ros_bridge.py`)

这是整个服务层的核心，负责在 FastAPI 的 async 世界和 rclpy 之间搭桥：

```python
# 伪代码概要
class RosBridge:
    def __init__(self):
        self.node = rclpy.create_node('franka_api_bridge')
        
        # 订阅器 — 持续接收机器人状态
        self.state_sub = self.node.create_subscription(
            FrankaRobotState, '/franka_robot_state_broadcaster/robot_state', ...)
        self.joint_sub = self.node.create_subscription(
            JointState, '/joint_states', ...)
        
        # Action 客户端 — 用于发送运动指令
        self.ptp_client = ActionClient(self.node, PTPMotion, '/ptp_motion')
        self.grasp_client = ActionClient(self.node, Grasp, '/franka_gripper/grasp')
        self.move_client = ActionClient(self.node, Move, '/franka_gripper/move')
        self.homing_client = ActionClient(self.node, Homing, '/franka_gripper/homing')
        
        # Service 客户端 — 用于参数配置
        self.set_stiffness_client = self.node.create_client(
            SetJointStiffness, '/set_joint_stiffness')
        
        # 后台线程运行 rclpy spin
        self._spin_thread = Thread(target=self._spin, daemon=True)
        self._spin_thread.start()
```

### 6.2 异步任务管理

对于长时间运行的运动指令，使用"任务 ID"模式：

1. 客户端发起 POST 请求 → 返回 `task_id`
2. 后台通过 ROS2 Action 执行
3. 客户端可通过 `GET /api/v1/motion/task/{task_id}` 查询进度
4. 也可通过 WebSocket 接收实时反馈

### 6.3 线程模型

```
主线程: FastAPI (uvicorn) — 处理 HTTP 请求
后台线程: rclpy.spin(node) — 处理 ROS2 回调
通信方式: asyncio.Queue / threading.Event 在两者之间传递数据
```

---

## 7. 配置文件设计 (`config/api_server.yaml`)

```yaml
api_server:
  ros__parameters:
    # 服务器配置
    host: "0.0.0.0"
    port: 8080
    
    # 认证配置
    auth_enabled: true
    api_key: "franka-api-default-key"
    
    # WebSocket 配置
    ws_publish_rate: 30.0  # Hz
    
    # ROS2 Topic 配置
    joint_states_topic: "/joint_states"
    robot_state_topic: "/franka_robot_state_broadcaster/robot_state"
    
    # 安全限制
    max_velocity_scaling: 0.5
    enable_collision_check: true
    
    # CORS 配置 (跨域)
    cors_origins: ["*"]
```

---

## 8. 启动方式

### 8.1 独立启动
```bash
ros2 launch franka_api_server api_server.launch.py
```

### 8.2 与 Franka 系统一起启动
```bash
# 先启动 Franka 底层
ros2 launch franka_bringup franka.launch.py robot_type:=fr3 use_fake_hardware:=true

# 再启动 API 服务层
ros2 launch franka_api_server api_server.launch.py
```

启动后访问 `http://localhost:8080/docs` 即可看到自动生成的 Swagger 交互式文档。

---

## 9. 依赖项

```xml
<!-- package.xml 中新增的依赖 -->
<exec_depend>rclpy</exec_depend>
<exec_depend>franka_msgs</exec_depend>
<exec_depend>sensor_msgs</exec_depend>
<exec_depend>geometry_msgs</exec_depend>
<exec_depend>controller_manager_msgs</exec_depend>
```

```
# Python 依赖 (pip)
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0
```

---

## 10. 客户端调用示例

### Python
```python
import requests

BASE_URL = "http://localhost:8080/api/v1"
HEADERS = {"X-API-Key": "franka-api-default-key"}

# 查询关节状态
resp = requests.get(f"{BASE_URL}/status/joints", headers=HEADERS)
print(resp.json())

# 发送运动指令
resp = requests.post(f"{BASE_URL}/motion/move_joints", headers=HEADERS, json={
    "goal_joint_configuration": [0, -0.785, 0, -2.356, 0, 1.571, 0.785],
    "max_velocity_scaling": 0.3,
    "goal_tolerance": 0.01
})
print(resp.json())
```

### cURL
```bash
# 查询状态
curl -H "X-API-Key: franka-api-default-key" http://localhost:8080/api/v1/status/joints

# 夹爪抓取
curl -X POST -H "X-API-Key: franka-api-default-key" \
  -H "Content-Type: application/json" \
  -d '{"width":0.04,"speed":0.1,"force":50}' \
  http://localhost:8080/api/v1/gripper/grasp
```

### JavaScript (WebSocket)
```javascript
const ws = new WebSocket("ws://localhost:8080/ws/joint_states?api_key=franka-api-default-key");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Joint positions:", data.data.positions);
};
```

---

## 11. 安全考虑

| 措施 | 说明 |
|------|------|
| API Key 认证 | 所有请求需携带 `X-API-Key` Header |
| 速度限制 | 服务端强制限制最大速度缩放系数 |
| 碰撞检测 | MoveIt2 运动规划自带碰撞检测 |
| 请求频率限制 | 防止客户端发送过于频繁的指令 |
| CORS 配置 | 可限制允许访问的来源域名 |
| 只读/读写分离 | 可配置某些 API Key 仅有查询权限 |

---

## 12. 实施步骤

| 阶段 | 内容 | 预计工时 |
|------|------|----------|
| 1 | 创建 `franka_api_server` 包结构，配置依赖 | 0.5 天 |
| 2 | 实现 `ros_bridge.py` (ROS2 桥接核心) | 1 天 |
| 3 | 实现状态查询 API + WebSocket 推送 | 1 天 |
| 4 | 实现运动控制 API (PTP + MoveIt2) | 1 天 |
| 5 | 实现夹爪控制 + 控制器管理 API | 0.5 天 |
| 6 | 实现认证、安全、配置加载 | 0.5 天 |
| 7 | **前端控制面板** - 仪表盘 + 实时状态 | 1 天 |
| 8 | **前端控制面板** - 运动/夹爪/API 测试页面 | 1 天 |
| 9 | 编写测试 + Swagger 文档完善 | 0.5 天 |
| **合计** | | **7 天** |

---

## 13. 与现有系统的关系

本方案**不修改**任何现有的 ROS2 包，而是作为一个独立的新包 `franka_api_server` 纯粹作为"翻译层"存在：

- **读取**：订阅现有的 `/joint_states`、`/franka_robot_state_broadcaster/robot_state` 等 Topic
- **写入**：调用现有的 ROS2 Service（如 `SetJointStiffness`）和 Action（如 `PTPMotion`、`Grasp`）
- **控制器管理**：调用 `controller_manager` 的标准 Service 接口

现有的 ROS2 原生通信方式完全不受影响，API 服务层只是多了一个访问入口。

---

## 14. 内置 Web 控制面板

为方便验证 API 及日常操控，本方案内置一套 Web 前端控制面板，随 API 服务一同启动，通过浏览器即可访问。

### 14.1 前端技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 构建方式 | **纯静态 HTML/CSS/JS** | 无需 Node.js 构建，FastAPI 直接托管静态文件，部署最简 |
| 样式 | **Vanilla CSS + CSS Variables** | 暗色主题，现代 glassmorphism 风格，零依赖 |
| 图表库 | **Chart.js (CDN)** | 轻量级，用于关节角度/力矩实时曲线 |
| 图标 | **Lucide Icons (CDN)** | 现代化 SVG 图标库 |
| HTTP 请求 | **Fetch API** | 浏览器原生，无需额外依赖 |
| 实时数据 | **WebSocket API** | 浏览器原生 WebSocket 连接 |

### 14.2 前端文件结构

```
franka_api_server/
  static/                          # FastAPI 静态文件托管目录
    index.html                     # 主页面 (单页应用入口)
    css/
      style.css                    # 全局样式 (暗色主题 + 设计系统)
    js/
      app.js                       # 应用主逻辑 (路由、初始化)
      api.js                       # API 客户端封装 (fetch + WebSocket)
      dashboard.js                 # 仪表盘页面逻辑
      motion.js                    # 运动控制页面逻辑
      gripper.js                   # 夹爪控制页面逻辑
      controller.js                # 控制器管理页面逻辑
      config.js                    # 参数配置页面逻辑
      api-tester.js                # API 测试工具页面逻辑
    assets/
      logo.svg                     # 项目 Logo
```

### 14.3 页面设计 (共 6 个功能页面)

前端采用左侧导航栏 + 右侧内容区的经典布局。

**页面 1：仪表盘 (Dashboard)** - 首页概览

| 区域 | 内容 |
|------|------|
| 顶部状态条 | 机器人模式 (IDLE/MOVE/ERROR)、连接状态指示灯、控制命令成功率 |
| 关节状态卡片 | 7 个关节的当前角度，以弧形进度条展示 |
| 末端位姿卡片 | XYZ 位置 + RPY 姿态，数值实时更新 |
| 力/力矩实时曲线 | Chart.js 绘制外部力矩实时波形 (30Hz 滚动窗口) |
| 错误信息面板 | 当前错误列表，一键"错误恢复"按钮 |

**页面 2：运动控制 (Motion Control)** - 发送运动指令

| 区域 | 内容 |
|------|------|
| 关节空间控制 | 7 个滑块 (Slider)，可拖动设置目标角度；显示当前值与目标值 |
| 参数设置 | 速度缩放系数滑块 (0-1)、目标容差输入框 |
| 快捷动作按钮 | 回到初始位姿 / 紧急停止 / 错误恢复 |
| 执行按钮 | 发送 PTP 运动 - 调用 `POST /api/v1/motion/move_joints` |
| 任务状态面板 | 显示 task_id、状态、进度反馈 |

**页面 3：夹爪控制 (Gripper Control)**

| 区域 | 内容 |
|------|------|
| 当前状态 | 夹爪宽度数值 + 可视化柱状图 |
| 抓取面板 | 输入：宽度/速度/力/epsilon；按钮：执行抓取 |
| 移动面板 | 输入：目标宽度/速度；按钮：移动夹爪 |
| 归位按钮 | 夹爪归位 (Homing) |
| 操作日志 | 最近操作结果 (成功/失败 + 错误信息) |

**页面 4：控制器管理 (Controller Manager)**

| 区域 | 内容 |
|------|------|
| 控制器列表 | 表格：名称、类型、状态 (active/inactive) |
| 切换操作 | 每行一个切换按钮，激活/停用控制器 |
| 当前活跃控制器 | 高亮显示 |

**页面 5：参数配置 (Configuration)**

| 区域 | 内容 |
|------|------|
| 关节刚度 | 7 个输入框 + 应用按钮 |
| 笛卡尔刚度 | 6 个输入框 (x/y/z/roll/pitch/yaw) + 应用按钮 |
| 碰撞行为 | 力矩/力的上下阈值输入 + 应用按钮 |
| 末端负载 | 质量、质心位置、惯性矩阵 + 应用按钮 |

**页面 6：API 测试工具 (API Tester)** - 类似 Postman

| 区域 | 内容 |
|------|------|
| 请求构造器 | 下拉选择 HTTP 方法 (GET/POST)；路径输入框 (自动补全) |
| 请求头 | 自动填充 API Key，支持自定义 Header |
| 请求体编辑器 | JSON 编辑区，按接口自动填充示例模板 |
| 发送按钮 | 发送请求 |
| 响应展示区 | 状态码 + 格式化 JSON + 耗时统计 |
| 预设接口列表 | 侧边栏列出所有 API 端点，点击自动填充 |

### 14.4 设计风格

- **主题**：深色 Dark Mode，主色调科技蓝 (#3b82f6)，深灰背景 (#0f172a)
- **卡片**：半透明玻璃质感 (glassmorphism)，backdrop-filter blur
- **动画**：状态变化平滑过渡，数值更新闪烁提示
- **响应式**：适配桌面和平板屏幕
- **字体**：Google Fonts - Inter

### 14.5 前端与后端集成

FastAPI 通过 StaticFiles 中间件直接托管前端静态文件：

```python
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Franka API Server")

# API 路由
app.include_router(status_router, prefix="/api/v1")
app.include_router(motion_router, prefix="/api/v1")

# 静态文件托管 (前端控制面板)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

启动后访问入口：
- `http://localhost:8080/` - Web 控制面板
- `http://localhost:8080/docs` - Swagger API 文档
- `http://localhost:8080/api/v1/...` - REST API 端点

### 14.6 前端 API 客户端封装 (api.js 核心设计)

```javascript
class FrankaApiClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async request(method, path, body) {
    const resp = await fetch(this.baseUrl + '/api/v1' + path, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
      },
      body: body ? JSON.stringify(body) : null,
    });
    return { status: resp.status, data: await resp.json() };
  }

  // 状态查询
  getJoints()     { return this.request('GET', '/status/joints'); }
  getPose()       { return this.request('GET', '/status/pose'); }
  getRobotState() { return this.request('GET', '/status/robot'); }

  // 运动控制
  moveJoints(cfg) { return this.request('POST', '/motion/move_joints', cfg); }
  moveToStart()   { return this.request('POST', '/motion/move_to_start'); }
  stopMotion()    { return this.request('POST', '/motion/stop'); }

  // 夹爪
  grasp(params)   { return this.request('POST', '/gripper/grasp', params); }
  homingGripper() { return this.request('POST', '/gripper/homing'); }

  // WebSocket
  connectWS(endpoint, onMessage) {
    const ws = new WebSocket(
      'ws://' + location.host + '/ws/' + endpoint + '?api_key=' + this.apiKey
    );
    ws.onmessage = (e) => onMessage(JSON.parse(e.data));
    return ws;
  }
}
```

