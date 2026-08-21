# -*- coding: utf-8 -*-
import io, re, sys, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'd:\AI\trae work\行业调研分析\pharma-publish\reports\companies'
exclude = ('companies-index', 'pharma-chain', '_', 'wangshi', 'bimap')
names = sys.argv[1:] or sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(BASE, '*.html')) if not os.path.basename(p).startswith(exclude))
ok = True
for name in names:
    p = os.path.join(BASE, '%s.html' % name)
    if not os.path.exists(p):
        print('MISSING PAGE:', name); ok = False; continue
    h = open(p, encoding='utf-8').read()
    ph = re.findall(r'\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)*\b', h)
    bad = sorted(set(t for t in ph if t.startswith(('KPI_','FIN_','FC_','TLDR_','VERDICT_','TIMING_','SRC_','VAL_','HIST_','GROWTH_','SOURCE_','CONFIDENCE','FUND_','COMPANY','SECTOR_DESC','CHAIN_ANCHOR','COMPANIES_LINK','CATALYSTS','RISKS','MOAT','PRICEIN','POTENTIAL','BLURB'))))
    for t in bad:
        print(name, '-> leftover', t); ok = False
    if 'id="s12"' not in h:
        print(name, '-> missing s12'); ok = False
print('=> ALL CLEAN' if ok else '=> ISSUES FOUND')