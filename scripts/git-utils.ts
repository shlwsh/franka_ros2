/**
 * Git 工具函数模块
 */

import { access } from 'fs/promises';
import { exec, execFile } from 'child_process';
import * as path from 'path';
import { promisify } from 'util';
import { getRepoRoot, isWslWindowsRuntime, toLinuxPath } from './repo-root';

const execAsync = promisify(exec);
const execFileAsync = promisify(execFile);

const WIN_GIT = '/mnt/c/Program Files/Git/cmd/git.exe';

/** mygit 自动提交时排除的路径前缀（含 colcon 构建产物） */
export const AUTO_COMMIT_EXCLUDE_PREFIXES = [
  'logs/',
  'log/',
  'build/',
  'install/',
] as const;

/** 不对其做完整 diff（避免 PDF/ZIP 等拖慢 mygit） */
export const BINARY_ARTIFACT_SUFFIXES = [
  '.pdf',
  '.zip',
  '.png',
  '.jpg',
  '.jpeg',
  '.gif',
  '.webp',
  '.svg',
  '.ico',
  '.bin',
  '.so',
  '.o',
  '.a',
  '.deb',
  '.exe',
  '.dll',
  '.mp4',
  '.wav',
  '.pt',
  '.onnx',
  '.pth',
  '.ckpt',
] as const;

export function isBinaryArtifact(filePath: string): boolean {
  const lower = filePath.replace(/\\/g, '/').toLowerCase();
  return BINARY_ARTIFACT_SUFFIXES.some((suffix) => lower.endsWith(suffix));
}

/** .env、.env.mygit、.env.example、.env.local 等环境配置文件（始终纳入提交） */
export function isEnvRelatedFile(filePath: string): boolean {
  const normalized = filePath.replace(/\\/g, '/');
  return /(^|\/)\.env(\.[^/]+)?$/.test(normalized);
}

export function isExcludedFromAutoCommit(filePath: string): boolean {
  if (isEnvRelatedFile(filePath)) return false;
  const normalized = filePath.replace(/\\/g, '/');
  return AUTO_COMMIT_EXCLUDE_PREFIXES.some((prefix) =>
    normalized.startsWith(prefix),
  );
}

/** 内网 Git 远程：推送时绕过本地 HTTP 代理 */
function isInternalGitRemote(url: string): boolean {
  return /\.winning\.com\.cn/i.test(url);
}

async function pathExists(filePath: string): Promise<boolean> {
  try {
    await access(filePath);
    return true;
  } catch {
    return false;
  }
}

/** Windows Git 推送时剥离 WSL 代理/SSL 变量，避免 TLS 失败 */
function cleanEnvForWindowsGit(): NodeJS.ProcessEnv {
  const cleaned: NodeJS.ProcessEnv = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (value === undefined) continue;
    if (['proxy', 'PROXY', 'SSL', 'CURL', 'GIT_SSL', 'GIT_HTTP'].some((p) => key.includes(p))) {
      continue;
    }
    cleaned[key] = value;
  }
  return cleaned;
}

function applyProxyEnv(env: NodeJS.ProcessEnv, proxyUrl: string): NodeJS.ProcessEnv {
  const out = { ...env };
  for (const key of [
    'http_proxy',
    'https_proxy',
    'HTTP_PROXY',
    'HTTPS_PROXY',
    'all_proxy',
    'ALL_PROXY',
  ]) {
    out[key] = proxyUrl;
  }
  return out;
}

async function execGitBinary(
  gitBin: string,
  args: string[],
  env: NodeJS.ProcessEnv = process.env,
  cwd: string = getRepoRoot(),
): Promise<string> {
  const repoRoot = toLinuxPath(cwd);
  try {
    if (isWslWindowsRuntime()) {
      const { stdout, stderr } = await execFileAsync(
        'wsl.exe',
        ['-e', 'git', '-C', repoRoot, ...args],
        { env, maxBuffer: 16 * 1024 * 1024 },
      );
      if (stderr && !stderr.includes('warning')) {
        console.warn('Git 警告:', stderr);
      }
      return stdout.trim();
    }

    const { stdout, stderr } = await execFileAsync(gitBin, args, {
      cwd: repoRoot,
      env,
      maxBuffer: 16 * 1024 * 1024,
    });
    if (stderr && !stderr.includes('warning')) {
      console.warn('Git 警告:', stderr);
    }
    return stdout.trim();
  } catch (error) {
    const err = error as { stderr?: string; message?: string };
    const detail = err.stderr?.trim() || err.message || String(error);
    throw new Error(`Git 命令执行失败: ${detail}`);
  }
}

async function branchHasUpstream(branch: string): Promise<boolean> {
  try {
    const merge = await execGit(`git config branch.${branch}.merge`);
    return Boolean(merge);
  } catch {
    return false;
  }
}

async function execGit(
  command: string,
  cwd: string = getRepoRoot(),
): Promise<string> {
  const repoRoot = toLinuxPath(cwd);
  try {
    if (isWslWindowsRuntime()) {
      const inner = `cd ${JSON.stringify(repoRoot)} && ${command}`;
      const { stdout, stderr } = await execAsync(
        `wsl.exe -e bash -lc ${JSON.stringify(inner)}`,
        { maxBuffer: 16 * 1024 * 1024 },
      );
      if (stderr && !stderr.includes('warning')) {
        console.warn('Git 警告:', stderr);
      }
      return stdout.trim();
    }

    const { stdout, stderr } = await execAsync(command, { cwd: repoRoot });
    if (stderr && !stderr.includes('warning')) {
      console.warn('Git 警告:', stderr);
    }
    return stdout.trim();
  } catch (error) {
    throw new Error(
      `Git 命令执行失败: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

export async function getGitStatus(): Promise<{
  modified: string[];
  added: string[];
  deleted: string[];
  untracked: string[];
  excluded: string[];
  hasChanges: boolean;
}> {
  const output = await execGit('git status --porcelain');

  const modified: string[] = [];
  const added: string[] = [];
  const deleted: string[] = [];
  const untracked: string[] = [];
  const excluded: string[] = [];

  if (!output) {
    return { modified, added, deleted, untracked, excluded, hasChanges: false };
  }

  const lines = output.split('\n');
  for (const line of lines) {
    if (!line) continue;

    const status = line.substring(0, 2);
    const file = line.slice(3).trim();

    if (isExcludedFromAutoCommit(file)) {
      excluded.push(file);
      continue;
    }

    if (status.includes('M')) {
      modified.push(file);
    } else if (status.includes('A')) {
      added.push(file);
    } else if (status.includes('D')) {
      deleted.push(file);
    } else if (status === '??') {
      untracked.push(file);
    }
  }

  const hasChanges =
    modified.length > 0 ||
    added.length > 0 ||
    deleted.length > 0 ||
    untracked.length > 0;

  return { modified, added, deleted, untracked, excluded, hasChanges };
}

export async function getGitDiff(files?: string[]): Promise<string> {
  try {
    await execGit('git rev-parse HEAD');
    let command = 'git diff --no-ext-diff HEAD';
    if (files && files.length > 0) {
      command += ' ' + files.join(' ');
    }

    try {
      return await execGit(command);
    } catch {
      console.warn('⚠️  完整 diff 获取失败，使用统计信息代替');
      return await execGit(command.replace('git diff', 'git diff --stat'));
    }
  } catch {
    let command = 'git diff --no-ext-diff --cached';
    if (files && files.length > 0) {
      command += ' ' + files.join(' ');
    }

    try {
      return await execGit(command);
    } catch {
      console.warn('⚠️  完整 diff 获取失败，使用统计信息代替');
      return await execGit(command.replace('git diff', 'git diff --stat'));
    }
  }
}

const MYGIT_DIFF_SEP = '---MYGIT_DIFF_SEP---';

/** 单次 shell 调用执行多条 git diff，减少 Windows bun 下多次 wsl.exe 开销 */
async function runBatchedGitDiff(commands: string[]): Promise<string> {
  if (commands.length === 0) return '';
  const repoRoot = toLinuxPath(getRepoRoot());
  const body = commands
    .map((cmd, i) =>
      i === 0 ? cmd : `echo ${JSON.stringify(MYGIT_DIFF_SEP)}; ${cmd}`,
    )
    .join('; ');
  const inner = `cd ${JSON.stringify(repoRoot)} && ${body}`;

  if (isWslWindowsRuntime()) {
    const { stdout } = await execAsync(
      `wsl.exe -e bash -lc ${JSON.stringify(inner)}`,
      { maxBuffer: 16 * 1024 * 1024 },
    );
    return stdout.trim();
  }

  const { stdout } = await execAsync(`bash -lc ${JSON.stringify(inner)}`, {
    cwd: repoRoot,
    maxBuffer: 16 * 1024 * 1024,
  });
  return stdout.trim();
}

export async function getStagedGitDiff(): Promise<string> {
  const namesOutput = await execGit('git diff --cached --name-only');
  const staged = namesOutput.split('\n').map((f) => f.trim()).filter(Boolean);
  if (staged.length === 0) return '';

  const textFiles = staged.filter((f) => !isBinaryArtifact(f));
  const binaryFiles = staged.filter((f) => isBinaryArtifact(f));

  if (textFiles.length === 0 && binaryFiles.length > 0) {
    return (
      '# 二进制/大文件（仅列出路径，不含 diff 内容）\n' +
      binaryFiles.map((f) => `- ${f}`).join('\n') +
      '\n\n' +
      (await execGit('git diff --no-ext-diff --cached --stat'))
    );
  }

  const parts: string[] = [];
  if (binaryFiles.length > 0) {
    parts.push(
      '# 二进制/大文件（仅列出路径，不含 diff 内容）\n' +
        binaryFiles.map((f) => `- ${f}`).join('\n'),
    );
  }

  const gitCommands: string[] = [];
  if (binaryFiles.length > 0) {
    gitCommands.push('git diff --no-ext-diff --cached --stat');
  }
  if (textFiles.length > 0) {
    const quoted = textFiles.map((f) => JSON.stringify(f)).join(' ');
    gitCommands.push(
      `git diff --no-ext-diff --cached -- ${quoted} 2>/dev/null || git diff --no-ext-diff --cached --stat -- ${quoted}`,
    );
  }

  if (gitCommands.length > 0) {
    const batched = await runBatchedGitDiff(gitCommands);
    const sections = batched
      .split(MYGIT_DIFF_SEP)
      .map((s) => s.trim())
      .filter(Boolean);
    parts.push(...sections);
  }

  return parts.join('\n\n');
}

async function stageEnvRelatedFiles(): Promise<void> {
  const output = await execGit('git status --porcelain');
  const envFiles: string[] = [];

  for (const line of output.split('\n')) {
    if (!line) continue;
    const file = line.slice(3).trim();
    if (isEnvRelatedFile(file)) envFiles.push(file);
  }

  if (envFiles.length === 0) return;

  const fileList = envFiles.map((f) => JSON.stringify(f)).join(' ');
  await execGit(`git add -f ${fileList}`);
}

export async function gitAdd(files: string[] = ['.']): Promise<void> {
  if (files.length === 1 && files[0] === '.') {
    await execGit('git add -A');
    for (const prefix of AUTO_COMMIT_EXCLUDE_PREFIXES) {
      try {
        await execGit(`git reset HEAD -- ${prefix}`);
      } catch {
        // 该前缀下无已暂存文件时可忽略
      }
    }
    await stageEnvRelatedFiles();
    return;
  }

  const toAdd = files.filter((f) => !isExcludedFromAutoCommit(f));
  if (toAdd.length === 0) return;

  const fileList = toAdd.map((f) => JSON.stringify(f)).join(' ');
  await execGit(`git add ${fileList}`);
}

export async function gitCommit(message: string): Promise<void> {
  const paragraphs = message
    .split(/\n\n/)
    .map((p) => p.trim())
    .filter(Boolean);

  if (paragraphs.length === 0) {
    throw new Error('提交信息为空');
  }

  const args = paragraphs.map((p) => `-m ${JSON.stringify(p)}`).join(' ');
  await execGit(`git commit ${args}`);
}

export async function gitPush(
  remote: string = 'origin',
  branch?: string,
): Promise<void> {
  if (!branch) {
    branch = await execGit('git rev-parse --abbrev-ref HEAD');
  }

  const remotes = await getRemoteInfo();
  const remoteUrl = remotes.find((r) => r.name === remote)?.url ?? '';
  const githubToken = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  const winGitExists = await pathExists(WIN_GIT);
  const gcmWrapper = path.join(getRepoRoot(), 'scripts/git-credential-gcm.sh');

  const configArgs: string[] = [];
  if (isInternalGitRemote(remoteUrl)) {
    configArgs.push('-c', 'http.proxy=', '-c', 'https.proxy=');
    console.log('ℹ️  内网远程仓库，推送时绕过本地 HTTP 代理');
  }

  let gitBin = 'git';
  let env: NodeJS.ProcessEnv = { ...process.env };

  if (githubToken) {
    if (winGitExists) gitBin = WIN_GIT;
    env.GIT_TERMINAL_PROMPT = '0';
    configArgs.push(
      '-c',
      `credential.helper=!f() { echo username=x-access-token; echo password=${githubToken}; }; f`,
    );
    const proxyUrl = process.env.MYGIT_HTTP_PROXY;
    if (!winGitExists && proxyUrl) {
      env = applyProxyEnv(env, proxyUrl);
    }
    console.log('🔐 使用 GITHUB_TOKEN 推送');
  } else if (winGitExists) {
    gitBin = WIN_GIT;
    env = cleanEnvForWindowsGit();
    env.GIT_TERMINAL_PROMPT = '0';
    console.log('🔐 使用 Windows Git 推送（复用 Windows 凭据，推荐 WSL 环境）');
  } else {
    env.GIT_TERMINAL_PROMPT = '0';
    configArgs.push('-c', 'http.version=HTTP/1.1');
    if (await pathExists(gcmWrapper)) {
      configArgs.push('-c', `credential.helper=!${gcmWrapper}`);
    }
    const proxyUrl = process.env.MYGIT_HTTP_PROXY;
    if (proxyUrl) {
      env = applyProxyEnv(env, proxyUrl);
    }
    console.log(
      '⚠️  未找到 Windows Git；若推送失败请安装 Git for Windows 或在 .env.mygit 配置 GITHUB_TOKEN',
    );
  }

  const hasUpstream = await branchHasUpstream(branch);
  const pushArgs = hasUpstream
    ? [...configArgs, 'push', remote, branch]
    : [...configArgs, 'push', '--set-upstream', remote, branch];

  await execGitBinary(gitBin, pushArgs, env);
}

export async function getRemoteInfo(): Promise<
  { name: string; url: string }[]
> {
  const output = await execGit('git remote -v');
  const remotes: { name: string; url: string }[] = [];

  const lines = output.split('\n');
  const seen = new Set<string>();

  for (const line of lines) {
    if (!line) continue;
    const parts = line.split(/\s+/);
    if (parts.length >= 2) {
      const key = `${parts[0]}-${parts[1]}`;
      if (!seen.has(key)) {
        seen.add(key);
        remotes.push({ name: parts[0], url: parts[1] });
      }
    }
  }

  return remotes;
}

export async function isGitRepository(): Promise<boolean> {
  try {
    await execGit('git rev-parse --git-dir');
    return true;
  } catch {
    return false;
  }
}

export async function hasUnpushedCommits(): Promise<boolean> {
  try {
    const output = await execGit('git cherry -v');
    return output.trim().length > 0;
  } catch {
    return false;
  }
}
