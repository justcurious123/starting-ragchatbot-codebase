#!/bin/bash

echo "🚀 Running full quality pipeline..."
echo ""

echo "Step 1: Formatting code..."
./format.sh

echo ""
echo "Step 2: Running quality checks..."
./lint.sh

echo ""
echo "✨ Quality pipeline complete!"