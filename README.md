# misukatti.github.io

Misukatti Interactive's website: plain static HTML and CSS, no build step.

| Path | |
|---|---|
| `index.html`, `assets/site.css` | The studio page: City of Thieves, Hammerite 3D, contact. Night and moon, DM Serif Display and Josefin Sans. |
| `hammerite/` | Hammerite 3D's page, in Hammerite's own look: stone, red and Cinzel, with a slim Misukatti bar and footer. |
| `assets/misukatti/` | Logos from [misukatti/brand](https://github.com/misukatti/brand): the `night` versions, which have no SVG mask. The `on-dark` ones are masked, and Safari on iOS blurs masks. |
| `hammerite/api/`, `hammerite/docs/` | Hammerite's API reference and its guides, generated from a Hammerite checkout; see below. Never edit the pages by hand. `hammerite/docs/docs.css` and `tools/docs-template.html` are this site's own. |
| `hammerite/assets/` | Hammerite's logo, favicons and screenshots, from the Hammerite repo (`docs/logo/`, the editor manual's images). |

Links are root-relative (`/hammerite/`), so the site has to be served from a domain's root: the org
Pages site or a custom domain, not a project path.

To look at it locally:

```bash
python3 -m http.server 8765
```

## Hammerite's docs

```bash
tools/import_hammerite_docs.sh ../hammerite
```

Regenerates `hammerite/api/` and `hammerite/docs/` from a Hammerite checkout: the API reference
through Hammerite's own `tools/make_api_docs.sh`, then the guides. Commit what changes. Needs Godot
and Python's `markdown` package
(`pip install markdown`). Links to files in the Hammerite repository outside `docs/` are shown as
plain text, since that repository is private.

## Before going live

- The **Buy** button on the Hammerite page points at `#buy`. Replace the `href` with the store page
  and drop "Store link coming soon".
- `hello@misukatti.fi` only receives mail once the domain has a mail provider and its MX records.

## Publishing

GitHub Pages serves `main` from the root at <https://misukatti.fi>. `CNAME` names the domain, and
misukatti.github.io and www.misukatti.fi redirect there.

DNS is at iwantmyname: four `A` records for the apex to GitHub Pages' addresses
(`185.199.108.153` to `185.199.111.153`), a `CNAME` from `www` to `misukatti.github.io`, and the
`_github-pages-challenge-misukatti` TXT record that verifies the domain for the organisation.
