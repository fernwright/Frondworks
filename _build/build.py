#!/usr/bin/env python3
"""Build the Frondworks storefront from _build/products.json.

Adding a product = add one entry to products.json, then run:
    python3 _build/build.py --images /path/to/preview/root   (once, to make WebP/JPG previews)
    python3 _build/build.py                                  (regenerates every page)

Generates: index.html, <slug>/index.html for each product, sitemap.xml,
and img/<slug>/*. Hand-kept files: CNAME, plumbers.html (archived), the
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
e = html.escape

# ---------- images ----------
def make_images(src_root):
    from PIL import Image
    for p in products:
        d = os.path.join(ROOT, "img", p["slug"]); os.makedirs(d, exist_ok=True)
        for im in p["images"]:
            img = Image.open(os.path.join(src_root, im["src"])).convert("RGB")
            for size in (1200, 600):
                c = img.copy(); c.thumbnail((size, size), Image.LANCZOS)
                c.save(os.path.join(d, f'{im["name"]}-{size}.webp'), "WEBP", quality=80, method=6)
                if size == 1200:
                    c.save(os.path.join(d, f'{im["name"]}-1200.jpg'), "JPEG", quality=78, optimize=True, progressive=True)
    # home share image: the three covers on a neutral background
    W, H = 1200, 630
    og = Image.new("RGB", (W, H), (244, 242, 236))
    x = 60
    for p in products:
        img = Image.open(os.path.join(src_root, p["images"][0]["src"])).convert("RGB")
        img.thumbnail((340, 510), Image.LANCZOS)
        og.paste(img, (x + (340 - img.width) // 2, (H - img.height) // 2)); x += 370
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

def price(p): return "$" + (p["price"][:-3] if p["price"].endswith(".00") else p["price"])

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
    ("How do I get my files?", f"Checkout is handled by Payhip. After you pay, you get an instant download of a zip file. No physical item is shipped."),
    ("What formats are the files?", "The Money Planner is an Excel workbook that also works in Google Sheets, with an instructions PDF. The Bill Audit comes as two Excel workbooks (a fictional sample and a blank copy) for Excel and Google Sheets, with an instructions PDF. The Goal-Setting Kit is two printable PDFs, one US Letter and one A4."),
    ("Can I share or resell the files?", "No. Each product is licensed for personal use: you may use, edit, and print it for yourself and your household. Please do not resell, share, or redistribute the files. The terms are included in each download."),
    ("Do the spreadsheets connect to my bank?", "No. You type the numbers. The spreadsheets do not connect to your bank or send reminders, and they use no macros."),
    ("Is this financial advice?", "No. These are planning tools, not financial advice."),
    ("I need help with a download.", f'Email <a href="mailto:{EMAIL}">{EMAIL}</a> or use the contact form below.'),
]

# ---------- home ----------
def card(p, i):
    return f'''      <li class="card">
        <a class="card-img" href="/{p["slug"]}/" tabindex="-1" aria-hidden="true">{picture(p, p["images"][0], "(min-width: 900px) 360px, (min-width: 600px) 45vw, 92vw", lazy=i > 0)}</a>
        <div class="card-body">
          <h3><a href="/{p["slug"]}/">{e(p["name"])}</a></h3>
          <p class="fmt">{e(p["format"])}</p>
          <p>{e(p["card_blurb"])}</p>
          <p class="price">{price(p)}</p>
          <div class="actions">
            <a class="btn" href="{p["buy_url"]}">Buy on Payhip<span class="sr">, {e(p["name"])}</span></a>
            <a class="btn ghost" href="/{p["slug"]}/">Details<span class="sr">, {e(p["name"])}</span></a>
          </div>
        </div>
      </li>'''

def build_home():
    title = "Frondworks: Printables and Spreadsheets for Money, Planning, and Goals"
    desc = "Printables and spreadsheets for money, planning, and goals: a 2027 money planner, a subscription and bill audit, and a goal-setting kit. Instant download."
    org = {"@context": "https://schema.org", "@type": "Organization", "name": "Frondworks", "url": SITE + "/",
           "email": EMAIL, "sameAs": [SHOP]}
    site = {"@context": "https://schema.org", "@type": "WebSite", "name": "Frondworks", "url": SITE + "/"}
    items = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/{p['slug']}/", "name": p["name"]} for i, p in enumerate(products)]}
    faq = "\n".join(f'''      <details>
        <summary>{e(q)}</summary>
        <p>{a}</p>
      </details>''' for q, a in FAQ)
    cards = "\n".join(card(p, i) for i, p in enumerate(products))
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
      <ul class="grid">
{cards}
      </ul>
      <p class="more"><a href="{SHOP}">See everything in the full Frondworks shop on Payhip</a></p>
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
def build_product(p):
    others = [o for o in products if o is not p]
    title = f'{p["name"]} | Frondworks'
    gallery = "\n".join(f'        <li><a href="/img/{p["slug"]}/{im["name"]}-1200.jpg">{picture(p, im, "(min-width: 900px) 33vw, 92vw", lazy=i > 0, priority=(i == 0))}</a></li>' for i, im in enumerate(p["images"]))
    inside = "\n".join(f"        <li>{x}</li>" for x in p["inside"])
    intro = "\n".join(f"      <p>{e(x)}</p>" for x in p["intro"])
    details = "\n".join(f"      <p>{e(x)}</p>" for x in p["details"])
    other = "\n".join(f'        <li><a href="/{o["slug"]}/">{e(o["name"])}</a>, {price(o)}</li>' for o in others)
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Frondworks", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": p["name"], "item": f"{SITE}/{p['slug']}/"}]}
    out = head(title, p["meta_description"], f'/{p["slug"]}/', f'/img/{p["slug"]}/{p["images"][0]["name"]}-1200.jpg',
               p["images"][0]["alt"], og_type="product", jsonld=(product_ld(p), crumbs)) + f'''<main id="main">
  <section class="section product">
    <div class="wrap">
      <p class="crumbs"><a href="/">Home</a> <span aria-hidden="true">/</span> <a href="/#products">Products</a></p>
      <h1>{e(p["name"])}</h1>
      <p class="lede">{e(p["subtitle"])}</p>
      <div class="buy">
        <p class="price">{price(p)} <span>USD</span></p>
        <a class="btn big" href="{p["buy_url"]}">Buy on Payhip</a>
      </div>
      <ul class="gallery" aria-label="Preview images">
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
      <div class="buy">
        <p class="price">{price(p)} <span>USD</span></p>
        <a class="btn big" href="{p["buy_url"]}">Buy on Payhip</a>
      </div>
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

def build_sitemap():
    urls = ["/"] + [f'/{p["slug"]}/' for p in products]
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
    build_home()
    for p in products: build_product(p)
    build_sitemap()
