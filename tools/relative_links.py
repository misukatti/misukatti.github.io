#!/usr/bin/env python3
"""Rewrite the site's root-relative links as links relative to each page, so the site also works
opened straight from disk.

    tools/relative_links.py [file or directory ...]     default: the whole site, but tools/

A link to a page names its index.html ("../hammerite/index.html", not "../hammerite/"), because a
browser reading files does not look for index.html in a folder. Absolute addresses (https://...,
mailto:) are left alone, and so are canonical links and og: meta tags, which must stay absolute.
Running it twice changes nothing.
"""

import os
import posixpath
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
ATTRIBUTE = re.compile(r'''(?P<attr>\b(?:href|src)=)(?P<q>["'])(?P<url>/(?!/)[^"']*)(?P=q)''')
REFRESH = re.compile(r'''(?P<attr>content=)(?P<q>["'])(?P<pre>\d+;\s*url=)(?P<url>/(?!/)[^"']*)(?P=q)''')
REPLACE = re.compile(r'''(?P<attr>location\.replace\()(?P<q>["'])(?P<url>/(?!/)[^"']*)(?P=q)''')
CANONICAL = re.compile(r'<link\s+rel="canonical"[^>]*>|<meta\s+property="og:[^>]*>')


def relative(url: str, page: Path) -> str:
    path, hash_mark, fragment = url.partition("#")
    path, question, query = path.partition("?")
    target = path.lstrip("/")
    if target == "" or target.endswith("/"):
        target += "index.html"
    elif (SITE / target).is_dir():
        target += "/index.html"
    here = posixpath.dirname(page.relative_to(SITE).as_posix())
    result = posixpath.relpath(target, here or ".")
    return result + (question + query if question else "") + (hash_mark + fragment if hash_mark else "")


def rewrite(page: Path) -> bool:
    text = page.read_text()
    kept = {}

    def keep(match):
        kept[f"\0{len(kept)}\0"] = match.group(0)
        return f"\0{len(kept) - 1}\0"

    work = CANONICAL.sub(keep, text)
    work = ATTRIBUTE.sub(lambda m: f'{m["attr"]}{m["q"]}{relative(m["url"], page)}{m["q"]}', work)
    work = REFRESH.sub(lambda m: f'{m["attr"]}{m["q"]}{m["pre"]}{relative(m["url"], page)}{m["q"]}', work)
    work = REPLACE.sub(lambda m: f'{m["attr"]}{m["q"]}{relative(m["url"], page)}{m["q"]}', work)
    for token, original in kept.items():
        work = work.replace(token, original)
    if work != text:
        page.write_text(work)
        return True
    return False


def pages(arguments: list) -> list:
    if not arguments:
        arguments = [str(SITE)]
    found = []
    for argument in arguments:
        path = Path(argument).resolve()
        if path.is_dir():
            found += [p for p in path.rglob("*.html") if not {".git", "tools"} & set(p.parts)]
        elif path.suffix == ".html":
            found.append(path)
    return sorted(found)


def main() -> int:
    changed = sum(rewrite(page) for page in pages(sys.argv[1:]))
    print(f"relative_links: {changed} pages rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
