#!/usr/bin/env python3
"""List the published versions of Hammerite's docs and point the version-less addresses at one.

    tools/index_hammerite_docs.py

import_hammerite_docs.sh runs this after each import. It reads which versions hammerite/docs/ holds
and writes:

- hammerite/docs/versions.json, which every page's version switcher reads: the newest release first
  and marked stable, older releases after it, latest last;
- hammerite/docs/index.html, a redirect to the stable version's docs;
- a redirect for every page at its address from before the docs had versions - hammerite/docs/<page>
  and hammerite/api/<page> - to the same page in the stable version, so links made then still land.

Only the redirects and the list are written: a version's own pages are never touched.
"""

import html
import json
import re
import shutil
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
DOCS = SITE / "hammerite" / "docs"
OLD_API = SITE / "hammerite" / "api"
OWN = {"docs.css", "versions.js", "versions.json", "index.html"}


def redirect(to: str) -> str:
	target = html.escape(to)
	return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Hammerite 3D docs</title>
<link rel="canonical" href="{target}">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace({json.dumps(to)} + location.hash)</script>
</head>
<body><p>Moved to <a href="{target}">{target}</a>.</p></body>
</html>
"""


def main() -> int:
	released = sorted((d.name for d in DOCS.iterdir() if d.is_dir() and re.fullmatch(r"\d+\.\d+", d.name)),
		key=lambda v: tuple(int(n) for n in v.split(".")), reverse=True)
	has_latest = (DOCS / "latest").is_dir()
	versions = [{"id": v, "label": f"{v} (current)" if i == 0 else v, "stable": i == 0}
		for i, v in enumerate(released)]
	if has_latest:
		versions.append({"id": "latest", "label": "latest (unreleased)", "stable": not released})
	if not versions:
		print("index_hammerite_docs: no versions in hammerite/docs/")
		return 1
	stable = next(v["id"] for v in versions if v["stable"])
	(DOCS / "versions.json").write_text(json.dumps(versions, indent="\t") + "\n")

	keep = {v["id"] for v in versions}
	for old in DOCS.iterdir():
		if old.name in keep or old.name in OWN:
			continue
		shutil.rmtree(old) if old.is_dir() else old.unlink()
	if OLD_API.exists():
		shutil.rmtree(OLD_API)

	(DOCS / "index.html").write_text(redirect(f"/hammerite/docs/{stable}/"))
	count = 0
	for page in sorted((DOCS / stable).rglob("*.html")):
		relative = page.relative_to(DOCS / stable).as_posix()
		if relative == "index.html":
			continue
		old = OLD_API / relative.removeprefix("api/") if relative.startswith("api/") else DOCS / relative
		old.parent.mkdir(parents=True, exist_ok=True)
		old.write_text(redirect(f"/hammerite/docs/{stable}/{relative}"))
		count += 1
	print(f"index_hammerite_docs: {', '.join(v['id'] for v in versions)}; {count} old addresses go to {stable}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
