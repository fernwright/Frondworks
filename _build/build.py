#!/usr/bin/env python3
"""Build the Frondworks storefront from _build/products.json.

Adding a product = add one entry to products.json, then run:
    python3 _build/build.py --images /path/to/preview/root   (once, to make WebP/JPG previews)
    python3 _build/build.py                                  (regenerates every page)

Generates: index.html, <slug>/index.html for each product, /guides/ pages,
sitemap.xml, and img/<slug>/*. Hand-kept files: CNAME, plumbers.html (archived), the
contact form markup below (field names must match worker/lead-form.js).
The _build folder is not published (Jekyll skips folders starting with _).
"""
import json, os, re, sys, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://frondworks.com"
SHOP = "https://payhip.com/Frondworks"
EMAIL = "hello@frondworks.com"
TODAY = datetime.date.today().isoformat()
products = json.load(open(os.path.join(ROOT, "_build", "products.json")))
guides = json.load(open(os.path.join(ROOT, "_build", "guides.json")))
e = html.escape

TOGETHER_ALT = "Preview pages from the Money Planner, the Bill Audit, and the Goal-Setting Kit, shown side by side"


def by_slug(slug):
    return next(p for p in products if p["slug"] == slug)

def is_bundle(p):
    return bool(p.get("bundle") or p.get("includes"))

def singles():
    return [p for p in products if not is_bundle(p)]

def bundles():
    return [p for p in products if is_bundle(p)]

def bundles_for(p):
    return [b for b in bundles() if p["slug"] in b.get("includes", [])]

def money(n):
    s = f"{float(n):.2f}"
    return "$" + (s[:-3] if s.endswith(".00") else s)

def count_word(n):
    return {2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
            7: "seven", 8: "eight", 9: "nine"}.get(n, str(n))


def separate_total(p):
    return sum(float(by_slug(s)["price"]) for s in p["includes"])

def bundle_save(p):
    return separate_total(p) - float(p["price"])

def compare_line(p):
    return f"Bought separately they are {money(separate_total(p))}, so you save {money(bundle_save(p))}."

def attach_together(p):
    """Prepend the generated together composite when the file exists."""
    if not is_bundle(p) or p.get("together") is False:
        return
    path = os.path.join(ROOT, "img", p["slug"], "together-1200.jpg")
    if os.path.exists(path) and not any(im["name"] == "together" for im in p["images"]):
        p["images"] = [{"src": "", "name": "together", "alt": TOGETHER_ALT}] + p["images"]

def make_together(p, src_root):
    from PIL import Image
    included = [by_slug(s) for s in p["includes"]]
    W, H = 1200, 630
    og = Image.new("RGB", (W, H), (244, 242, 236))
    n = len(included)
    margin, gap = 40, 24
    slot_w = (W - 2 * margin - gap * (n - 1)) // n
    x = margin
    for inc in included:
        src = next(im["src"] for im in inc["images"] if im.get("src"))
        img = Image.open(os.path.join(src_root, src)).convert("RGB")
        img.thumbnail((slot_w, H - 80), Image.LANCZOS)
        og.paste(img, (x + (slot_w - img.width) // 2, (H - img.height) // 2))
        x += slot_w + gap
    d = os.path.join(ROOT, "img", p["slug"]); os.makedirs(d, exist_ok=True)
    og.save(os.path.join(d, "together-1200.jpg"), "JPEG", quality=80, optimize=True, progressive=True)
    og.save(os.path.join(d, "together-1200.webp"), "WEBP", quality=80, method=6)
    small = og.copy(); small.thumbnail((600, 600), Image.LANCZOS)
    small.save(os.path.join(d, "together-600.webp"), "WEBP", quality=80, method=6)

# ---------- images ----------
def make_images(src_root):
    from PIL import Image
    for p in products:
        d = os.path.join(ROOT, "img", p["slug"]); os.makedirs(d, exist_ok=True)
        for im in p["images"]:
            if not im.get("src"):
                continue
            img = Image.open(os.path.join(src_root, im["src"])).convert("RGB")
            for size in (1200, 600):
                c = img.copy(); c.thumbnail((size, size), Image.LANCZOS)
                c.save(os.path.join(d, f'{im["name"]}-{size}.webp'), "WEBP", quality=80, method=6)
                if size == 1200:
                    c.save(os.path.join(d, f'{im["name"]}-1200.jpg'), "JPEG", quality=78, optimize=True, progressive=True)
        if is_bundle(p) and p.get("together") is not False:
            make_together(p, src_root)
    # home share image: individual product covers on a neutral background
    covers = singles()
    W, H = 1200, 630
    og = Image.new("RGB", (W, H), (244, 242, 236))
    n = len(covers)
    margin, gap = 40, 20
    slot_w = (W - 2 * margin - gap * (n - 1)) // n
    x = margin
    for p in covers:
        src = next(im["src"] for im in p["images"] if im.get("src"))
        img = Image.open(os.path.join(src_root, src)).convert("RGB")
        img.thumbnail((slot_w, H - 80), Image.LANCZOS)
        og.paste(img, (x + (slot_w - img.width) // 2, (H - img.height) // 2))
        x += slot_w + gap
    og.save(os.path.join(ROOT, "img", "og-home.jpg"), "JPEG", quality=80, optimize=True)

def dims(slug, name, size):
    from PIL import Image
    return Image.open(os.path.join(ROOT, "img", slug, f"{name}-{size}.webp")).size

def picture(p, im, sizes, lazy, cls="", priority=False):
    s, n = p["slug"], im["name"]
    w, h = dims(s, n, 1200)
    attrs = f'width="{w}" height="{h}"'
    attrs += ' loading="lazy" decoding="async"' if lazy else (' fetchpriority="high"' if priority else '')
    return (f'<picture{" class=%s" % chr(34)+cls+chr(34) if cls else ""}>'
            f'<source type="image/webp" srcset="/img/{s}/{n}-600.webp {dims(s,n,600)[0]}w, /img/{s}/{n}-1200.webp {w}w" sizes="{sizes}">'
            f'<img src="/img/{s}/{n}-1200.jpg" alt="{e(im["alt"])}" {attrs}></picture>')

def is_free(p):
    return bool(p.get("free") or float(p["price"]) == 0)

def price(p):
    if is_free(p):
        return "Free"
    return "$" + (p["price"][:-3] if p["price"].endswith(".00") else p["price"])

def buy_label(p):
    return "Get it free" if is_free(p) else "Buy on Payhip"

def price_html(p, show_currency=True):
    if is_free(p) or not show_currency:
        return f'<p class="price">{price(p)}</p>'
    return f'<p class="price">{price(p)} <span>USD</span></p>'

# ---------- shared chrome ----------
def head(title, desc, path, og_image, og_alt, og_type="website", jsonld=()):
    url = SITE + path
    ld = "".join(f'\n<script type="application/ld+json">{json.dumps(j, ensure_ascii=False, separators=(",", ":"))}</script>' for j in jsonld)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Frondworks">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og_image}">
<meta property="og:image:alt" content="{e(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{SITE}{og_image}">
<meta name="theme-color" content="#1f4d3a">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/site.css">{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="/">Frondworks</a>
    <nav aria-label="Main">
      <a href="/#products">Products</a>
      <a href="/guides/">Guides</a>
      <a href="/#faq">FAQ</a>
      <a href="/#contact">Contact</a>
      <a class="nav-shop" href="{SHOP}">Shop</a>
    </nav>
  </div>
</header>
'''

def footer():
    links = "\n".join(f'        <li><a href="/{p["slug"]}/">{e(p["name"])}</a></li>' for p in products)
    return f'''<footer class="site-footer">
  <div class="wrap foot">
    <div>
      <p class="brand">Frondworks</p>
      <p>Practical printables and spreadsheets for money, planning, and goals.</p>
    </div>
    <div>
      <h2>Products</h2>
      <ul>
{links}
        <li><a href="{SHOP}">Full shop on Payhip</a></li>
      </ul>
    </div>
    <div>
      <h2>Help</h2>
      <ul>
        <li><a href="/#faq">FAQ</a></li>
        <li><a href="/guides/">Guides</a></li>
        <li><a href="/#contact">Contact form</a></li>
        <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
      </ul>
    </div>
  </div>
  <div class="wrap legal">&copy; 2026 Frondworks</div>
</footer>
<script src="/assets/site.js" defer></script>
</body>
</html>
'''

def product_ld(p):
    return {
        "@context": "https://schema.org", "@type": "Product",
        "name": p["name"], "description": p["meta_description"],
        "url": f"{SITE}/{p['slug']}/",
        "image": [f"{SITE}/img/{p['slug']}/{im['name']}-1200.jpg" for im in p["images"]],
        "brand": {"@type": "Brand", "name": "Frondworks"},
        "offers": {"@type": "Offer", "price": p["price"], "priceCurrency": p["currency"],
                   "availability": "https://schema.org/InStock", "url": p["buy_url"],
                   "seller": {"@type": "Organization", "name": "Frondworks"}},
    }

# ---------- contact form (hand-kept; must match worker/lead-form.js) ----------
FORM = open(os.path.join(ROOT, "_build", "contact-form.html")).read().rstrip()

FAQ = [
    ("How do I get my files?", "Checkout is handled by Payhip. After you pay, you get an instant download of a zip file. No physical item is shipped."),
    ("What formats are the files?", "The Money Planner and Bill Audit are Excel workbooks that also work in Google Sheets, with instructions PDFs. The Goal-Setting Kit and Christmas and Holiday Planner are printable PDFs in US Letter and A4. The Monthly and Weekly Planner includes four PDFs: US Letter and A4, in Sunday start and Monday start editions. The Budget Binder is a 28-page printable PDF in US Letter and A4. The Holiday Gift List and Budget Tracker is a free two-page printable PDF in US Letter and A4. The Gift Card Holders and DIY Gift Coupons pack is a 15-page printable PDF in US Letter and A4. The Printable Christmas Gift Tags pack is a free 7-page printable PDF in US Letter and A4. The Valentine's Day Printables Pack is a 14-page printable PDF in US Letter and A4. The Debt Payoff Planner is a 15-page printable PDF in US Letter and A4. The Meal Planner and Grocery List is a 14-page printable PDF in US Letter and A4. The 2027 Printable Calendar is a free 13-page printable PDF in four editions: US Letter and A4, Sunday start and Monday start. The 2027 Fresh Start Bundle includes the Money Planner, the Bill Audit, and the Goal-Setting Kit in one purchase. The 2027 Complete Printables Collection includes nine paid products in one purchase."),
    ("What is in the 2027 Fresh Start Bundle?", "It includes the 2027 Fresh Start Money Planner ($9), the Subscription and Recurring Bill Audit ($7), and the 2027 New Year Goal-Setting Kit ($4.99). Bought separately they are $20.99. The bundle is $14.99, so you save $6 versus buying them separately."),
    ("What is in the 2027 Complete Printables Collection?", "It includes nine paid products: the 2027 Fresh Start Money Planner ($9), the Subscription and Recurring Bill Audit ($7), the 2027 New Year Goal-Setting Kit ($4.99), the 2026 Christmas and Holiday Planner ($4.99), the 2027 Monthly and Weekly Planner ($4.99), the 2027 Budget Binder ($6.99), the Printable Gift Card Holders and DIY Gift Coupons ($4.99), the 2027 Debt Payoff Planner ($4.99), and the 2027 Meal Planner and Grocery List ($4.99). Bought separately they are $52.93. The collection is $19.99, so you save $32.94 versus buying them separately."),
    ("Can I share or resell the files?", "No. Each product is licensed for personal use: you may use, edit, and print it for yourself and your household. Please do not resell, share, or redistribute the files. The terms are included in each download."),
    ("Do the spreadsheets connect to my bank?", "No. You type the numbers. The spreadsheets do not connect to your bank or send reminders, and they use no macros."),
    ("Is this financial advice?", "No. These are planning tools, not financial advice."),
    ("I need help with a download.", f'Email <a href="mailto:{EMAIL}">{EMAIL}</a> or use the contact form below.'),
]

# ---------- home ----------
def feature(p):
    img = picture(p, p["images"][0], "(min-width: 800px) 55vw, 92vw", lazy=False, priority=True)
    names = [e(by_slug(s)["name"]) for s in p["includes"]]
    if len(names) == 1:
        included = names[0]
    elif len(names) == 2:
        included = f"{names[0]} and {names[1]}"
    elif len(names) > 3:
        included = f"{count_word(len(names)).capitalize()} printables and spreadsheets"
    else:
        included = ", ".join(names[:-1]) + ", and " + names[-1]
    return f'''      <article class="feature" id="{e(p["slug"])}">
        <a class="feature-img" href="/{p["slug"]}/" tabindex="-1" aria-hidden="true">{img}</a>
        <div class="feature-body">
          <p class="fmt">Bundle</p>
          <h3><a href="/{p["slug"]}/">{e(p["name"])}</a></h3>
          <p>{included} in one purchase.</p>
          <p class="price">{price(p)} <span>USD</span></p>
          <p class="compare">{compare_line(p)}</p>
          <div class="actions">
            <a class="btn" href="{p["buy_url"]}">{buy_label(p)}<span class="sr">, {e(p["name"])}</span></a>
            <a class="btn ghost" href="/{p["slug"]}/">Details<span class="sr">, {e(p["name"])}</span></a>
          </div>
        </div>
      </article>'''

def card(p, i):
    return f'''      <li class="card">
        <a class="card-img" href="/{p["slug"]}/" tabindex="-1" aria-hidden="true">{picture(p, p["images"][0], "(min-width: 900px) 360px, (min-width: 600px) 45vw, 92vw", lazy=i > 0)}</a>
        <div class="card-body">
          <h3><a href="/{p["slug"]}/">{e(p["name"])}</a></h3>
          <p class="fmt">{e(p["format"])}</p>
          <p>{e(p["card_blurb"])}</p>
          <p class="price">{price(p)}</p>
          <div class="actions">
            <a class="btn" href="{p["buy_url"]}">{buy_label(p)}<span class="sr">, {e(p["name"])}</span></a>
            <a class="btn ghost" href="/{p["slug"]}/">Details<span class="sr">, {e(p["name"])}</span></a>
          </div>
        </div>
      </li>'''

def build_home():
    title = "Frondworks: Printables and Spreadsheets for Money, Planning, and Goals"
    desc = "Practical printables and spreadsheets for money, planning, and goals, including the 2027 Fresh Start Bundle of the money planner, bill audit, and goal kit. Instant download."
    org = {"@context": "https://schema.org", "@type": "Organization", "name": "Frondworks", "url": SITE + "/",
           "email": EMAIL, "sameAs": [SHOP]}
    site = {"@context": "https://schema.org", "@type": "WebSite", "name": "Frondworks", "url": SITE + "/"}
    items = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/{p['slug']}/", "name": p["name"]} for i, p in enumerate(products)]}
    faq = "\n".join(f'''      <details>
        <summary>{e(q)}</summary>
        <p>{a}</p>
      </details>''' for q, a in FAQ)
    cards = "\n".join(card(p, i) for i, p in enumerate(singles()))
    featured = "\n".join(feature(p) for p in bundles())
    home_guides = "\n".join(
        "        <li>\n"
        f'          <h3><a href="/guides/{g["slug"]}/">{e(g["h1"])}</a></h3>\n'
        f'          <p>{e(g["summary"])}</p>\n'
        "        </li>"
        for g in guides
    )
    out = head(title, desc, "/", "/img/og-home.jpg", "Frondworks product previews", jsonld=(org, site, items)) + f'''<main id="main">
  <section class="hero">
    <div class="wrap">
      <h1>Practical printables and spreadsheets for money, planning, and goals.</h1>
      <p class="lede">Digital downloads for Excel, Google Sheets, and home printing. Buy on Payhip and download right away.</p>
      <p><a class="btn" href="#products">See the products</a> <a class="btn ghost" href="{SHOP}">Visit the full shop</a></p>
    </div>
  </section>

  <section id="products" class="section" aria-labelledby="products-h">
    <div class="wrap">
      <h2 id="products-h">Products</h2>
      <div class="features">
{featured}
      </div>
      <h3 class="grid-h">Individual products</h3>
      <ul class="grid">
{cards}
      </ul>
      <p class="more"><a href="{SHOP}">See everything in the full Frondworks shop on Payhip</a></p>
    </div>
  </section>

  <section id="guides" class="section" aria-labelledby="guides-h">
    <div class="wrap narrow">
      <h2 id="guides-h">Guides</h2>
      <p>Short, practical how-tos for planning and everyday money tasks.</p>
      <ul class="guide-list">
{home_guides}
      </ul>
      <p class="more"><a href="/guides/">All guides</a></p>
    </div>
  </section>

  <section id="about" class="section alt" aria-labelledby="about-h">
    <div class="wrap narrow">
      <h2 id="about-h">About</h2>
      <p>Frondworks makes practical digital downloads: spreadsheets for Excel and Google Sheets and printable PDFs for planning your money, your year, and your goals. You type your own numbers, and nothing connects to your bank.</p>
    </div>
  </section>

  <section id="faq" class="section" aria-labelledby="faq-h">
    <div class="wrap narrow">
      <h2 id="faq-h">FAQ</h2>
{faq}
    </div>
  </section>

  <section id="contact" class="section alt" aria-labelledby="contact-h">
    <div class="wrap contact">
      <div>
        <h2 id="contact-h">Contact</h2>
        <p>Questions about a product or a download? Send a note here, or email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
      </div>
      <div class="form-card">
{FORM}
      </div>
    </div>
  </section>
</main>
''' + footer()
    write("index.html", out)

# ---------- landing pages ----------
def callout_label(b):
    return f"Get all {count_word(len(b['includes']))} in the {e(b['name'])} for {price(b)}"

def callout(b):
    return f'      <p class="callout"><a href="/{b["slug"]}/">{callout_label(b)}</a>. {compare_line(b)}</p>'

def related_callouts(p):
    bundled = bundles_for(p)
    bits = []
    if len(bundled) > 1:
        bundled = sorted(bundled, key=lambda b: -len(b.get("includes", [])))
        first, rest = bundled[0], bundled[1:]
        parts = [f'<a href="/{first["slug"]}/">{callout_label(first)}</a>. {compare_line(first)}']
        for b in rest:
            names = [by_slug(s)["name"] for s in b["includes"]]
            if b["slug"] == "bundle":
                short = "the Money Planner, the Bill Audit, and the Goal-Setting Kit"
            elif len(names) == 3:
                short = f"the {names[0]}, the {names[1]}, and the {names[2]}"
            else:
                short = "those products"
            parts.append(f'Or get {e(short)} in the <a href="/{b["slug"]}/">{e(b["name"])}</a> for {price(b)}.')
        bits.append("      <p class=\"callout\">" + " ".join(parts) + "</p>")
    else:
        bits.extend(callout(b) for b in bundled)
    for r in p.get("related", []):
        other = by_slug(r["slug"])
        bits.append(f'      <p class="callout"><a href="/{other["slug"]}/">{e(r["text"])}</a></p>')
    if is_free(p):
        bits.insert(0, '      <p class="compare">This download is free. Pay what you want is optional.</p>')
    return "\n".join(bits)


def product_faq_html(p):
    items = p.get("faq") or []
    if not items:
        return ""
    body = "\n".join(
        "      <details>\n"
        "        <summary>" + e(q) + "</summary>\n"
        "        <p>" + e(a) + "</p>\n"
        "      </details>"
        for q, a in items
    )
    return "      <h2 id=\"product-faq\">FAQ</h2>\n" + body + "\n"


def faq_ld(p):
    items = p.get("faq") or []
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in items
        ],
    }


def build_product(p):
    others = [o for o in products if o is not p]
    title = p.get("page_title") or f'{p["name"]} | Frondworks'
    gallery_items = list(p["images"])
    if is_bundle(p):
        nword = count_word(len(p["includes"]))
        inside = "\n".join(
            f'        <li><a href="/{by_slug(s)["slug"]}/">{e(by_slug(s)["name"])}</a>, {price(by_slug(s))}. {e(by_slug(s)["card_blurb"])}</li>'
            for s in p["includes"]
        )
        compare = f'      <p class="compare">{price(p)} for all {nword}. {compare_line(p)}</p>'
        buy_extra = compare
        mid_callout = ""
        if any(im["name"] == "together" for im in gallery_items):
            # Combined composite first, then the first preview of each included product.
            hero = next(im for im in gallery_items if im["name"] == "together")
            extra = [(by_slug(s), by_slug(s)["images"][0]) for s in p["includes"]]
            gallery = "\n".join(
                [f'        <li class="hero-shot"><a href="/img/{p["slug"]}/{hero["name"]}-1200.jpg">{picture(p, hero, "(min-width: 900px) 1120px, 92vw", lazy=False, priority=True)}</a></li>']
                + [f'        <li><a href="/{inc["slug"]}/">{picture(inc, im, "(min-width: 900px) 33vw, 92vw", lazy=True)}</a></li>'
                   for inc, im in extra]
            )
            gallery_class = " gallery wide-first"
        else:
            gallery = "\n".join(
                f'        <li{" class=\"hero-shot\"" if i == 0 and len(gallery_items) > 1 else ""}><a href="/img/{p["slug"]}/{im["name"]}-1200.jpg">{picture(p, im, "(min-width: 900px) 1120px, 92vw" if i == 0 else "(min-width: 900px) 33vw, 92vw", lazy=i > 0, priority=(i == 0))}</a></li>'
                for i, im in enumerate(gallery_items)
            )
            gallery_class = " gallery wide-first" if len(gallery_items) > 1 else ""
    else:
        gallery = "\n".join(f'        <li><a href="/img/{p["slug"]}/{im["name"]}-1200.jpg">{picture(p, im, "(min-width: 900px) 33vw, 92vw", lazy=i > 0, priority=(i == 0))}</a></li>' for i, im in enumerate(gallery_items))
        gallery_class = ""
        inside = "\n".join(f"        <li>{x}</li>" for x in p["inside"])
        mid_callout = related_callouts(p)
        buy_extra = mid_callout
    intro = "\n".join(f"      <p>{e(x)}</p>" for x in p["intro"])
    details = "\n".join(f"      <p>{e(x)}</p>" for x in p["details"])
    other = "\n".join(f'        <li><a href="/{o["slug"]}/">{e(o["name"])}</a>, {price(o)}</li>' for o in others)
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Frondworks", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": p["name"], "item": f"{SITE}/{p['slug']}/"}]}
    out = head(title, p["meta_description"], f'/{p["slug"]}/', f'/img/{p["slug"]}/{p["images"][0]["name"]}-1200.jpg',
               p["images"][0]["alt"], og_type="product", jsonld=tuple(j for j in (product_ld(p), crumbs, faq_ld(p)) if j)) + f'''<main id="main">
  <section class="section product">
    <div class="wrap">
      <p class="crumbs"><a href="/">Home</a> <span aria-hidden="true">/</span> <a href="/#products">Products</a></p>
      <h1>{e(p.get("h1") or p["name"])}</h1>
      <p class="lede">{e(p["subtitle"])}</p>
      <div class="buy">
        {price_html(p)}
        <a class="btn big" href="{p["buy_url"]}">{buy_label(p)}</a>
      </div>
{buy_extra}
      <ul class="gallery{gallery_class}" aria-label="Preview images">
{gallery}
      </ul>
    </div>
    <div class="wrap narrow desc">
      <h2>{e(p["tagline"])}</h2>
{intro}
      <h3>{e(p["inside_heading"])}</h3>
      <ul class="ticks">
{inside}
      </ul>
{details}
{mid_callout}
{guide_callouts(p)}
      <div class="buy">
        {price_html(p)}
        <a class="btn big" href="{p["buy_url"]}">{buy_label(p)}</a>
      </div>
{product_faq_html(p)}
      <p>Questions? See the <a href="/#faq">FAQ</a> or email <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
      <h2 class="small">More from Frondworks</h2>
      <ul>
{other}
        <li><a href="{SHOP}">The full shop on Payhip</a></li>
      </ul>
    </div>
  </section>
</main>
''' + footer()
    write(f'{p["slug"]}/index.html', out)


def guide_callouts(p):
    bits = []
    for g in guides:
        if p["slug"] in g.get("products", []):
            bits.append(f'      <p class="callout"><a href="/guides/{g["slug"]}/">A short guide: {e(g["h1"])}</a></p>')
    return "\n".join(bits)


def article_ld(g):
    url = f"{SITE}/guides/{g['slug']}/"
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": g["h1"],
        "description": g["meta_description"],
        "datePublished": g["date"],
        "dateModified": g["date"],
        "author": {"@type": "Organization", "name": "Frondworks", "url": SITE + "/"},
        "publisher": {"@type": "Organization", "name": "Frondworks", "url": SITE + "/"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "image": SITE + g["og_image"],
    }


def build_guides_index():
    title = "Guides | Frondworks"
    desc = "Short, practical how-tos from Frondworks for holiday gift budgets, debt payoff order, and reviewing recurring subscriptions."
    crumbs = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Frondworks", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": SITE + "/guides/"},
        ],
    }
    items = "\n".join(
        "        <li>\n"
        f'          <h2><a href="/guides/{g["slug"]}/">{e(g["h1"])}</a></h2>\n'
        f'          <p>{e(g["summary"])}</p>\n'
        "        </li>"
        for g in guides
    )
    out = head(title, desc, "/guides/", "/img/og-home.jpg", "Frondworks product previews", jsonld=(crumbs,)) + f'''<main id="main">
  <section class="section">
    <div class="wrap narrow">
      <p class="crumbs"><a href="/">Home</a> <span aria-hidden="true">/</span> Guides</p>
      <h1>Guides</h1>
      <p class="lede">Short, practical how-tos for planning and everyday money tasks. No jargon, and no promised results.</p>
      <ul class="guide-list">
{items}
      </ul>
    </div>
  </section>
</main>
''' + footer()
    write("guides/index.html", out)


def build_guide(g):
    body = open(os.path.join(ROOT, "_build", "guides", g["file"])).read().strip()
    others = "\n".join(
        f'        <li><a href="/guides/{o["slug"]}/">{e(o["h1"])}</a></li>'
        for o in guides if o is not g
    )
    crumbs = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Frondworks", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": SITE + "/guides/"},
            {"@type": "ListItem", "position": 3, "name": g["h1"], "item": f"{SITE}/guides/{g['slug']}/"},
        ],
    }
    year, month, day = g["date"].split("-")
    months = "January February March April May June July August September October November December".split()
    published = f"{months[int(month)-1]} {int(day)}, {year}"
    out = head(g["title"], g["meta_description"], f"/guides/{g['slug']}/", g["og_image"], g["og_alt"],
               og_type="article", jsonld=(article_ld(g), crumbs)) + f'''<main id="main">
  <section class="section">
    <div class="wrap narrow article">
      <p class="crumbs"><a href="/">Home</a> <span aria-hidden="true">/</span> <a href="/guides/">Guides</a> <span aria-hidden="true">/</span> {e(g["h1"])}</p>
      <h1>{e(g["h1"])}</h1>
      <p class="guide-date">Published {e(published)}</p>
{body}
      <h2 class="small">More guides</h2>
      <ul>
{others}
        <li><a href="/guides/">All guides</a></li>
      </ul>
    </div>
  </section>
</main>
''' + footer()
    write(f'guides/{g["slug"]}/index.html', out)


def build_sitemap():
    urls = ["/"] + [f'/{p["slug"]}/' for p in products] + ["/guides/"] + [f'/guides/{g["slug"]}/' for g in guides]
    body = "\n".join(f"  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n  </url>" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n')

def write(rel, text):
    path = os.path.join(ROOT, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    bad = re.findall(r"\u2014|\u2013|&mdash;|&ndash;|&#8212;|&#8211;", text)
    if bad: sys.exit(f"dash found in {rel}: {bad}")
    open(path, "w").write(text)
    print("wrote", rel)

if __name__ == "__main__":
    if "--images" in sys.argv:
        make_images(sys.argv[sys.argv.index("--images") + 1])
    for p in products:
        attach_together(p)
    build_home()
    for p in products: build_product(p)
    build_guides_index()
    for g in guides:
        build_guide(g)
    build_sitemap()
