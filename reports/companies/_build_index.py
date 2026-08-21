# -*- coding: utf-8 -*-
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'companies-index.html')
CMP = json.load(open(os.path.join(BASE, 'companies.json'), encoding='utf-8'))

def tag_item(t):
    return {'real': ('real', '上市·核心'), 'story': ('story', '概念/前沿'), 'concept': ('concept', '未上市/边缘')}.get(t, ('real',''))

def badge(t):
    return '<span class="tag %s">%s</span>' % tag_item(t)

html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>产业链公司 · 12维度深度分析 · 索引</title><style>%s</style></head><body>
""" % open(os.path.join(BASE,'_index_style.css'), encoding='utf-8').read()

# sidebar
nav_items = ''
for i, sec in enumerate(CMP['sectors']):
    nav_items += '<a href="#%s"><span class="n">%02d</span>%s</a>' % (sec['key'], i+1, sec['name'])
nav_items += '<a href="../pharma-chain.html"><span class="n">→</span>回产业链报告</a>'

html += """
<div class="sidebar-wrap" id="sidebarWrap"><aside class="sidebar" id="sidebar">
  <div class="sidebar-head"><div class="sidebar-title">产业链公司深度分析<br><span style="font-size:0.72rem;font-weight:600;color:#64748b;">12 维度 · 全部公司索引</span></div></div>
  <nav class="sidebar-nav">%s</nav></aside><span class="sidebar-tab">目录</span></div>
<button class="sidebar-toggle" id="sidebarToggle">☰</button><div class="sidebar-mask" id="sidebarMask"></div>

<header><div class="container">
  <div class="crumb">← <a href="../pharma-chain.html#top">产业链研究报告</a></div>
  <h1>产业链公司 · 12 维度深度分析</h1>
  <p class="subtitle">按产业链环节分组，点击公司进入独立 12 维度深度分析（基本面/估值/盈利预测/投资时机/券商评价等）</p>
  <div class="meta"><span>共 %d 家公司</span><span>数据截至 2026.08</span>
  <span class="hl2"><span class="tag real">上市·核心</span><span class="tag story">概念/前沿</span><span class="tag concept">未上市/边缘</span></span></div>
</div></header>

<div class="container">
""" % (nav_items, len(CMP['companies']))

for sec in CMP['sectors']:
    comps = [c for c in CMP['companies'] if c['sector'] == sec['key'] and not c.get('skip')]
    if not comps:
        continue
    html += '<section class="sec" id="%s"><h2><span class="num">%02d</span>%s</h2><div class="grid">' % (sec['key'], sec['order'], sec['name'])
    for c in comps:
        done = os.path.exists(os.path.join(BASE, c['slug'] + '.html'))
        mark = '<span class="built">{0}</span>'.format('已出' if done else '制作中')
        html += '<a class="card" href="%s.html">%s%s<div class="nm">%s</div><div class="cd">%s</div></a>' % (
            c['slug'], badge(c['tag']), mark, c['name'], c['code'])
    html += '</div></section>'

html += """
  <div class="footer"><a href="../pharma-chain.html">← 返回产业链研究报告</a></div>
</div>
<script>%s</script>
</body></html>""" % open(os.path.join(BASE,'_index_script.js'), encoding='utf-8').read()

open(OUT, 'w', encoding='utf-8').write(html)
print('wrote', OUT, len(html.encode('utf-8')), 'bytes')