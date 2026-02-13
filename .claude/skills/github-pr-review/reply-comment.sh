#!/bin/bash
# 回复 PR review comment
# 用法: ./reply-comment.sh <pr_number> <comment_id> <reply_body>

set -e

# 颜色
BLUE='\033[0;34m'
GREEN='\033[0;32m'
GRAY='\033[0;90m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

PR_NUMBER=$1
COMMENT_ID=$2
REPLY_BODY=$3

if [ -z "$PR_NUMBER" ] || [ -z "$COMMENT_ID" ] || [ -z "$REPLY_BODY" ]; then
    echo "用法: $0 <pr_number> <comment_id> <reply_body>"
    echo ""
    echo "示例:"
    echo "  $0 2 2762581291 \"感谢建议！这是示例代码...\""
    echo ""
    echo "注意: comment_id 是评论的数字ID，不是线程ID"
    echo "可以从 list-unresolved.sh 的输出中找到 comment_id"
    exit 1
fi

echo -e "${CYAN}回复 PR #${PR_NUMBER} 的评论 #${COMMENT_ID}${NC}"
echo ""

# 获取评论线程信息
OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO=$(gh repo view --json name --jq '.name')

# 先获取线程ID（comment所属的review thread）
THREAD_DATA=$(gh api graphql -f query="
query {
  repository(owner: \"${OWNER}\", name: \"${REPO}\") {
    pullRequest(number: ${PR_NUMBER}) {
      reviewThreads(first: 100) {
        nodes {
          id
          comments(first: 10) {
            nodes {
              databaseId
            }
          }
        }
      }
    }
  }
}
" --jq ".data.repository.pullRequest.reviewThreads.nodes[] | select(.comments.nodes[].databaseId == ${COMMENT_ID}) | .id")

if [ -z "$THREAD_DATA" ]; then
    echo -e "${RED}错误: 未找到评论 #${COMMENT_ID}${NC}"
    echo "请确认 comment_id 是否正确"
    exit 1
fi

echo -e "${GRAY}线程ID: ${THREAD_DATA}${NC}"
echo ""

# 构造 API 请求 - 使用专门的 replies 端点
API_URL="https://api.github.com/repos/${OWNER}/${REPO}/pulls/${PR_NUMBER}/comments/${COMMENT_ID}/replies"

echo -e "${BLUE}发送回复...${NC}"
echo ""

# 发送回复到 review thread（使用 -F 参数发送 form-data）
gh api "${API_URL}" \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  -F body="$REPLY_BODY" --silent

echo ""
echo -e "${GREEN}✓ 回复已发送${NC}"
echo ""
echo -e "${CYAN}查看: https://github.com/${OWNER}/${REPO}/pull/${PR_NUMBER}${NC}"
