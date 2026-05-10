#!/bin/bash

# 设置出错即退出
set -e

echo "🚀 AI Git 提交工具启动"

# 1. 验证 Git 仓库
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "❌ 错误: 当前目录不是一个有效的 Git 仓库"
    exit 1
fi

# 检查依赖
if ! command -v jq >/dev/null; then
    echo "⚠️ 警告: 未找到 jq 命令。AI 生成功能将不可用，将使用托底提交。"
    HAS_JQ=false
else
    HAS_JQ=true
fi

if ! command -v curl >/dev/null; then
    echo "❌ 错误: 未找到 curl 命令，请先安装 curl。"
    exit 1
fi

# 2. 加载配置
ENV_FILE=".env.mygit"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 错误: 找不到配置文件 $ENV_FILE"
    echo "请在项目根目录创建该文件，并包含 DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DASHSCOPE_MODEL"
    exit 1
fi

# 读取配置（解析 .env 文件并去掉注释、空格和引号）
while IFS='=' read -r key value; do
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    if [[ ! "$key" =~ ^# ]] && [ -n "$key" ]; then
        value=$(echo "$value" | tr -d '\r' | sed 's/^"//' | sed 's/"$//' | sed "s/^'//" | sed "s/'$//")
        export "$key=$value"
    fi
done < "$ENV_FILE"

if [ -z "$DASHSCOPE_API_KEY" ] || [ -z "$DASHSCOPE_BASE_URL" ] || [ -z "$DASHSCOPE_MODEL" ]; then
    echo "❌ 错误: 配置文件 $ENV_FILE 中缺少必填项 (DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, DASHSCOPE_MODEL)"
    exit 1
fi

# 移除 URL 末尾可能的斜杠
DASHSCOPE_BASE_URL=${DASHSCOPE_BASE_URL%/}

# 3. 检测变更
echo "📝 正在检查代码变更..."
CHANGES=$(git status --porcelain)

if [ -z "$CHANGES" ]; then
    echo "✅ 没有检测到代码变更"
    exit 0
fi

# 统计变更文件数量
CHANGE_COUNT=$(echo "$CHANGES" | wc -l)
echo "发现 $CHANGE_COUNT 个文件变更："
echo "$CHANGES" | while read -r line; do
    status=$(echo "$line" | awk '{print $1}')
    file=$(echo "$line" | awk '{print $2}')
    case "$status" in
        M|AM|MM) echo "  修改: $file" ;;
        A) echo "  新增: $file" ;;
        D|AD) echo "  删除: $file" ;;
        ??) echo "  未跟踪: $file" ;;
        *) echo "  其他: $file" ;;
    esac
done

# 4. 版本文件检测
if echo "$CHANGES" | grep -E "package\.json|src-tauri/tauri\.conf\.json|src-tauri/Cargo\.toml" > /dev/null; then
    echo "⚠️ 检测到版本相关文件变更，建议使用相关的版本发布命令"
    # 按要求这里提示并退出
    echo "⚠️ 请使用 \`bun run release:tag\` 或对应的工作流进行版本发布"
    exit 1
fi

# 5. 生成提交信息
echo "🤖 正在使用 AI 生成提交信息..."

AI_SUCCESS=false
COMMIT_MSG=""

if [ "$HAS_JQ" = true ]; then
    # 先把所有内容加进暂存区，以便我们能得到完整的 diff 作为 AI 的输入
    git add .
    DIFF_CONTENT=$(git diff --cached)
    if [ ${#DIFF_CONTENT} -gt 10000 ]; then
        DIFF_CONTENT="${DIFF_CONTENT:0:10000}... (Diff truncated)"
    fi

    # 构造 JSON (按 OpenAI 兼容 API 格式构建)
    JSON_PAYLOAD=$(jq -n \
      --arg model "$DASHSCOPE_MODEL" \
      --arg sys_prompt "你是一个专业的 Git 提交信息生成助手。请根据代码变更生成简洁、清晰的中文提交信息。规范要求：第一行为简短标题（不超过50字符），必须使用 Conventional Commits 前缀（feat, fix, docs, style, refactor, test, chore等），不要带多余的引号和额外解释。" \
      --arg user_prompt "变更摘要:\n$CHANGES\n\n变更详情:\n$DIFF_CONTENT" \
      '{
        model: $model,
        messages: [
          {role: "system", content: $sys_prompt},
          {role: "user", content: $user_prompt}
        ],
        max_tokens: 300,
        temperature: 0.7
      }')

    # 临时取消出错退出，处理请求失败
    set +e
    HTTP_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$DASHSCOPE_BASE_URL/chat/completions" \
      -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
      -H "Content-Type: application/json" \
      -d "$JSON_PAYLOAD")
    CURL_STATUS=$?
    set -e
    
    # 分离出 http code 和 body
    HTTP_BODY="${HTTP_RESPONSE:0:${#HTTP_RESPONSE}-3}"
    HTTP_CODE="${HTTP_RESPONSE:${#HTTP_RESPONSE}-3}"

    if [ $CURL_STATUS -eq 0 ] && [ "$HTTP_CODE" = "200" ]; then
        COMMIT_MSG=$(echo "$HTTP_BODY" | jq -r '.choices[0].message.content')
        if [ "$COMMIT_MSG" != "null" ] && [ -n "$COMMIT_MSG" ]; then
            AI_SUCCESS=true
            # 移除可能的 markdown 代码块标记和多余空行
            COMMIT_MSG=$(echo "$COMMIT_MSG" | sed 's/^```[a-zA-Z]*$//' | sed 's/^```//' | sed 's/```$//')
            COMMIT_MSG=$(echo "$COMMIT_MSG" | awk 'NF{p=1} p' | awk '{a[NR]=$0} END{while(a[NR]=="")NR--; for(i=1;i<=NR;i++)print a[i]}')
        fi
    else
        echo "⚠️ API 请求失败，HTTP 状态码: $HTTP_CODE"
    fi
fi

# 6. 托底逻辑
if [ "$AI_SUCCESS" = false ]; then
    echo "⚠️ AI 生成提交信息失败，正在使用托底逻辑生成简介..."
    TODAY=$(date +"%Y-%m-%d")
    MODIFIED=$(echo "$CHANGES" | grep -E "^(M| M|A| A)" | wc -l)
    ADDED=$(echo "$CHANGES" | grep -E "^\?\?" | wc -l)
    DELETED=$(echo "$CHANGES" | grep -E "^(D| D)" | wc -l)
    
    COMMIT_MSG="chore: 自动同步代码变更 ($TODAY)

变更摘要：
- 修改 $MODIFIED 个文件
- 新增 $ADDED 个文件
- 删除 $DELETED 个文件

由于 AI 生成失败，此信息由系统自动生成。"

    # 确保加入暂存区（防没有 jq 的情况走到这里）
    git add .
fi

echo ""
echo "提交信息："
echo "──────────────────────────────────────────────────"
echo "$COMMIT_MSG"
echo "──────────────────────────────────────────────────"

# 8. 提交（跳过 husky 检查等）
echo "💾 正在创建提交..."
git commit -m "$COMMIT_MSG" --no-verify

# 9. 推送
echo "🚀 正在推送到远程仓库..."

# 取消可能存在的代理环境变量，防止在 WSL 等环境中 127.0.0.1 不可用导致 push 失败
# （如果用户使用了 TUN 模式或系统透明代理，直连反而能正常走代理）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

# 获取当前分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
# 获取当前分支对应的远程
REMOTE=$(git config "branch.$CURRENT_BRANCH.remote" || echo "origin")
# 检测是否已有 upstream 配置
MERGE=$(git config "branch.$CURRENT_BRANCH.merge" || echo "")

if [ -z "$MERGE" ]; then
    echo "📡 远程仓库: $REMOTE, 分支: $CURRENT_BRANCH (首次推送)"
    git push --set-upstream "$REMOTE" "$CURRENT_BRANCH" --no-verify
else
    echo "📡 远程仓库: $REMOTE, 分支: $CURRENT_BRANCH"
    git push --no-verify
fi

echo "✨ 提交并推送成功！"
