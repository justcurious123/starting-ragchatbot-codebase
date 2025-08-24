#!/bin/bash

echo "🔧 Running code formatting..."
echo ""

echo "📝 Sorting imports with isort..."
uv run isort .

echo "🖤 Formatting code with black..."
uv run black .

echo ""
echo "✅ Code formatting complete!"