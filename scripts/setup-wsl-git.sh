#!/bin/bash
# WSL2 环境下配置 Git：复用 Windows Git Credential Manager，并修复工作区权限。
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GCM_EXE="/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe"
GCM_WRAPPER="${HOME}/bin/git-credential-manager-wsl.sh"
GITCONFIG="${HOME}/.gitconfig"

echo "==> 检查 Windows Git Credential Manager"
if [[ ! -x "$GCM_EXE" ]]; then
    echo "错误: 未找到 $GCM_EXE"
    echo "请先在 Windows 上安装 Git for Windows（含 Git Credential Manager）。"
    exit 1
fi
"$GCM_EXE" --version

echo "==> 安装 WSL 凭证包装脚本"
mkdir -p "${HOME}/bin"
cat >"${GCM_WRAPPER}" <<'EOF'
#!/bin/bash
export GCM_INTERACTIVE="${GCM_INTERACTIVE:-never}"
exec "/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe" "$@"
EOF
chmod +x "${GCM_WRAPPER}"

echo "==> 写入 ${GITCONFIG}"
cat >"${GITCONFIG}" <<EOF
[user]
	name = ${USER}
	email = ${USER}@local

[credential]
	helper = ${GCM_WRAPPER}
	interactive = never

[credential "https://github.com"]
	provider = github

[init]
	defaultBranch = main

[fetch]
	prune = true

[safe]
	directory = ${REPO_DIR}
EOF

echo "==> 修复工作区目录权限（当前用户: ${USER})"
if [[ "$(id -u)" -eq 0 ]]; then
    TARGET_USER="${SUDO_USER:-ros}"
    chown -R "${TARGET_USER}:${TARGET_USER}" "${REPO_DIR}/.git" "${REPO_DIR}/.vscode" 2>/dev/null || true
    chown "${TARGET_USER}:${TARGET_USER}" "${GITCONFIG}"
    if [[ -d "/home/${TARGET_USER}" ]]; then
        chown "${TARGET_USER}:${TARGET_USER}" "/home/${TARGET_USER}"
    fi
else
    chown -R "${USER}:${USER}" "${REPO_DIR}/.git" "${REPO_DIR}/.vscode" 2>/dev/null || true
fi

echo "==> 验证 git fetch（使用 Windows 已保存的 GitHub 凭证）"
cd "${REPO_DIR}"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
export GIT_TERMINAL_PROMPT=0
export GCM_INTERACTIVE=never
if git fetch --prune origin; then
    echo "✅ git fetch 成功，远程分支已刷新"
    git branch -a
else
    echo "⚠️  git fetch 失败。请在 Windows 终端执行一次 git fetch 完成 GitHub 登录，"
    echo "   或在 WSL 中重新运行本脚本（GCM 会弹出 Windows 登录窗口）。"
    exit 1
fi

echo "✅ WSL Git 配置完成"
