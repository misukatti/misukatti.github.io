#!/usr/bin/env bash
# Publish one version of Hammerite's docs: its API reference, generated as HTML by that version's own
# tools/make_api_docs.sh with this site's template, and its guides, rendered by
# import_hammerite_docs.py - all into hammerite/docs/<version>/. Then index_hammerite_docs.py lists
# the versions and points the old addresses at the current release, and relative_links.py makes the
# pages' links relative, so they work opened from disk too.
#
#   tools/import_hammerite_docs.sh latest [ref]         default ref: master
#   tools/import_hammerite_docs.sh 1.0 [ref]            default ref: v1.0.0
#
# HAMMERITE= names the checkout to read from (default ../hammerite). The pages come from the ref
# exported with git archive, not from the checkout's working tree. From 2.0 the reference is read
# partly from the native library, which git does not hold: a release takes it from its own
# hammerite-full zip on GitHub (HAMMERITE_REPO=, default misukatti/hammerite), latest from the
# checkout's build in hammerite-core/bin. A released version is read-only: once
# hammerite/docs/<version>/ exists it is never written again, unless FORCE=1. latest is rebuilt every
# time. Needs Godot (GODOT=), Python's markdown package (PYTHON=), and gh for a release from 2.0.
set -euo pipefail

SITE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:?usage: import_hammerite_docs.sh <latest|X.Y> [ref]}"
HAMMERITE="$(cd "${HAMMERITE:-$SITE/../hammerite}" && pwd)"
PYTHON="${PYTHON:-python3}"
OUT="$SITE/hammerite/docs/$VERSION"

if [[ "$VERSION" == latest ]]; then
	REF="${2:-master}"
elif [[ "$VERSION" =~ ^[0-9]+\.[0-9]+$ ]]; then
	REF="${2:-v$VERSION.0}"
	if [[ -e "$OUT" && "${FORCE:-0}" != 1 ]]; then
		echo "hammerite/docs/$VERSION/ is a released version and read-only (FORCE=1 to rebuild it)" >&2
		exit 1
	fi
else
	echo "import_hammerite_docs: '$VERSION' is neither latest nor a version like 1.0" >&2
	exit 2
fi

COMMIT="$(git -C "$HAMMERITE" rev-parse --short "$REF^{commit}")"
DATE="$(git -C "$HAMMERITE" log -1 --format=%cs "$COMMIT")"
SRC="$(mktemp -d)"
trap 'rm -rf "$SRC"' EXIT
git -C "$HAMMERITE" archive "$COMMIT" | tar -x -C "$SRC"

if grep -q -- "--gdextension-docs" "$SRC/tools/make_api_docs.sh"; then
	if [[ "$VERSION" == latest ]]; then
		cp -R "$HAMMERITE/hammerite-core/bin" "$SRC/hammerite-core/"
	else
		TAG="$(git -C "$HAMMERITE" describe --tags --exact-match "$COMMIT" 2>/dev/null || echo "v$VERSION.0")"
		gh release download "$TAG" -R "${HAMMERITE_REPO:-misukatti/hammerite}" -p 'hammerite-full-*.zip' -D "$SRC/package"
		unzip -q "$SRC"/package/*.zip 'addons/hammerite-core/bin/*' -d "$SRC/package"
		cp -R "$SRC/package/addons/hammerite-core/bin" "$SRC/hammerite-core/"
	fi
fi

sed -e "s|{version}|$VERSION|g" -e "s|{source}|$COMMIT, $DATE|g" "$SITE/tools/docs-template.html" >"$SRC/page.html"
rm -rf "$OUT"
mkdir -p "$OUT"
"$SRC/tools/make_api_docs.sh" --html "$OUT/api" --template "$SRC/page.html"
"$PYTHON" "$SITE/tools/import_hammerite_docs.py" "$SRC" "$VERSION" "$SRC/page.html"
"$PYTHON" "$SITE/tools/index_hammerite_docs.py"
python3 "$SITE/tools/relative_links.py" "$SITE/hammerite/docs" "$SITE/hammerite/api"
echo "hammerite/docs/$VERSION/ from Hammerite $REF ($COMMIT, $DATE)"
