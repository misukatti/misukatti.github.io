#!/usr/bin/env bash
# Bring Hammerite's docs onto the site: the API reference, generated as HTML by Hammerite's own
# tools/make_api_docs.sh with this site's template into hammerite/api/, then the guides, rendered by
# import_hammerite_docs.py into hammerite/docs/. Run it again whenever Hammerite's docs change, and
# commit what changes.
#
#   tools/import_hammerite_docs.sh [hammerite checkout]     default ../hammerite
#
# Needs Godot (GODOT= to point at it, as make_api_docs.sh reads) and Python's markdown package.
# make_api_docs.sh also rewrites the checkout's own docs/api/ from its source: on an up-to-date
# checkout that changes nothing.
set -euo pipefail

SITE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HAMMERITE="$(cd "${1:-$SITE/../hammerite}" && pwd)"
PYTHON="${PYTHON:-python3}"

"$HAMMERITE/tools/make_api_docs.sh" --html "$SITE/hammerite/api" --template "$SITE/tools/docs-template.html"
"$PYTHON" "$SITE/tools/import_hammerite_docs.py" "$HAMMERITE"
echo "from Hammerite $(git -C "$HAMMERITE" log -1 --format='%h %cs')"
