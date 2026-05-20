# mygit 在 WSL2 下的配置说明

`./scripts/mygit.sh` 用于自动完成 `git add` → AI 生成提交信息 → `commit` → `push`。

## 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| `package 'ros_gz_sim' not found` | 与 mygit 无关，见 Gazebo 文档 | 安装 `ros-jazzy-ros-gz-sim` |
| AI `Connection reset` | DashScope 直连超时，需走本地代理 | 在 `.env.mygit` 设置 `MYGIT_HTTP_PROXY=http://127.0.0.1:7897` |
| `gnutls_handshake() failed` | WSL Git 经错误代理访问 GitHub | 脚本已改为用 **Windows Git** 推送 |
| `could not read Username` | WSL Git 无凭据 | 安装 Windows Git，或配置 `GITHUB_TOKEN` |

## 推荐配置（WSL2 + Windows 代理）

1. 编辑项目根目录的 `.env.mygit`（已纳入 Git 跟踪，团队共享配置）：

```bash
# 若本地尚无该文件，可从模板复制：
cp .agent/skills/mygit/resources/env.mygit.template .env.mygit
# 填入 DASHSCOPE_API_KEY，按需修改 MYGIT_HTTP_PROXY 端口
```

2. 确保 Windows 已安装 [Git for Windows](https://git.github.io/for-windows/)（含 Git Credential Manager），并在 Windows 侧完成过一次 GitHub 登录。

3. 运行环境检查：

```bash
bash .agent/skills/mygit/scripts/setup-check.sh
```

4. 提交推送：

```bash
./scripts/mygit.sh
```

## 工作原理

- **AI 请求**：优先通过 `MYGIT_HTTP_PROXY`（默认探测 `127.0.0.1:7897`）访问 DashScope。
- **Git 推送**：优先调用 `/mnt/c/Program Files/Git/cmd/git.exe`，复用 Windows 凭据与网络，**不**向 WSL Git 注入易出错的 `127.0.0.1:7890` 代理。
- **备选**：在 `.env.mygit` 中设置 `GITHUB_TOKEN`，可在无 Windows Git 时由 WSL Git 非交互推送。

## 是否需要与 Windows 共享 Git 权限？

**不需要额外配置 WSL 文件权限。** 脚本通过调用 Windows 自带的 `git.exe` 使用已在 Windows 登录的 GitHub 凭据，无需在 WSL 内重复 `git config --global` 或共享 SSH 密钥目录。

若希望完全在 WSL 内推送，可添加 `GITHUB_TOKEN`（需 `repo` 权限的 PAT）。
