# misukatti.github.io

Misukatti Interactive's website: plain static HTML and CSS, no build step.

| Path | |
|---|---|
| `index.html`, `assets/site.css` | The studio page: City of Thieves, Hammerite 3D, contact. Night and moon, DM Serif Display and Josefin Sans. |
| `hammerite/` | Hammerite 3D's page, in Hammerite's own look: stone, red and Cinzel, with a slim Misukatti bar and footer. |
| `assets/misukatti/` | Logos from [misukatti/brand](https://github.com/misukatti/brand): the `night` versions, which have no SVG mask. The `on-dark` ones are masked, and Safari on iOS blurs masks. |
| `hammerite/docs/<version>/` | Hammerite's docs, one folder per version: its guides and its API reference, generated from a Hammerite checkout; see below. Never edit the pages by hand. `hammerite/docs/docs.css`, `versions.js` and `tools/docs-template.html` are this site's own. |
| `hammerite/api/`, the rest of `hammerite/docs/` | Redirects from the addresses the docs had before they had versions, to the current release. |
| `hammerite/assets/` | Hammerite's logo, favicons and screenshots, from the Hammerite repo (`docs/logo/`, the editor manual's images). |

Links are root-relative (`/hammerite/`), so the site has to be served from a domain's root: the org
Pages site or a custom domain, not a project path.

To look at it locally:

```bash
python3 -m http.server 8765
```

## Hammerite's docs

Each version has its own folder, `hammerite/docs/1.0/`, `hammerite/docs/latest/`, and every page has
a switcher between them. `hammerite/docs/` goes to the current release.

```bash
tools/import_hammerite_docs.sh latest          # master, rebuilt every time
tools/import_hammerite_docs.sh 1.1             # tag v1.1.0, once
```

The pages come from the ref, exported with `git archive` from the checkout `HAMMERITE=` names
(default `../hammerite`): the API reference through that version's own `tools/make_api_docs.sh`,
then the guides. Needs Godot and Python's `markdown` package (`pip install markdown`).

- **Releases are read-only.** Once a version's folder exists the script refuses to write it again,
  unless `FORCE=1`. Its pages still list later versions: `versions.json` is read when the page is
  viewed.
- **Releasing:** import the new version, then `latest` if master has moved on. The newest release
  becomes the current one: `hammerite/docs/` and the old addresses go there, and the other
  versions' pages say there is a newer one.
- Links to files in the Hammerite repository outside `docs/` are shown as plain text, since that
  repository is private.

## Before going live

- The **Buy** button on the Hammerite page points at `#buy`. Replace the `href` with the store page
  and drop "Store link coming soon".
- `hello@misukatti.fi` only receives mail once the domain has a mail provider and its MX records.

## Publishing

GitHub Pages serves `main` from the root at <https://misukatti.fi>. `CNAME` names the domain, and
misukatti.github.io and www.misukatti.fi redirect there. HTTPS is enforced, with a certificate GitHub
issues and renews itself, so http:// redirects to https://.

DNS is at iwantmyname: four `A` records for the apex to GitHub Pages' addresses
(`185.199.108.153` to `185.199.111.153`), a `CNAME` from `www` to `misukatti.github.io`, and the
`_github-pages-challenge-misukatti` TXT record that verifies the domain for the organisation.
