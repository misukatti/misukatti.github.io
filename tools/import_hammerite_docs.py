#!/usr/bin/env python3
"""Render one version's guides and manual into hammerite/docs/<version>/ beside its API reference.

    tools/import_hammerite_docs.py <hammerite source> <version> <page template>

tools/import_hammerite_docs.sh runs this after the API reference, with the template it filled in
for the version. Pages come from the source's
docs/: the top-level guides (installing, getting started, baking...) and docs/guides/. A link to
another of these pages or to the API reference becomes a link to its HTML page; a link to anything
else in the repository - a README, the manual, a script - is left as plain text, since the
repository is not public.

The manual is the one the editor shows under Help, from each addon's manual/ directory: a folder per
section in manual/, its links and images as they are in the repository, as docs/manual/publish.sh
lays it out. A heading's anchor is the editor's, so a link to one lands on the same heading.
"""

import html
import posixpath
import re
import shutil
import sys
from pathlib import Path

import markdown

SITE = Path(__file__).resolve().parent.parent

TOP = [
	("Get started", ["install", "getting-started"]),
	("Going further", ["migrating-to-2.0", "baking", "performance", "troubleshooting", "api-stability"]),
]


MANUAL = [
	("core", "Core", "hammerite-core/manual"),
	("editor", "Editor", "hammerite-editor/manual"),
	("audio", "Audio", "hammerite-audio/manual"),
	("nav", "Navigation", "hammerite-nav/manual"),
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


def front_matter(text: str) -> tuple:
	"""(fields, body) of a manual page."""
	match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
	if not match:
		return {}, text
	fields = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
	return {k.strip(): v.strip() for k, v in fields.items()}, text[match.end():]


def manual_sections(repo: Path) -> list:
	"""[(id, title, directory, [(stem, title)])], each section's pages in the editor's order."""
	sections = []
	for section, label, directory in MANUAL:
		folder = repo / directory
		if not folder.is_dir():
			continue
		pages = []
		for page in folder.glob("*.md"):
			fields, body = front_matter(page.read_text())
			order = -1 if page.stem == "index" else int(fields.get("order", 1000))
			pages.append((order, page.stem, fields.get("title") or title_of(body)))
		pages.sort()
		sections.append((section, label, folder, [(stem, title) for _, stem, title in pages]))
	return sections


# HammeriteManualPage::anchor_for: lowercase, spaces to hyphens, and only letters, digits, - and _
# kept; a repeated heading numbered as GitHub does.
def anchor_for(text: str) -> str:
	lowered = html.unescape(re.sub(r"<[^>]+>", "", text)).strip().lower()
	return "".join("-" if c == " " else c for c in lowered if c in " -_" or c.isascii() and c.isalnum() or ord(c) > 127)


def manual_page(body: str, folder: Path, section: str, pages: set) -> str:
	body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
	content = markdown.markdown(body, extensions=["tables", "fenced_code", "sane_lists"])
	used = {}

	def heading(match):
		anchor = anchor_for(match.group(2))
		if anchor in used:
			used[anchor] += 1
			anchor = f"{anchor}-{used[anchor]}"
		else:
			used[anchor] = 0
		return f'<h{match.group(1)} id="{anchor}">{match.group(2)}</h{match.group(1)}>'

	content = re.sub(r"<h([1-3])>(.*?)</h\1>", heading, content)

	def figure(match):
		alt, src = html.unescape(match.group(1)), match.group(2)
		if not (folder / src).is_file():
			return f'<figure class="manual-missing"><figcaption>{html.escape(alt)}</figcaption></figure>'
		return (f'<figure><img src="{src}" alt="{html.escape(alt)}" loading="lazy">'
			f'<figcaption>{html.escape(alt)}</figcaption></figure>')

	content = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)" ?/?></p>', figure, content)
	content = re.sub(r"<blockquote>\s*<p><strong>(\w+):</strong>",
		lambda m: f'<blockquote class="callout callout-{m.group(1).lower()}"><p><strong>{m.group(1)}:</strong>', content)

	def link(match):
		href, label = match.group(1), match.group(2)
		if re.match(r"^[a-z]+:", href) or href.startswith("#"):
			return match.group(0)
		path, _, anchor = href.partition("#")
		target = posixpath.normpath(posixpath.join(section, path))
		if not path.endswith(".md") or target not in pages:
			return f'<span class="unlinked">{label}</span>'
		return f'<a href="{path[:-3]}.html{"#" + anchor if anchor else ""}">{label}</a>'

	return re.sub(r'<a href="([^"]+)">(.*?)</a>', link, content, flags=re.DOTALL)


def manual_nav(sections: list, current: str, base: str) -> str:
	parts = ['<nav class="api-nav">', f'<a class="api-home" href="{base}manual/">Manual</a>']
	for section, label, _, pages in sections:
		parts.append(f"<h2>{html.escape(label)}</h2><ul>")
		for stem, title in pages:
			href = f"{base}manual/{section}/{stem}.html"
			here = ' aria-current="page"' if href == current else ""
			parts.append(f'<li><a href="{href}"{here}>{html.escape(title)}</a></li>')
		parts.append("</ul>")
	parts.append(f'<h2>Docs</h2><ul><li><a href="{base}">Docs home</a></li><li><a href="{base}api/">API reference</a></li></ul>')
	parts.append("</nav>")
	return "".join(parts)


def manual_home(sections: list, repo: Path) -> str:
	cards = []
	for section, label, folder, _ in sections:
		_, body = front_matter((folder / "index.md").read_text())
		lede = next((line for line in body.splitlines() if line and not line.startswith(("#", "!", "<"))), "")
		lede = re.sub(r"\*\*|`|\[([^\]]+)\]\([^)]*\)", lambda m: m.group(1) or "", lede)
		cards.append(f'<a class="doc-card" href="{section}/index.html"><h2>{html.escape(label)}</h2>'
			f"<p>{html.escape(lede)}</p></a>")
	return f"""<h1>Hammerite manual</h1>
<p class="lede-doc">The manual the editor shows under Help: for the people who build levels with it.
How the carved world works, every tool, and the audio and navigation it builds.</p>
<div class="doc-cards">{"".join(cards)}</div>"""


def write_manual(repo: Path, out_dir: Path, base: str, template: str) -> int:
	sections = manual_sections(repo)
	if not sections:
		return 0
	manual_dir = out_dir / "manual"
	pages = {f"{section}/{stem}.md" for section, _, _, stems in sections for stem, _ in stems}
	count = 0

	def write(path: Path, title: str, current: str, content: str) -> None:
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text(template.replace("{title}", html.escape(title))
			.replace("{nav}", manual_nav(sections, current, base)).replace("{content}", content))

	for section, label, folder, stems in sections:
		for stem, title in stems:
			_, body = front_matter((folder / f"{stem}.md").read_text())
			content = manual_page(body, folder, section, pages)
			write(manual_dir / section / f"{stem}.html", f"{label} manual" if stem == "index" else title,
				f"{base}manual/{section}/{stem}.html", content)
			count += 1
		if (folder / "images").is_dir():
			shutil.copytree(folder / "images", manual_dir / section / "images",
				ignore=shutil.ignore_patterns("*.import"), dirs_exist_ok=True)
	write(manual_dir / "index.html", "Manual", f"{base}manual/", manual_home(sections, repo))
	return count + 1


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
	parts.append(item(f"{base}manual/", "Manual"))
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
<a class="doc-card" href="manual/"><h2>Manual</h2><p>The editor's own manual, for the people who build the levels.</p></a>
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
	global TOP
	TOP = [(heading, [stem for stem in stems if (docs / f"{stem}.md").exists()]) for heading, stems in TOP]
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
	manual = write_manual(repo, out_dir, base, template)
	print(f"import_hammerite_docs: {len(sources) + 1} pages and {manual} manual pages to {out_dir}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
