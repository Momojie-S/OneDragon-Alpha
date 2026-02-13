#!/bin/bash
# 列出 PR 的未解决评论
# 用法: ./list-unresolved.sh <pr_number>

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# 颜色
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
GRAY='\033[0;90m'
NC='\033[0m'

PR_NUMBER=$1

if [ -z "$PR_NUMBER" ]; then
    echo "用法: $0 <pr_number>"
    exit 1
fi

echo -e "${BLUE}查询 PR #${PR_NUMBER} 的未解决评论...${NC}"
echo ""

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 获取仓库信息
OWNER=$(gh repo view --json owner --jq '.owner.login')
REPO=$(gh repo view --json name --jq '.name')

# 使用 GraphQL API 查询未解决的评论
gh api graphql -f query="
query {
  repository(owner: \"${OWNER}\", name: \"${REPO}\") {
    pullRequest(number: ${PR_NUMBER}) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          id
          comments(first: 1) {
            nodes {
              author { login }
              body
              path
              line
              url
            }
          }
        }
      }
    }
  }
}
" --jq '.data.repository.pullRequest.reviewThreads.nodes | map(select(.isResolved == false))'
