# Frondworks

Local SEO + Google Business Profile management for plumbers. $997/mo.

## Site
Static site (HTML/CSS/JS, no build step), deployed via GitHub Pages from `main`.

- `index.html` — homepage
- `pricing.html` — pricing
- `contact.html` — free audit request form (POSTs to `/api/lead`)
- `worker/lead-form.js` — Cloudflare Worker handling form submissions
  (Discord alert + optional Resend email). Deploy notes in the file header.

## Launch checklist
- [x] Site built and pushed
- [ ] DNS pointed at GitHub Pages
- [ ] Email forwarding + SPF/DKIM/DMARC
- [ ] Worker deployed at frondworks.com/api/lead
