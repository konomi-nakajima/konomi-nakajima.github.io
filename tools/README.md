# tools/ — how `site/` was generated

These are the scripts used (with Claude) to turn the Webflow export in `reference/` into the static site in `site/`.
You do **not** need them to edit the site: `site/` is plain HTML and CSS and can be edited directly.
Kept for the record, and in case the site ever needs to be regenerated.

| File | What it does |
|---|---|
| `build.py` | Reads `reference/html/*.html` and writes the clean pages in `site/` (also copies images). |
| `alt_text.py`, `alt_ja.py` | The English and Japanese alt text for every image. |
| `meta_text.py` | Page titles and descriptions. |
| `optimize.py` | Converts images to WebP and updates the references (needs the Pillow library). |
| `og-image.jpg` | Master copy of the 1200×630 link-preview image. |

Caveats: the scripts expect the original folder locations (`/Users/konomi/Documents/portfolio-site`) and a few
setup details (environment variable `SCRATCH` pointing at this folder, and a Python with Pillow). Running
`build.py` rewrites the pages and would overwrite any hand edits made in `site/` since.
