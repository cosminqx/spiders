#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy_to_zyte.sh
# Packages and deploys the Seek Digital spider suite to Zyte Cloud.
#
# Usage:
#   chmod +x deploy_to_zyte.sh
#   ./deploy_to_zyte.sh
#
# Prerequisites:
#   pip install shub           # Zyte's deployment CLI
#   shub login                 # authenticate once
#   Set PROJECT_ID below
# ─────────────────────────────────────────────────────────────────────────────

set -e

PROJECT_ID="859827"   # replace with your numeric project ID
SPIDER_VERSION=$(date +"%Y%m%d_%H%M")

echo "▶ Seek Digital Intelligence — deploying to Zyte Cloud"
echo "  Project: $PROJECT_ID"
echo "  Version: $SPIDER_VERSION"
echo ""

# Check shub is installed
if ! command -v shub &>/dev/null; then
    echo "✗ shub not found — run: pip install shub && shub login"
    exit 1
fi

# Deploy
echo "▶ Deploying..."
shub deploy $PROJECT_ID --version $SPIDER_VERSION

echo ""
echo "✓ Deployed successfully!"
echo ""
echo "Next steps:"
echo "  1. Open app.zyte.com → your project"
echo "  2. Set environment variable: ZYTE_API_KEY (under Settings → Env Variables)"
echo "  3. Schedule your spiders:"
echo ""
echo "  Spider              | Recommended schedule"
echo "  ─────────────────── | ────────────────────"
echo "  pagini_aurii        | Daily, 02:00 EET"
echo "  facebook_ads        | Every 3 days, 03:00 EET"
echo "  competitor_pricing  | Weekly, Sunday 04:00 EET"
echo "  website_audit       | After pagini_aurii (chain via webhook)"
echo ""
echo "  4. Run your first test: go to Spiders → pagini_aurii → Run"
echo "     Arguments: industry=restaurante city=iasi max_pages=3"
