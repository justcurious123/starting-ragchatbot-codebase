#!/bin/bash

echo "🔍 Running code quality checks..."
echo ""

echo "📋 Checking code style with flake8..."
uv run flake8 backend/ main.py || echo "⚠️  flake8 found some style issues"

echo ""
echo "📝 Checking import order with isort (dry-run)..."
uv run isort . --check-only --diff || echo "⚠️  isort found import ordering issues"

echo ""
echo "🖤 Checking code format with black (dry-run)..."
uv run black . --check --diff || echo "⚠️  black found formatting issues"

echo ""
echo "✅ Code quality checks complete!"