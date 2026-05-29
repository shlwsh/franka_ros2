#!/usr/bin/env bash
# WSL 下优先使用 Linux 版 bun，避免 Windows npm 全局 bun 的 UNC 路径问题
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -x "${HOME}/.bun/bin/bun" ]]; then
  exec "${HOME}/.bun/bin/bun" run scripts/git-auto-commit.ts "$@"
fi

if command -v bun >/dev/null 2>&1; then
  exec bun run scripts/git-auto-commit.ts "$@"
fi

echo "❌ 未找到 bun。请安装: curl -fsSL https://bun.sh/install | bash" >&2
exit 1
