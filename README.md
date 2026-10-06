# konomi.cc — portfolio site

Two folders:

| Folder | What it is |
|---|---|
| `site/` | The rebuilt site: plain HTML + one CSS file + a tiny JS file. No Webflow code, no build step. |
| `reference/` | Everything downloaded from the published Webflow site, untouched, so nothing is lost. See `reference/README.md`. |

See [REBUILD-NOTES.md](REBUILD-NOTES.md) for what was and wasn't reproduced exactly.

## Preview locally

Pages use root-relative URLs (`/about/`, `/css/style.css`), so serve `site/` as the web root:

```bash
python3 -m http.server 8000 --directory site
```

Then open http://localhost:8000. (Opening the files by double-click won't work: the links and CSS expect to be served from `/`.)

## Structure

```
site/
  index.html              home
  about/index.html
  projects/index.html
  goodwill/  honda/  robot/  medium/  ai-process/    one folder per page → URL /goodwill/ etc.
  astro/index.html        redirect to /robot/ (old URL that was still live)
  css/fonts.css           @font-face rules for the self-hosted fonts in fonts/
  css/style.css           all styling; design tokens (colours, type scale, spacing scale) are at the top
  js/main.js              click-to-zoom on case-study images (the only JavaScript)
  images/<page>/…         every image as WebP, including the responsive -p-500 … -p-1600 sizes
  fonts/                  self-hosted font files
```

Page URLs are the same as on the old site, so existing links keep working.

## Editing

- **Text**: edit the HTML directly. Case studies use plain `<h2>`, `<p>`, `<ul>`, `<mark>` (the tan highlight) and `<img class="shot">`.
- **Colours / fonts / spacing**: the tokens are at the top of `css/style.css` (`--rust`, `--paper`, `--text-m`, `--space-l`, `--measure`, …). Change a token and it changes everywhere.
- **New project**: copy a page folder (e.g. `robot/`), edit it, then add a row to `projects/index.html` (copy an `<article class="project">`).
- **New image**: put it in `images/<page>/`. Use `srcset` for large images, as the existing ones do.

## Deploying

Any static host works (Cloudflare Pages, Netlify, GitHub Pages with a custom domain, S3 + CDN). Publish the contents of `site/` at the **root** of the domain. Nothing has been deployed yet; the live site is still on Webflow. When you move the domain, also set up what Webflow did for you:

- HTTPS, and a redirect from `www.konomi.cc` to `konomi.cc` (the site's pages all name `konomi.cc`, without "www", as their official address).
- Optionally a `404.html` for unknown URLs.

Fonts (Karla, Kiwi Maru, Inconsolata, Noto Sans JP) are included in `site/fonts/`, so the site makes no requests to Google. Images are WebP (the `reference/` folder keeps the originals). Link previews use `images/og-image.jpg` (1200×630).
