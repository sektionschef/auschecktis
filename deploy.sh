#!/bin/bash
# Manual deployment script for GitHub Pages

set -e

echo "🚀 Manual GitHub Pages Deployment"

# Build the site
echo "🏗️  Building site..."
./build.sh

# Create temporary directory for gh-pages
TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: $TEMP_DIR"

# Copy generated files to temp directory
cp -r generated/* "$TEMP_DIR/"

# Switch to gh-pages branch (create if doesn't exist)
if git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "📋 Switching to existing gh-pages branch..."
    git checkout gh-pages
else
    echo "🆕 Creating new gh-pages branch..."
    git checkout --orphan gh-pages
    git rm -rf .
fi

# Copy built files to root
cp -r "$TEMP_DIR"/* .

# Add and commit
git add .
git commit -m "Deploy site - $(date)"

# Push to GitHub
git push origin gh-pages

# Return to main branch
git checkout main

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ Deployment complete!"
echo "🌐 Site should be available at: https://sektionschef.github.io/auschecktis"
echo "🌐 Custom domain: https://auschecktis.at (after DNS propagation)"