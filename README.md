# Frondworks

Local SEO + Google Business Profile management for plumbers. $997/mo.

## Site
Static site (HTML/CSS/JS, no build step), deployed via GitHub Pages from `main`.

- `index.html` — Frondworks studio homepage (umbrella brand)
- `plumbers.html` — plumber practice landing page
- `pricing.html` — plumber program pricing
- `contact.html` — free audit request form (POSTs to `/api/lead`)
- `favicon.svg` — orange "F" site icon
- `worker/lead-form.js` — Cloudflare Worker handling form submissions
  (Discord alert + optional Resend email). Deploy notes in the file header.

## Launch checklist
- [x] Site built and pushed
- [ ] DNS pointed at GitHub Pages
- [ ] Email forwarding + SPF/DKIM/DMARC
- [ ] Worker deployed at frondworks.com/api/lead

## Security
Secrets (Discord webhook URL, Resend API key, Cloudflare tokens) are stored as
Cloudflare Worker secrets via `wrangler secret put` — never in this repo. The
worker reads them from `env` at runtime. Do not commit `.env`, `.dev.vars`,
or any credential files. See `.gitignore`.
