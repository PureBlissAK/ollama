#!/bin/bash
# Git setup script to enforce Elite Standards
# Run this once to configure git for the project

set -e

echo "🚀 Setting up Git for Elite Standards Compliance..."
echo ""

cd "$(dirname "$0")" || exit 1

# Configure hooks path
echo "📍 Configuring hooks path..."
git config core.hooksPath .husky
echo "✅ Hooks path configured: .husky"
echo ""

# Ensure hooks are executable
echo "🔐 Making hooks executable..."
chmod +x .husky/pre-commit
chmod +x .husky/commit-msg
chmod +x .husky/push
echo "✅ Hooks are executable"
echo ""

# Configure signing
echo "🔑 Configuring commit signing..."
git config commit.gpgsign true
git config user.signingkey || echo "⚠️  No GPG key configured. Set one with: git config user.signingkey <KEY>"
echo "✅ GPG signing configured"
echo ""

# Configure commit message template
if [ -f .gitmessage ]; then
    echo "📝 Setting commit message template..."
    git config commit.template .gitmessage
    echo "✅ Commit template configured"
    echo ""
fi

# Show current configuration
echo "📋 Current Git Configuration:"
echo "  core.hooksPath: $(git config core.hooksPath)"
echo "  commit.gpgsign: $(git config commit.gpgsign)"
echo "  user.email: $(git config user.email)"
echo "  user.name: $(git config user.name)"
echo ""

echo "✅ Git setup complete!"
echo ""
echo "📚 Elite Standards Summary:"
echo "  - Commit Format: type(scope): description"
echo "  - Valid Types: feat, fix, refactor, perf, test, docs, infra, security"
echo "  - All commits must be GPG signed: git commit -S"
echo "  - Push frequency: Every 4 hours max"
echo "  - Commit frequency: Every 30 minutes min"
echo "  - All tests must pass before push"
echo ""
echo "🔗 For more information, see .github/copilot-instructions.md"
echo ""
