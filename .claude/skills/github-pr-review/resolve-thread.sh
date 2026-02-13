#!/bin/bash
# 关闭 PR review thread
# 用法: ./resolve-thread.sh <pr_number> <comment_id>

set -e

# 颜色
BLUE='\033[0;34m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

PR_NUMBER=$1
COMMENT_ID=$2

if [ -z "$PR_NUMBER" ] || [ -z "$COMMENT_ID" ]; then
    echo "用法: $0 <pr_number> <comment_id>"
    echo ""
    echo "示例:"
    echo "  $0 2 2786061437"
    echo ""
    echo "注意: comment_id 是评论的数字ID（如 2786061437），不是线程ID（如 PRRT_kwDOP1X2Vs5tpqvt）"
    echo "可以从 list-unresolved.sh 的输出或 gh api 查询结果中找到 comment_id"
    exit 1
fi

echo -e "${CYAN}关闭 PR #${PR_NUMBER} 的评论线程 #${COMMENT_ID}${NC}"
echo ""

# 获取评论线程信息
OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO=$(gh repo view --json name --jq '.name')

# 获取线程ID（comment所属的review thread）
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

echo -e "线程ID: ${THREAD_DATA}"
echo ""

# Resolve the review thread
echo -e "${BLUE}正在关闭评论线程...${NC}"

gh api graphql -f query="mutation { resolveReviewThread(input: {threadId: \"${THREAD_DATA}\"}) { thread { isResolved } } }" --silent

echo -e "${GREEN}✓ 评论线程已关闭${NC}"
echo ""
echo -e "${CYAN}查看: https://github.com/${OWNER}/${REPO}/pull/${PR_NUMBER}${NC}"
