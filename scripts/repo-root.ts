/**
 * 解析仓库根目录。Windows 版 bun 在 WSL 下会把 cwd 变成 UNC 路径，
 * 导致子进程里的 git 回退到 C:\Windows\System32 并误判“非 Git 仓库”。
 */

import * as path from 'path';
import { fileURLToPath } from 'url';

let cachedRepoRoot: string | null = null;

/** Windows bun 通过 WSL 访问 Linux 工作区 */
export function isWslWindowsRuntime(): boolean {
  if (process.platform !== 'win32') return false;
  const cwd = process.cwd().replace(/\\/g, '/');
  return /wsl\.localhost|wsl\$/i.test(cwd);
}

/** 将 \\wsl.localhost\Distro\home\... 转为 /home/... */
export function toLinuxPath(inputPath: string): string {
  const normalized = inputPath.replace(/\\/g, '/');
  const wslMatch = normalized.match(/^\/\/wsl(?:\.localhost|\$)\/[^/]+\/(.*)$/i);
  if (wslMatch) {
    return `/${wslMatch[1]}`;
  }
  return inputPath;
}

function repoRootFromScriptLocation(): string {
  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  return path.resolve(scriptDir, '..');
}

/** 供 git / dotenv / 日志使用的 Linux 风格仓库根路径 */
export function getRepoRoot(): string {
  if (cachedRepoRoot) return cachedRepoRoot;

  const fromCwd = toLinuxPath(process.cwd());
  if (fromCwd.startsWith('/')) {
    cachedRepoRoot = fromCwd;
    return cachedRepoRoot;
  }

  cachedRepoRoot = toLinuxPath(repoRootFromScriptLocation());
  return cachedRepoRoot;
}
