# Frondworks

Storefront for Frondworks digital products: practical printables and
spreadsheets for money, planning, and goals. Checkout is on Payhip
(https://payhip.com/Frondworks).

## Site
Static site (plain HTML and CSS, one small JS file), deployed by GitHub Pages
from `main`. DNS is on Cloudflare.

- `_build/products.json`: the product list. One entry per product.
- `_build/build.py`: generates `index.html`, `<slug>/index.html`, and
  `sitemap.xml` from `products.json`. Run `python3 _build/build.py`.
  Add `--images <preview root>` to regenerate `img/<slug>/` (WebP 600/1200
  plus a JPG fallback) from the source PNGs named in `products.json`.
- `_build/contact-form.html`: the contact form markup. It POSTs to
  `/api/lead` (Cloudflare Worker `frondworks-leads`, source in
  `worker/lead-form.js`). Do not rename the action, method, or fields.
- `assets/site.css`, `assets/site.js`: styles and the form submit helper.
- `contact.html`, `pricing.html`: redirect stubs to the home page (noindex).
- `plumbers.html`: archived, noindex, not in the sitemap or nav. Uses the
  old `styles.css` and `script.js`.
- `CNAME`: custom domain. Do not change.

## Adding a product
1. Add an entry to `_build/products.json` (slug, name, price, Payhip URL,
   description, preview image sources and alt text).
2. `python3 _build/build.py --images /path/to/previews/root`
3. Grep for dashes, commit, push.

## Security
Secrets (Discord webhook URL, Resend API key, Cloudflare tokens) are stored as
Cloudflare Worker secrets via `wrangler secret put`, never in this repo.
