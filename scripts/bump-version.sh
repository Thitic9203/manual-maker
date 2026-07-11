#!/usr/bin/env bash
# Bump the manual-maker version in every place it lives, in one shot.
#
# Version currently lives in 4 spots that must stay in sync:
#   .claude-plugin/plugin.json      "version"
#   .claude-plugin/marketplace.json "metadata.version" AND "plugins[0].version"
#   README.md                       shields badge + the "**Version X ...**" line
# A mismatch ships a broken marketplace entry, so never hand-edit these — run this.
#
# Usage:
#   scripts/bump-version.sh 0.3.0     # explicit version
#   scripts/bump-version.sh patch     # 0.2.0 -> 0.2.1
#   scripts/bump-version.sh minor     # 0.2.0 -> 0.3.0
#   scripts/bump-version.sh major     # 0.2.0 -> 1.0.0
set -euo pipefail

cd "$(dirname "$0")/.."  # repo root

PLUGIN_JSON=".claude-plugin/plugin.json"
MARKET_JSON=".claude-plugin/marketplace.json"
README="README.md"
CHANGELOG="CHANGELOG.md"

cur="$(grep -m1 '"version"' "$PLUGIN_JSON" | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"
[ -n "$cur" ] || { echo "error: cannot read current version from $PLUGIN_JSON" >&2; exit 1; }

arg="${1:-}"
[ -n "$arg" ] || { echo "usage: $0 <new-version|major|minor|patch>" >&2; exit 1; }

IFS=. read -r MA MI PA <<<"$cur"
case "$arg" in
  major) new="$((MA + 1)).0.0" ;;
  minor) new="${MA}.$((MI + 1)).0" ;;
  patch) new="${MA}.${MI}.$((PA + 1))" ;;
  [0-9]*.[0-9]*.[0-9]*) new="$arg" ;;
  *) echo "error: '$arg' is not a version or major|minor|patch" >&2; exit 1 ;;
esac

[ "$new" != "$cur" ] || { echo "already at $cur, nothing to do" >&2; exit 1; }
echo "Bumping $cur -> $new"

# BSD sed (macOS) in-place edits. Anchored so only version fields change.
sed -i '' -E "s/(\"version\"[[:space:]]*:[[:space:]]*\")${cur}(\")/\1${new}\2/g" "$PLUGIN_JSON" "$MARKET_JSON"
sed -i '' -E "s|badge/version-[0-9][0-9A-Za-z._-]*-|badge/version-${new}-|g" "$README"
sed -i '' -E "s/(\*\*Version )${cur}( )/\1${new}\2/g" "$README"

# Prepend a dated CHANGELOG stub if this version isn't recorded yet.
if [ -f "$CHANGELOG" ] && ! grep -q "\[${new}\]" "$CHANGELOG"; then
  tmp="$(mktemp)"
  {
    head -n 3 "$CHANGELOG"
    printf '\n## [%s] - %s\n### Changed\n- _describe changes_\n' "$new" "$(date +%F)"
    tail -n +4 "$CHANGELOG"
  } >"$tmp" && mv "$tmp" "$CHANGELOG"
fi

echo "Updated: $PLUGIN_JSON, $MARKET_JSON, $README, $CHANGELOG"
echo "Next: edit the CHANGELOG stub, then commit + push. Team updates with:"
echo "  /plugin marketplace update manual-maker-dev"
