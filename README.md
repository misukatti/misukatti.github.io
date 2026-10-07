# misukatti.github.io

Misukatti Interactive's website: plain static HTML and CSS, no build step.

| Path | |
|---|---|
| `index.html`, `assets/site.css` | The studio page: City of Thieves, Hammerite 3D, contact. Night and moon, DM Serif Display and Josefin Sans. |
| `hammerite/` | Hammerite 3D's page, in Hammerite's own look: stone, red and Cinzel, with a slim Misukatti bar and footer. |
| `assets/misukatti/` | Logos from [misukatti/brand](https://github.com/misukatti/brand): the `night` versions, which have no SVG mask. The `on-dark` ones are masked, and Safari on iOS blurs masks. |
| `hammerite/assets/` | Hammerite's logo, favicons and screenshots, from the Hammerite repo (`docs/logo/`, the editor manual's images). |

Links are root-relative (`/hammerite/`), so the site has to be served from a domain's root: the org
Pages site or a custom domain, not a project path.

To look at it locally:

```bash
python3 -m http.server 8765
```

## Before going live

- The **Buy** button on the Hammerite page points at `#buy`. Replace the `href` with the store page
  and drop "Store link coming soon".
- `hello@misukatti.fi` only receives mail once the domain is bought and has mail set up.

## Publishing

GitHub Pages: Settings → Pages → Deploy from a branch → `main`, `/ (root)`. It is then at
<https://misukatti.github.io>.

For misukatti.fi, once bought: add a `CNAME` file containing `misukatti.fi`, point the domain's DNS at
GitHub (`A` records for the apex to GitHub Pages' addresses, and a `CNAME` for `www` to
`misukatti.github.io`), then tick **Enforce HTTPS** in the Pages settings.
