#!/usr/bin/env python3
"""Render one version's guides into hammerite/docs/<version>/ beside its API reference.

    tools/import_hammerite_docs.py <hammerite source> <version> <page template>

tools/import_hammerite_docs.sh runs this after the API reference, with the template it filled in
for the version. Pages come from the source's
docs/: the top-level guides (installing, getting started, baking...) and docs/guides/. A link to
another of these pages or to the API reference becomes a link to its HTML page; a link to anything
else in the repository - a README, the manual, a script - is left as plain text, since the
repository is not public.
"""

import html
import posixpath
import re
import sys
from pathlib import Path

import markdown

SITE = Path(__file__).resolve().parent.parent

TOP = [
	("Get started", ["install", "getting-started"]),
	("Going further", ["baking", "performance", "troubleshooting", "api-stability"]),
]


def title_of(text: str) -> str:
	match = re.search(r"^# (.+)$", text, re.MULTILINE)
	return match.group(1).strip() if match else "Untitled"


def guides_table(index_text: str) -> list:
	"""[(title, page stem, summary)] from the table in docs/guides/index.md, in its order."""
	rows = []
	for match in re.finditer(r"^\| \[([^\]]+)\]\(([\w-]+)\.md\) \| (.+?) \|$", index_text, re.MULTILINE):
		rows.append((match.group(1), match.group(2), match.group(3)))
	return rows


def render(text: str) -> str:
	return markdown.markdown(text, extensions=["tables", "fenced_code", "toc", "sane_lists"],
		extension_configs={"toc": {"permalink": False}})


def relink(content: str, source: str, pages: dict, api: set, base: str) -> str:
	"""Point links at the published pages. [source] and the keys of [pages] are repo paths."""

	def replace(match):
		href, label = match.group(1), match.group(2)
		if re.match(r"^[a-z]+:", href) or href.startswith("#"):
			return match.group(0)
		path, _, anchor = href.partition("#")
		target = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
		fragment = "#" + anchor if anchor else ""
		if target in pages:
			return f'<a href="{pages[target]}{fragment}">{label}</a>'
		if target.startswith("docs/api/") and target.endswith(".md"):
			name = posixpath.basename(target)[:-3]
			if name == "index" or name in api:
				return f'<a href="{base}api/{"" if name == "index" else name + ".html"}{fragment}">{label}</a>'
		return f'<span class="unlinked">{label}</span>'

	return re.sub(r'<a href="([^"]+)">(.*?)</a>', replace, content, flags=re.DOTALL)


def nav(guides: list, titles: dict, current: str, base: str) -> str:
	def item(href: str, label: str) -> str:
		here = ' aria-current="page"' if href == current else ""
		return f'<li><a href="{href}"{here}>{html.escape(label)}</a></li>'

	parts = ['<nav class="api-nav">']
	for heading, stems in TOP[:1]:
		parts.append(f"<h2>{heading}</h2><ul>")
		parts += [item(f"{base}{stem}.html", titles[stem]) for stem in stems]
		parts.append("</ul>")
	parts.append('<h2>Guides</h2><ul>')
	parts += [item(f"{base}guides/{stem}.html", title) for title, stem, _ in guides]
	parts.append("</ul>")
	parts.append('<h2>Reference</h2><ul>')
	parts.append(item(f"{base}api/", "API reference"))
	parts += [item(f"{base}{stem}.html", titles[stem]) for stem in TOP[1][1]]
	parts.append("</ul></nav>")
	return "".join(parts)


def home(guides: list, titles: dict) -> str:
	rows = "".join(f'<tr><td><a href="guides/{stem}.html">{html.escape(title)}</a></td><td>{html.escape(summary)}</td></tr>'
		for title, stem, summary in guides)
	more = "".join(f'<li><a href="{stem}.html">{html.escape(titles[stem])}</a></li>' for stem in TOP[1][1])
	return f"""<h1>Hammerite 3D docs</h1>
<p class="lede-doc">How to put Hammerite in your game, how its classes are used together, and every
supported class and member.</p>
<div class="doc-cards">
<a class="doc-card" href="install.html"><h2>Install</h2><p>Requirements, the addon folders, enabling the plugins.</p></a>
<a class="doc-card" href="getting-started.html"><h2>Getting started</h2><p>A map in your game with the editor over it, step by step.</p></a>
<a class="doc-card" href="api/"><h2>API reference</h2><p>Every supported class, generated from the source's documentation.</p></a>
</div>
<h2>Guides</h2>
<p>How the classes are used together, one task at a time.</p>
<table class="members"><thead><tr><th>Guide</th><th></th></tr></thead><tbody>{rows}</tbody></table>
<h2>Going further</h2>
<ul>{more}</ul>"""


def main() -> int:
	if len(sys.argv) != 4:
		print(__doc__, file=sys.stderr)
		return 2
	repo = Path(sys.argv[1]).resolve()
	version = sys.argv[2]
	template = Path(sys.argv[3]).read_text()
	base = f"/hammerite/docs/{version}/"
	out_dir = SITE / "hammerite" / "docs" / version
	docs = repo / "docs"
	guides = guides_table((docs / "guides" / "index.md").read_text())
	api = {p.stem for p in (out_dir / "api").glob("*.html")} - {"index"}

	sources = {}
	for _, stems in TOP:
		for stem in stems:
			sources[f"docs/{stem}.md"] = f"{base}{stem}.html"
	sources["docs/guides/index.md"] = f"{base}guides/"
	for _, stem, _ in guides:
		sources[f"docs/guides/{stem}.md"] = f"{base}guides/{stem}.html"
	titles = {Path(src).stem: title_of((repo / src).read_text()) for src in sources if src.count("/") == 1}

	def write(path: Path, title: str, current: str, content: str) -> None:
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text(template.replace("{title}", html.escape(title))
			.replace("{nav}", nav(guides, titles, current, base)).replace("{content}", content))

	for source, url in sources.items():
		text = (repo / source).read_text()
		content = relink(render(text), source, sources, api, base)
		page = url.removeprefix(base)
		write(out_dir / (page + "index.html" if page.endswith("/") else page), title_of(text), url, content)
	write(out_dir / "index.html", "Docs", base, home(guides, titles))
	print(f"import_hammerite_docs: {len(sources) + 1} pages to {out_dir}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
