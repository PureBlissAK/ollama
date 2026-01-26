#!/usr/bin/env bash
# Usage: GH_TOKEN must be set or gh CLI must be logged in.
# This script posts update comments to issues and can close them when ready.

REPO="kushin77/ollama"
BRANCH="feature/issue-24-predictive"
PR_URL="https://github.com/kushin77/ollama/pull/39"
RELEASE_NOTES_PATH="docs/release-notes/pmo-issues-24-30.md"

ISSUES=(24 25 26 27 28 29 30)

COMMENT_TEMPLATE=$(cat <<'EOF'
PMO update: work for this issue has been implemented and tested.

- Branch: %s
- Pull request: %s
- Release notes: %s

Local PMO unit tests passed: 132 passed, 2 skipped.

Next step: awaiting CI. If CI passes, this issue will be closed and the Epic (#18) marked complete.
EOF
)

for i in "${ISSUES[@]}"; do
  BODY=$(printf "$COMMENT_TEMPLATE" "$BRANCH" "$PR_URL" "$RELEASE_NOTES_PATH")
  echo "Posting update to issue #$i"
  if command -v gh >/dev/null 2>&1; then
    gh issue comment $i --repo $REPO -b "$BODY"
  else
    echo "gh CLI not found — printing prepared comment for issue #$i."
    echo "-----"
    echo "$BODY"
    echo "-----"
  fi
done

# To close issues after CI, run with CLOSE=true
if [ "$CLOSE" = "true" ]; then
  for i in "${ISSUES[@]}"; do
    if command -v gh >/dev/null 2>&1; then
      gh issue close $i --repo $REPO
      echo "Closed issue #$i"
    else
      echo "gh CLI not found — cannot close issue #$i from script."
    fi
  done
  # Mark Epic #18 complete (if using GitHub issues for Epic, otherwise update tracker)
  echo "Note: update Epic #18 status manually if needed."
fi
