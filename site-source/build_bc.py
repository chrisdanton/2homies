"""Turn the preview (src.html) into Big Cartel templates: new-layout.html + new-home.html."""
import re, json, html

REPO = '/Users/christinadanton/2homies'
IMG = 'https://chrisdanton.github.io/2homies/illo/site/'

src = open('src.html').read()
css = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
main = re.search(r'<main id="top">(.*?)</main>', src, re.S).group(1)

# ---- CSS ----
css = re.sub(r'@font-face \{[^}]*\}\n', '', css)          # layout already loads both fonts
css = re.sub(r'/\* Preview banner.*?\n\.preview-tag \{[^}]*\}\n', '', css, flags=re.S)

classes = set()
for m in re.finditer(r'class="([^"]+)"', src):
    classes.update(m.group(1).split())
classes.discard('preview-tag')
classes |= {'nav', 'nav-links', 'say', 'answer'}

def rename_css(text):
    return re.sub(r'\.([a-zA-Z][\w-]*)', lambda m: '.nh-' + m.group(1) if m.group(1) in classes else m.group(0), text)

css = rename_css(css)
VARS = r'(sun|paper|ink|line|red|green|purple|orange|blue|display|body)\b'
css = re.sub(r'--(?=' + VARS + ')', '--nh-', css)

fixes = [
    ('* { box-sizing: border-box; }\n', ''),
    ('html { scroll-behavior: smooth; }\n@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }\n', ''),
    ('body { background:', '.nh { background:'),
    ('img, video { max-width: 100%; height: auto; display: block; }',
     '.nh img, .nh video, .nh-nav img, .nh-footer img { max-width: 100%; height: auto; display: block; }'),
    ('a { color: inherit; }', '.nh a, .nh-nav a, .nh-footer a { color: inherit; }'),
    (':focus-visible {', '.nh :focus-visible, .nh-nav :focus-visible, .nh-footer :focus-visible {'),
    ('h1, h2, h3 { text-wrap: balance; margin: 0; }',
     '.nh h1, .nh h2, .nh h3 { text-wrap: balance; margin: 0; }\n.nh h3 { font-family: var(--nh-body); }'),
    ('\nh2 { font-family:', '\n.nh h2 { font-family:'),
    ('footer { background: var(--nh-ink);', '.nh-footer { border-top: 0; background: var(--nh-ink);'),
    ('footer .nh-wrap', '.nh-footer .nh-wrap'),
    ('footer img', '.nh-footer img'),
    ('footer .nh-say', '.nh-footer .nh-say'),
    ('footer nav a:hover', '.nh-footer nav a:hover'),
    ('footer nav a {', '.nh-footer nav a {'),
    ('footer nav {', '.nh-footer nav {'),
    ('.nh-btn { display: inline-flex;', '.nh-btn { font-family: inherit; cursor: pointer; display: inline-flex;'),
]
for a, b in fixes:
    assert css.count(a) >= 1, a
    css = css.replace(a, b)
assert not re.search(r'^(body|footer|h1|h2|img|a|html|\*)\b', css, re.M), 'unscoped element rule left'
css += """
/* Menu: cart link + shop button */
.nh-nav-right { display: flex; align-items: center; gap: 18px; }
.nh-nav-cart { font-weight: 600; font-size: 0.95rem; text-decoration: none; }
.nh-footer-legal { margin-top: 28px; font-size: 0.8rem; opacity: 0.55; }
"""

# ---- Home markup ----
def rename_markup(text):
    text = re.sub(r'class="([^"]+)"', lambda m: 'class="' + ' '.join('nh-' + c if c in classes else c for c in m.group(1).split()) + '"', text)
    return re.sub(r'--(?=' + VARS + ')', '--nh-', text)

main = rename_markup(main)
main = re.sub(r'src="img/([^"]+)"', lambda m: 'src="' + IMG + m.group(1) + '"', main)
main = re.sub(r'poster="img/([^"]+)"', lambda m: 'poster="' + IMG + m.group(1) + '"', main)
main = main.replace('href="https://2homies.com/about" target="_blank" rel="noopener"', 'href="/about"')
add = '<a class="nh-btn nh-btn-buy" href="https://2homies.com/#shop" target="_blank" rel="noopener">Add to cart · $35</a>'
assert main.count(add) == 1
main = main.replace(add, '<button class="nh-btn nh-btn-buy" type="button" onclick="Cart.addItem(477191019, 1, function(){ window.location.href=\'/cart\'; })">Add to cart · $35</button>')
main = main.replace('<section class="nh-band nh-buy" id="buy">', '<section class="nh-band nh-buy" id="buy">\n    <span id="shop"></span>')
assert 'img/' not in main.replace(IMG, '') and '2homies.com/#shop' not in main

d = json.load(open('faq.json'))
faqhtml = '\n'.join('<details id="q%d"><summary>%s</summary><div class="nh-answer">%s</div></details>' % (
    i + 1, html.escape(x['q']), ''.join('<p>%s</p>' % html.escape(p) for p in x['a'])) for i, x in enumerate(d))
main = main.replace('__FAQHTML__', faqhtml)
schema = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": x['q'], "acceptedAnswer": {"@type": "Answer", "text": " ".join(x['a'])}} for x in d]},
    {"@context": "https://schema.org", "@type": "Product", "name": "2Homies Calendar & Workbook",
     "brand": {"@type": "Brand", "name": "2Homies"},
     "description": "An undated, yearlong calendar and feelings workbook for kids ages 6 to 14 who live between two homes after separation or divorce. Includes a feelings wheel, star breathing, creative prompts and a sticker sheet.",
     "image": IMG + "hero.jpg",
     "offers": {"@type": "Offer", "price": "35.00", "priceCurrency": "USD", "availability": "https://schema.org/InStock",
                "url": "https://www.2homies.com/"}}]
home = '<div class="nh">\n' + main.strip('\n') + '\n</div>\n\n<script type="application/ld+json">' + json.dumps(schema).replace('</', '<\\/') + '</script>\n'
assert '__' not in home.replace('__nh', '')

# ---- Layout ----
lay = open(REPO + '/bc-layout.html').read()
old_title = re.search(r'<title>.*?</title>', lay).group(0)
lay = lay.replace(old_title, old_title.replace("{% if current_page == 'home' %}2 Homies Calendar",
                  "{% if current_page == 'home' %}2Homies | Calendar &amp; Workbook for Kids with Two Homes"))
lay = lay.replace('\n  </style>\n</head>', '\n\n/* ===== 2026-10 simpler homepage (all classes start with nh-) ===== */\n' + css.strip() + '\n  </style>\n</head>')

nav_old = lay[lay.find('  <div class="bar">'):lay.find('  {{ page_content }}')]
nav_new = '''  <header class="nh-nav">
    <div class="nh-wrap">
      <a href="/" aria-label="2Homies home"><img src="https://chrisdanton.github.io/2homies/logo.png" alt="2Homies"></a>
      <nav class="nh-nav-links" aria-label="Main">
        <a href="/#book">The book</a>
        <a href="/#peek">Peek inside</a>
        <a href="/about">Our story</a>
        <a href="/#questions">Good questions</a>
      </nav>
      <div class="nh-nav-right">
        <a href="/cart" class="nh-nav-cart">Cart{% if cart.item_count > 0 %} ({{ cart.item_count }}){% endif %}</a>
        <a class="nh-btn nh-btn-buy" href="/#buy">Shop · $35</a>
      </div>
    </div>
  </header>

'''
foot_old = lay[lay.find('  <footer>'):lay.find('</footer>') + len('</footer>')]
foot_new = '''  <footer class="nh-footer">
    <div class="nh-wrap">
      <img src="https://chrisdanton.github.io/2homies/logo.png" alt="2Homies">
      <p class="nh-say">You've got this.</p>
      <nav aria-label="Footer">
        <a href="/about">Our story</a>
        <a href="/#questions">Good questions</a>
        <a href="/contact">Contact</a>
        <a href="https://www.instagram.com/2HomeHomies/" target="_blank" rel="noopener">Instagram</a>
        <a href="/cart">Cart</a>
      </nav>
    </div>
    <div class="nh-wrap nh-footer-legal">&copy; 2026 2Homies. Made by moms. Illustrated by Maxine McCrann.</div>
  </footer>'''
assert nav_old and foot_old
lay = lay.replace(nav_old, nav_new).replace(foot_old, foot_new)

open('new-layout.html', 'w').write(lay)
open('new-home.html', 'w').write(home)
print('layout', len(lay), 'home', len(home))
