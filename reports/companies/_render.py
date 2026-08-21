# -*- coding: utf-8 -*-
"""Render single-company 12-dimension HTML pages.
Reads metadata from companies.json + research content from company_data/<slug>.py.
Usage: python _render.py            # all companies with a data file
       python _render.py hengrui    # just one/all listed slugs
"""
import io, re, sys, os, glob, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(BASE, '_company_template.html')
OUTDIR = BASE                              # rendered pages sit beside template
CMP_JSON = os.path.join(BASE, 'companies.json')
DATA_DIR = os.path.join(BASE, 'company_data')
INDEX_LINK = 'companies-index.html'
CHAIN_FILE = '../pharma-chain.html'

# ---------- metadata ----------
def load_meta():
    with open(CMP_JSON, encoding='utf-8') as f:
        cmp = json.load(f)
    sec_anchor = {s['key']: s['chainAnchor'] for s in cmp['sectors']}
    companies = [c for c in cmp['companies'] if not c.get('skip')]
    return sec_anchor, companies

def load_contents():
    out = {}
    for path in sorted(glob.glob(os.path.join(DATA_DIR, '*.py'))):
        slug = os.path.splitext(os.path.basename(path))[0]
        if slug.startswith('_'):
            continue
        try:
            ns = {}
            exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), ns)
            if 'D' in ns:
                out[slug] = ns['D']
        except Exception as e:
            print('[render] skip %s: %s' % (slug, e))
    return out

SEC_ANCHOR, METAS = load_meta()
CONTENTS = load_contents()
ORDER = [c['slug'] for c in METAS]

def meta_of(slug):
    for c in METAS:
        if c['slug'] == slug:
            return c
    return None

def prev_next(slug):
    i = ORDER.index(slug)
    prev = ORDER[i-1] if i > 0 else None
    nxt = ORDER[i+1] if i < len(ORDER)-1 else None
    def nm(s):
        m = meta_of(s)
        return m['name'] if m else s
    return (prev, nm(prev)) if prev else (None, ''), (nxt, nm(nxt)) if nxt else (None, '')

# ---------- template map ----------
TPL_MAP = [
    ('COMPANY', 'company'), ('CODE', 'code'), ('COMPANIES_LINK', lambda d: INDEX_LINK),
    ('CHAIN_ANCHOR', 'chain_anchor'), ('PREV_LINK', lambda d: d['prev'][0]+'.html'), ('NEXT_LINK', lambda d: d['next'][0]+'.html'),
    ('PREV', lambda d: d['prev'][1]), ('NEXT', lambda d: d['next'][1]),
]

def render(slug):
    m = meta_of(slug)
    d = dict(CONTENTS[slug])
    d['company'] = m['name'] if 'company' not in d else d['company']
    d['code'] = m['code'] if 'code' not in d else d['code']
    d.setdefault('title', d['company'] + ' · 12维度深度分析 · 2026.08')
    d.setdefault('chain_anchor', SEC_ANCHOR[m['sector']])
    (d['prev'], d['next']) = prev_next(slug)

    tpl = open(TPL, encoding='utf-8').read()
    # title / sidebar / header
    tpl = tpl.replace('<title>COMPANY · 12维度深度分析 · 2026.08</title>', '<title>'+d['title']+'</title>')
    tpl = tpl.replace('>COMPANY<br>', '>'+d['company']+'<br>')
    tpl = tpl.replace('<div class="sidebar-sub">数据截至 2026.08.20</div>', '<div class="sidebar-sub">{0}</div>'.format(d['sidebar_sub']))
    tpl = tpl.replace('<h1>COMPANY<span class="code">CODE</span></h1>', '<h1>'+d['company']+'<span class="code">'+d['code']+'</span></h1>')
    tpl = tpl.replace('<p class="subtitle">SECTOR_DESC</p>', '<p class="subtitle">'+d['sector_desc']+'</p>')
    tpl = tpl.replace('pharma-chain.html#CHAIN_ANCHOR', CHAIN_FILE+'#'+d['chain_anchor'])
    p, n = d['prev'], d['next']
    tpl = tpl.replace('href="PREV_LINK"', 'href="'+p[0]+'.html"' if p[0] else '')
    tpl = tpl.replace('href="NEXT_LINK"', 'href="'+n[0]+'.html"' if n[0] else '')
    tpl = tpl.replace('上一家 · PREV', '上一家 · '+p[1] if p[0] else '上一家')
    tpl = tpl.replace('下一家 · NEXT', '下一家 · '+n[1] if n[0] else '下一家')
    # kpi
    k = d['kpi']
    tpl = tpl.replace('>KPI_MCAP</div>', '>'+k['mcap']+'</div>').replace('KPI_MCAP_DATE', k['mcap_date'])
    tpl = tpl.replace('>KPI_PE</div>', '>'+k['pe']+'</div>').replace('KPI_PE_DATE', k['pe_date'])
    tpl = tpl.replace('>KPI_PCT</div>', '>'+k['pct']+'</div>').replace('KPI_PE_MED', k['pe_med'])
    tpl = tpl.replace('>KPI_26G</div>', '>'+k['g26']+'</div>').replace('KPI_26G_NOTE', k['g26_note'])
    # tldr
    t = d['tldr']
    for key in ['pitch','fund','val','pricein','watch','scen']:
        tpl = tpl.replace('TLDR_'+key.upper(), t[key])
    tpl = tpl.replace('COMPANY_BLURB', d['blurb'])
    # fin table
    f = d['fin']
    for i, name in enumerate(['rev','ni','core','gm','roe','ocf']):
        col = f.get(name, [])
        for j, ph in enumerate(['_23','_24','_25','_26E','_27E']):
            v = col[j] if j < len(col) else '—'
            tpl = tpl.replace('FIN_'+name.upper()+ph, str(v))
    tpl = tpl.replace('FUND_BUSINESS', d['fund_business'])
    tpl = tpl.replace('FUND_SPLIT', d['fund_split'])
    # val rows
    vr = ''.join('<tr><td>%s</td><td><strong>%s</strong></td><td>%s</td></tr>' % (a,b,c) for a,b,c in d['val_rows'])
    tpl = tpl.replace('VAL_ROWS', vr)
    tpl = tpl.replace('VAL_NOTE', d['val_note'])
    # hist
    hr = ''.join('<tr><td>%s</td><td><strong>%s</strong></td><td>%s</td></tr>' % (a,b,c) for a,b,c in d['hist_rows'])
    tpl = tpl.replace('HIST_ROWS', hr).replace('HIST_TAKE', d['hist_take'])
    # fc
    fc = d['fc']
    for i, name in enumerate(['rev','gm','ni','eps']):
        col = fc.get(name, [])
        for j, ph in enumerate(['_25A','_26E','_27E','_28E']):
            v = col[j] if j < len(col) else '—'
            tpl = tpl.replace('FC_'+name.upper()+ph, str(v))
    tpl = tpl.replace('FC_NOTE_OPTION_A', fc['note_a']).replace('FC_NOTE_MARKET', fc['note_market']).replace('FC_NOTE_AI', fc['note_ai'])
    # potential / growth / pricein / moat / catalysts / risks
    tpl = tpl.replace('POTENTIAL', d['potential'])
    gr = ''.join('<tr><td>%s</td><td><strong>%s</strong></td><td>%s</td></tr>' % (a,b,c) for a,b,c in d['growth_rows'])
    tpl = tpl.replace('GROWTH_ROWS', gr).replace('GROWTH_TAKE', d['growth_take'])
    tpl = tpl.replace('PRICEIN', d['pricein']).replace('MOAT', d['moat'])
    tpl = tpl.replace('CATALYSTS', d['catalysts']).replace('RISKS', d['risks'])
    # verdict
    v = d['verdict']
    tpl = tpl.replace('VERDICT_BULL_ASSUME', v['bull'][0]).replace('VERDICT_BULL_NI', v['bull'][1]).replace('VERDICT_BULL_MULT', v['bull'][2]).replace('VERDICT_BULL_PRICE', v['bull'][3])
    tpl = tpl.replace('VERDICT_BASE_ASSUME', v['base'][0]).replace('VERDICT_BASE_NI', v['base'][1]).replace('VERDICT_BASE_MULT', v['base'][2]).replace('VERDICT_BASE_PRICE', v['base'][3])
    tpl = tpl.replace('VERDICT_BEAR_ASSUME', v['bear'][0]).replace('VERDICT_BEAR_NI', v['bear'][1]).replace('VERDICT_BEAR_MULT', v['bear'][2]).replace('VERDICT_BEAR_PRICE', v['bear'][3])
    tpl = tpl.replace('VERDICT_RR', v['rr']).replace('VERDICT_FALSIFY', v['falsify'])
    # timing
    tm = d['timing']
    tpl = tpl.replace('TIMING_SECTOR', tm['sector']).replace('TIMING_VERDICT', tm['verdict']).replace('TIMING_BROKER', tm['broker'])
    tr = ''.join('<tr><td>%s</td><td>%s</td><td><strong>%s</strong></td></tr>' % (a,b,c) for a,b,c in tm['rows'])
    tpl = tpl.replace('TIMING_ROWS', tr)
    # src
    s = d['src']
    tpl = tpl.replace('SRC_T1', s['t1']).replace('SRC_T2', s['t2']).replace('SRC_T3', s['t3']).replace('SRC_T4', s['t4'])
    tpl = tpl.replace('CONFIDENCE', d['confidence'])
    src_list = '\n        '.join('<li>'+x+'</li>' for x in d['sources'])
    tpl = tpl.replace('SOURCE_LIST', src_list)
    tpl = tpl.replace('companies-index.html', INDEX_LINK)
    # drop leftover placeholders
    tpl = tpl.replace('href="COMPANIES_LINK"', 'href="'+INDEX_LINK+'"')
    tpl = re.sub(r'(PREV_LINK|NEXT_LINK|PREV|NEXT)','',tpl)
    return tpl

if __name__ == '__main__':
    os.makedirs(OUTDIR, exist_ok=True)
    targets = sys.argv[1:] if len(sys.argv) > 1 else [s for s in ORDER if s in CONTENTS]
    for slug in targets:
        if slug not in CONTENTS:
            print('skip unknown/not-yet-researched:', slug); continue
        out = os.path.join(OUTDIR, slug + '.html')
        html = render(slug)
        open(out, 'w', encoding='utf-8').write(html)
        print('wrote', os.path.basename(out), len(html.encode('utf-8')), 'bytes')