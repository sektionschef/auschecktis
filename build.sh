#!/bin/bash
# Automated build script for Auscheckt Is static site
# Run this script to update the site with latest data

set -e

echo "🚀 Starting automated build process..."

# Step 1: Update heurigen data (if needed)
echo "📊 Updating heurigen data..."
if [ -f "check_heurigen_updates.py" ]; then
    python3 check_heurigen_updates.py
fi

# Step 2: Build static site
echo "🏗️  Building static site..."
python3 build_static_site.py

# Step 3: Copy static assets
echo "📁 Copying static assets..."
cp -r assets generated/ 2>/dev/null || true
cp custom.css generated/
cp *.png generated/ 2>/dev/null || true
cp *.ico generated/ 2>/dev/null || true
cp *.svg generated/ 2>/dev/null || true
cp *.webmanifest generated/ 2>/dev/null || true
cp robots.txt generated/ 2>/dev/null || true
cp CNAME generated/ 2>/dev/null || true

echo "✅ Build complete!"
echo "📂 Static site generated in: ./generated/"
echo ""
echo "🌐 To serve locally:"
echo "   cd generated && python3 -m http.server 8000"
echo ""
echo "📤 To deploy:"
echo "   rsync -av generated/ your-server:/var/www/html/"