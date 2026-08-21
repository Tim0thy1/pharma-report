# -*- coding: utf-8 -*-
"""Inject hyperlinks into pharma-chain.html: company-card name -> companies/<slug>.html.
Also inject supporting CSS. Idempotent (skips already-linked)."""
import io, sys, os, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
CHAIN = os.path.join(os.path.dirname(BASE), 'pharma-chain.html')   # reports/pharma-chain.html
CMP = json.load(open(os.path.join(BASE, 'companies.json'), encoding='utf-8'))

# name -> slug, preferring non-skip
name2slug = {}
for c in CMP['companies']:
    if c.get('skip'):
        continue
    name2slug.setdefault(c['name'].split('/')[0].strip(), c['slug'])
    name2slug.setdefault(c['name'], c['slug'])

# aliases for parenthesized names used in the chain report
name2slug.update({
    '剂泰科技（Metis）': 'metis', '剂泰科技（metis）': 'metis', '剂泰科技': 'metis',
    '晶泰控股（晶泰科技）': 'xtalpi', '晶泰控股': 'xtalpi', '晶泰科技': 'xtalpi',
    '百图生科（BiMap）': 'bimap', '百图生科': 'bimap',
})

html = open(CHAIN, encoding='utf-8').read()
done_names = set()

# CSS to inject after the .company-card .card-name rule
css_block = ("\n.company-card .card-name a.card-link { color: inherit; text-decoration: none; }\n"
             ".company-card .card-name a.card-link:hover { color:#2563eb; text-decoration: underline; }\n"
             ".company-card .dlink { display:inline-block; margin-left:0.5rem; font-size:0.72rem; font-weight:600; "
             "color:#2563eb; background:#eff6ff; border:1px solid #bfdbfe; border-radius:4px; padding:0.05rem 0.45rem; "
             "text-decoration:none; vertical-align:middle; white-space:nowrap; }\n"
             ".company-card .dlink:hover { background:#dbeafe; }\n")

if css_block.strip() not in html:
    # insert right before the card-header background rule if present, else after the card-name rule
    anchor_search = ['.company-card .card-name', '.company-card .card-header', '.company-card {']
    anchor = next((a for a in anchor_search if a in html), None)
    if anchor:
        idx = html.index(anchor) + len(anchor)
        html = html[:idx] + css_block + html[idx:]

def link_for(name, slug):
    return ('<a class="card-link" href="companies/%s.html">%s</a>'
            '<a class="dlink" href="companies/%s.html" title="12维度深度分析(基本面/估值/投资时机/券商)">12维分析</a>' % (slug, name, slug))

def on_name(m):
    name = m.group(1).strip()
    slug = name2slug.get(name) or name2slug.get(name.split('/')[0].strip())
    if not slug:
        return m.group(0)
    done_names.add(name)
    return '<span class="card-name">' + link_for(name, slug) + '</span>'

# match card-name spans (handle our own injected ones are already not card-name-in-span anyway)
pattern = re.compile(r'<span class="card-name">([^<]*?)</span>', re.S)
html2, n = pattern.subn(on_name, html)

open(CHAIN, 'w', encoding='utf-8').write(html2)
linked = sorted(done_names)
print('linked companies:', len(linked), linked)
report_names = set(re.findall(r'<span class="card-name">([^<]*?)</span>', html))
print('remaining unlinked card-names in file:', sorted(n.strip() for n in report_names if n.strip() not in done_names))
print('bytes delta:', len(html2.encode('utf-8')) - len(html.encode('utf-8')))