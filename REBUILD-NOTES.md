# Rebuild notes

## Design pass (second round)

After the faithful rebuild you asked for a better layout, so the site **no longer matches the original pixel for pixel**, on purpose. What changed:

- **Type scale and spacing scale.** Seven text sizes (13 → 44px, fluid between phone and desktop) and eight spacings (4 → 96px) replace the ~25 sizes and ~30 one-off margins. Body text is 16–18px (was 14–16), captions 13px (was 6–10px), line height 1.75.
- **Contrast.** The grey for notes, footnotes and links on the beige pages is now #5f5f5f (5.1:1; it was #7e7e7e at 3.2:1). Every text colour now passes the 4.5:1 minimum.
- **Reading width and alignment.** Text in the case studies is left-aligned with the header's left edge. On the two Japanese case studies (Goodwill, Honda) everything, including the title, project details and slides, sits in one centred column 40 characters wide (40 × the body font size, about 717px on desktop), with text left-aligned inside it. Footnotes are inset further (narrower than the body text) and have no side line; the one real quote on Goodwill keeps its line. The AI-process page uses the same layout in a narrower 30-character column, chosen so its first sentence breaks after "ChatGPTを" instead of stranding "た。". To change the widths, edit `--measure` under `.article--column` and `.article--narrow` in `css/style.css`.
- **Line spacing** is 1.6 (was 1.75, and the original site's Japanese articles used 1.5), with a 1em gap between paragraphs.
- **About page.** English stays shifted left and Japanese shifted right, on desktop and phones, as in the original. The 362px / 500px padding hacks that did it are replaced by a simple width and margin.
- **Home page.** Same layout as the original (English tagline left, Japanese right-aligned below it, photo on the right, two columns even on phones). The English tagline is now the page's `<h1>`. No extra copy or links: visitors find About and Projects in the header.
- **Photo captions** (home and about) are deliberately quiet: 10px, thin weight, 75% opacity.
- **Touch targets.** Nav links, footer links and the 日本語訳あり link are at least 44px tall.
- **Click-to-zoom** on every slide in the case studies (keyboard accessible; on phones the slide opens larger than the screen so its text can be read, and you can scroll around it).
- **Header on phones** is smaller (18–20px name, 16–24px from the top instead of 68–88px) and has **no menu**: "About" and "Projects" stay in the header as links at every width, so the hamburger button and its script are gone. Only at around 320px wide do the links drop to a second line.
- Section headings in the Japanese case studies now use Noto Sans JP like the body text (before: system font).
- Small things dropped: the extra blank lines a few paragraphs had, and the per-page quirks listed below.

The comparison results below describe the first, faithful rebuild.

## How closely it matches

I rendered the original (a local copy of the Webflow pages) and the rebuild in headless Chrome and compared the position, size, font, weight and colour of every line of text and every image, on all 8 pages, at widths from 320px to 1920px (including both sides of the 991 / 767 / 479px breakpoints).

- **home, about, projects, robot, medium, honda, goodwill**: identical to the pixel, at every width, except the nav offset below. Page heights match too.
- **ai-process**: layout identical; the only differences are the font-build issue in #1.

I also checked that the visible text and image descriptions on every page are identical to the original (the only change: Honda's requirements box now pairs each heading with its list in the HTML; it looks the same). I looked at the home page and the open mobile menu side by side with the live site.

## Couldn't reproduce exactly

1. **Font files.** The old site loaded Google Fonts through Webflow's loader in fixed weights. The rebuild self-hosts Google's current files (Karla and Noto Sans JP are now variable fonts). Result: on `/ai-process`, Latin letters inside Japanese text can differ by a few pixels, and one paragraph wraps at a slightly different spot at some widths (tablet and phone). I matched the one visible weight difference I found (the bold "nurturing your AI" renders at weight 800, as it did before).
2. **Hamburger icon.** Webflow drew it from an icon font; I redrew it as a small inline SVG. It's the same size and position but not the same glyph, so it can differ by a pixel or so.

## Deliberately different (small fixes to the old site's quirks)

- **Nav/logo position on phones.** The original had accidental per-page offsets: logo 5px further right on home, 10px further right on goodwill/honda/ai-process. All pages now use the same 20px margin.
- **Short pages scrolled too far.** In the original, an empty element pushed the whole page down 88px (68px on light pages), so a short page, such as home on a phone, could scroll by that much for no reason. Not reproduced.
- **Footer "|"** was a link to the home page. It's now plain text.
- **ai-process nav "Projects"** linked to `konomi.cc/#projects` (an anchor that doesn't exist on the home page). It now goes to `/projects/`.
- **Structured data (JSON-LD).** Kept on every page. Fixed two errors: the home page had a template placeholder image (`…/[your-profile-photo-url]`), now removed; the robot page's `url` said `/astro`, now `/robot`.
- **`/astro`** was a live page, not linked anywhere, identical to `/robot`. It's now a small redirect to `/robot/` so old links don't break.
- **Added, invisible**: `lang` attributes (`ja`/`en`) for screen readers and font selection, a real `<button>` for the menu with `aria-expanded`, `aria-current` on the active nav link, `<figure>`/`<figcaption>`, and `width`/`height` on every image so the page doesn't jump while loading.

## Changes made after the first rebuild (your requests)

- Header: "|" is now "・" (`Konomi ・ 中島このみ`).
- Mobile menu: the icon is white on the dark pages (it stays black on the light case-study pages, where white would be invisible). The menu now opens in the flow of the page, pushing the content down instead of covering it, as a panel on the right half of the screen with more space above "About", and it animates open and closed (respecting the "reduce motion" setting).
- Alt text: every image (all 32 uses of 28 pictures) has new bilingual alt text in the format "AI-generated alt text / English: … / 日本語：…". The Japanese was written separately, not translated from the English. Because these edits changed the header and menu, the pixel-match results above describe the first rebuild; the page layouts are otherwise unchanged.

## Added after review

- **Link preview** (Slack, LinkedIn, iMessage, etc.): `images/og-image.jpg`, a 1200×630 crop of the home photo around the horizon, referenced from every page's `<head>`.
- **Self-hosted fonts** (no requests to Google; `css/fonts.css` + `fonts/`, trimmed to the characters the site uses after a Lighthouse report showed the full list was slowing phones down; new Japanese characters you might add later would show in a system font, so ask me to regenerate the list) and **WebP images** (about 40% smaller files; typical page about 30% lighter).
- **"Skip to content" link**: invisible until a keyboard user presses Tab; jumps past the header to the page content.
- **New-tab links** (LinkedIn, Bluesky, the Medium article) now tell screen-reader users they open in a new tab.
- **Print stylesheet**: printing or "Save as PDF" gives white pages with black text, no navigation, and the address after each external link.
- Project hashtags are smaller (15px) and thin (weight 200) with a larger gap above them.

## Phone refinements (after checking on Safari)

- Header: the name is 20px and the menu's overline sits close to its text, so the name and the menu have the same visual height; the name drops to 18px only below 360px wide.
- Home: one column on phones, English shifted left, Japanese shifted right, photo below it at about two-thirds width and centered. About photos use the same width. About line spacing is tighter (1.5 English, 1.7 Japanese).
- Japanese case studies: 17px text with 1.75 line spacing and 24px side margins on phones. I removed `text-wrap: pretty` from body text because Safari used it to shorten every line, which made the text look crammed to the left. (Safari also ignores `word-break: auto-phrase`, so Japanese there breaks between any two characters; Chrome and Edge break at phrase boundaries.)
- The 余談 note is inset like the other footnotes. The Honda "***" footnote is a plain footnote (it was styled as a quote by mistake).
- The "Next project" / "All projects" links at the bottom of the case studies were added and then removed again at your request.
- Japanese headings break between phrases in every browser, including Safari: `tools/phrases.py` adds `<wbr>` marks (using Google's BudouX) and the `.jp-phrases` CSS rule honors them. On phones the case-study column sits 8px further in than the header. Home on phones has a smaller English phrase, more left padding and more space between the English, Japanese and photo. The header has 48px above it on phones.

## Phone refinements, round 3

- Home on phones: the English and Japanese phrases come first and fill most of the first screen (the block is the screen height minus 16rem, so about 100px of the photo shows at the bottom as a hint to scroll), then the photo. The English starts 48px from the left edge and the Japanese ends 48px from the right edge. On desktop the photo is still in the right column. About photos on phones are 78% wide, which puts their left edge halfway between the English and Japanese text edges.
- About line spacing on phones is 1.4 for English and 1.6 for Japanese; Projects descriptions are 1.45. These are below the 1.5 that WCAG's strictest level (AAA) recommends, but meet the AA level, which only requires that readers can raise spacing to 1.5 themselves. If readability on small screens ever feels tight, raise them in `css/style.css`.
- The Japanese case studies are left-aligned with the header again on phones (the 8px inset was removed).
- The menu link for the page you're on is bold as well as having the thicker line (Inconsolata 400–700 is included in `fonts/`).

## Search setup

- `sitemap.xml` and `robots.txt` list the 8 pages and point search engines at the sitemap. Both assume the site lives at `https://konomi.cc` (no "www"); if the address ever changes, update them and the `canonical` line in each page's `<head>`.
- Each page has a `canonical` tag naming its official address, so `konomi.cc` and `www.konomi.cc` aren't counted as two copies. Still set up a redirect from `www.konomi.cc` to `konomi.cc` at your host.

## Page titles and descriptions

Rewritten for search: each says what the page helps a searcher with, not the article's headline. Japanese for About, Honda and Goodwill (their text is Japanese); English for the rest; the Projects description is bilingual. They live in each page's `<head>` (`<title>`, `description`, and the `og:`/`twitter:` copies used for link previews). Google cuts results off by pixel width, not character count: roughly 600px for titles and 900px for descriptions on desktop (narrower on phones), so Japanese characters count about double. The current text is sized to fit: about 60 English or 30 Japanese characters for titles, about 140 English or 60 Japanese characters for descriptions. Put the key point first, since the end is what gets cut. These limits are estimates, and Google sometimes rewrites snippets anyway.

## Preserved quirks (same as the original, easy to change)

- Section headings in the two Japanese case studies (e.g. 「はじめに：本編の読み方」) never had a font set, so they render in the browser's default (Arial → your system's Japanese font) rather than Noto Sans JP like the body text. Left as is. To change it, add `font-family: var(--font-jp);` to `.section-title` in `css/style.css`.
- The home page has no `<h1>`.

## Still to do on your side

- **Hosting + domain.** Nothing is deployed. The domain still points at Webflow, which also provided HTTPS and the redirect between the two addresses (Webflow sent `konomi.cc` to `www.konomi.cc`; the rebuilt site does the reverse); set those up at the new host (see `README.md`).
- **Things Webflow keeps that aren't in the published HTML** (unpublished drafts, CMS items, the project itself): export those from the Webflow dashboard if you want them.
- I could only discover pages by following links and probing about 15 likely URLs. If you ever published a page with no link to it, other than `/astro`, I wouldn't have found it. Tell me any you know of.
