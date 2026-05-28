#!/bin/bash
# One-time setup for tutuadetunmbi-com.
# Run me from Terminal:   bash ~/Desktop/tutuadetunmbi-com/setup.sh
set -e

PROJECT_DIR="$HOME/Desktop/tutuadetunmbi-com"
cd "$PROJECT_DIR"

echo ""
echo "================================================"
echo "  tutuadetunmbi.com — one-time setup"
echo "================================================"
echo ""

# --- 1. Clean any partial git stub left by the sandbox ---
if [ -d .git ]; then
  echo "→ Removing partial .git folder from previous session..."
  rm -rf .git
fi

# --- 2. Install Node deps ---
if [ ! -d node_modules ]; then
  echo "→ Installing dependencies (this takes ~1 minute)..."
  npm install --no-audit --no-fund
else
  echo "→ Dependencies already installed."
fi

# --- 3. Build the site to verify everything compiles ---
echo ""
echo "→ Building the site..."
npm run build

# --- 4. Initialize git and make first commit ---
echo ""
echo "→ Initializing git repository..."
git init -b main
git config user.email "info@tutuadetunmbi.com"
git config user.name "Tutu Adetunmbi"
git add .
git commit -m "Initial commit: Astro site with 73 migrated Substack memos" --quiet

echo ""
echo "================================================"
echo "  ✓ Local repo ready. Site built to dist/"
echo "================================================"
echo ""
echo "NEXT STEPS"
echo ""
echo "OPTION A — fastest: deploy the dist/ folder to Netlify right now"
echo "    1. Open https://app.netlify.com/drop"
echo "    2. Drag the 'dist' folder (inside ~/Desktop/tutuadetunmbi-com/)"
echo "       into the drop zone."
echo "    3. Site goes live in ~30 seconds."
echo ""
echo "OPTION B — proper auto-deploy on every memo: push to GitHub"
echo "    1. Sign in at https://github.com"
echo "    2. Create a new repo: https://github.com/new"
echo "       Name: tutuadetunmbi-com   Public   (don't tick any init options)"
echo "    3. After it's created, GitHub will show 'push existing repository'"
echo "       commands — copy/paste them into Terminal."
echo "    4. Once pushed, connect Netlify to the repo:"
echo "       https://app.netlify.com/start"
echo "       Pick 'Deploy from GitHub' → pick tutuadetunmbi-com → Deploy."
echo "       Netlify auto-detects Astro and builds it."
echo ""
echo "After either option works, point tutuadetunmbi.com DNS at the new Netlify site."
echo ""
