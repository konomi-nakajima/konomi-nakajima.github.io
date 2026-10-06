# reference/ — snapshot of the published Webflow site

Downloaded 2026-10-06 from https://www.konomi.cc (Webflow "Last Published: Jan 06 2026"). Treat as read-only.

| Path | Contents |
|---|---|
| `html/` | The 9 published pages exactly as served: `index`, `about`, `projects`, `goodwill`, `honda`, `robot`, `medium`, `ai-process`, `astro` (`astro` is identical to `robot`; an old URL). Image/CSS/JS links still point at Webflow's CDN. |
| `assets/` | Every file those pages use, in folders named after the host they came from: `cdn.prod.website-files.com/…` (images, the Webflow CSS and JS, favicon), `d3e54v103j8qbb.cloudfront.net/` (jQuery), `ajax.googleapis.com/` (WebFont loader), `fonts.googleapis.com/fonts.css` + `fonts.gstatic.com/` (all 619 font files the site could request). 141 images include every responsive size (`-p-500` … `-p-1600`). |
| `offline/` | The same pages with their links rewritten to point at `assets/`, so they open from a local server without Webflow's CDN: `python3 -m http.server 8000` from the project root, then http://localhost:8000/reference/offline/index.html. (Fonts still come from Google.) |
| `manifest.json` | Every page and asset: original URL → local path, plus notes. |

Not included: anything that isn't in the published HTML. Unpublished drafts, Webflow CMS data and the Webflow project itself can only be exported from the Webflow dashboard (Site settings → Backups, or Export code).
