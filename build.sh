#!/bin/bash
# Build script for the AusCheckt Is static site (used locally and by CI)

set -e

echo "🔍 Validating data..."
python3 validate_data.py

echo "🏗️  Building static site..."
python3 build_static_site.py

echo "✅ Build complete!"
echo "📂 Static site generated in: ./generated/"
echo ""
echo "🌐 To serve locally:"
echo "   cd generated && python3 -m http.server 8000"
