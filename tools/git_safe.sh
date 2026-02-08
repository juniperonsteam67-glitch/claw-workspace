#!/bin/bash
# Error-resilient wrapper for git operations
# Usage: ./git_safe.sh [commit message]

set -e

cd /config/clawd

echo "🦅 Safe Git Wrapper"
echo "=================="

# Check if there are changes
if git diff --quiet && git diff --cached --quiet; then
    echo "✓ No changes to commit"
    exit 0
fi

# Add all changes
echo "→ Adding changes..."
git add -A

# Commit with message (or default)
MSG="${1:-Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')}"
echo "→ Committing: $MSG"
git commit -m "$MSG" || echo "⚠️  Commit may have failed, continuing..."

# Push with retry
echo "→ Pushing to origin..."
for i in 1 2 3; do
    if git push; then
        echo "✓ Push successful"
        exit 0
    else
        echo "⚠️  Push failed (attempt $i/3), retrying in 5s..."
        sleep 5
    fi
done

echo "❌ Push failed after 3 attempts"
exit 1
