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

# ---------- tech data (ch13/ch14) ----------
TECH = {}
REG = {}
_tech_path = os.path.join(DATA_DIR, '_tech.json')
_reg_path = os.path.join(DATA_DIR, '_review_registry.json')
if os.path.exists(_tech_path):
    TECH = json.load(open(_tech_path, encoding='utf-8'))
if os.path.exists(_reg_path):
    REG = json.load(open(_reg_path, encoding='utf-8'))
# optional per-company qualitative text for ch13
TECH_TEXT_PATH = os.path.join(DATA_DIR, '_tech_text.py')
TECH_TEXT = {}
if os.path.exists(TECH_TEXT_PATH):
    try:
        _ns = {}
        exec(compile(open(TECH_TEXT_PATH, encoding='utf-8').read(), TECH_TEXT_PATH, 'exec'), _ns)
        TECH_TEXT = _ns.get('T', {})
    except Exception as e:
        print('[render] skip _tech_text.py:', e)

def _cls(v):
    return 'up' if v > 0 else ('down' if v < 0 else '')

def _fmt(x):
    return '—' if x is None else (('%.2f' % x) if isinstance(x, float) else str(x))

def _yi(x):
    """资金流(元)->亿元字符串"""
    if x is None: return '—'
    return ('%+.2f亿' % (x / 1e8))

def tech_block(slug):
    """返回 ch13+ch14 占位符替换字典。无技术数据的公司给降级文案。"""
    ph = {k: '' for k in ['TECH_DATE','SCORE','RATING','SCORE_BASIS','TREND_CLS','TECH_TREND','TECH_TREND_N',
        'MOM_CLS','TECH_MOM','TECH_MOM_N','CHAN_CLS','TECH_CHAN','TECH_CHAN_N','VOL_NOTE','VOL_CLS','TECH_VOL','TECH_VOL_N',
        'TECH_IND_ROWS','TECH_REASONING','LEVEL_SUP','LEVEL_RES','LEVEL_STOP','LEVEL_T12','LEVEL_RR_POS','TECH_PLAYBOOK',
        'PRED_DATE','PRED_BASE','PRED_DIR','PRED_SCORE','PRED_LEVELS','PRED_HORIZON','PRED_STOP','PRED_STATUS','PRED_RESULT','GLOBAL_TRACK']}
    t = TECH.get(slug)
    tt = TECH_TEXT.get(slug, {})
    if not t:
        ph['TECH_DATE'] = '暂缺'
        ph['RATING'] = '数据待补'
        ph['SCORE_BASIS'] = '该标的行情数据尚未采集，本章将在下一轮数据刷新时补充。'
        ph['TECH_TREND'] = ph['TECH_MOM'] = ph['TECH_CHAN'] = ph['TECH_VOL'] = '—'
        ph['TECH_TREND_N'] = ph['TECH_MOM_N'] = ph['TECH_CHAN_N'] = ph['TECH_VOL_N'] = '待采集'
        ph['VOL_NOTE'] = ''
        ph['TECH_IND_ROWS'] = '<tr><td colspan="3">待采集</td></tr>'
        ph['TECH_REASONING'] = '待技术面数据采集后补充论据。'
        ph['LEVEL_SUP'] = ph['LEVEL_RES'] = ph['LEVEL_STOP'] = ph['LEVEL_T12'] = ph['LEVEL_RR_POS'] = '—'
        ph['TECH_PLAYBOOK'] = '等数据就绪后给出操作剧本。'
    else:
        sc = t['scores']
        mkt_note = 'A股含筹码+主力资金' if t['market'] == 'a' else '港股：无筹码/主力资金数据，本维度仅量价，权重已摊入前三维'
        ph.update({
            'TECH_DATE': t['date'], 'SCORE': '%+.1f' % t['score'], 'RATING': t['rating'],
            'SCORE_BASIS': '评分=趋势30%%+动量25%%+通道15%%+量价20%%加权归一至±10；信号明细：%s。' % '、'.join(
                t['notes']['trend'] + t['notes']['mom'] + t['notes']['chan'] + t['notes']['vol']),
            'TREND_CLS': _cls(sc['trend']), 'TECH_TREND': '%+.1f' % sc['trend'], 'TECH_TREND_N': ' · '.join(t['notes']['trend']) or '中性',
            'MOM_CLS': _cls(sc['mom']), 'TECH_MOM': '%+.1f' % sc['mom'], 'TECH_MOM_N': ' · '.join(t['notes']['mom']) or '中性',
            'CHAN_CLS': _cls(sc['chan']), 'TECH_CHAN': '%+.1f' % sc['chan'], 'TECH_CHAN_N': ' · '.join(t['notes']['chan']) or '中性',
            'VOL_NOTE': mkt_note,
            'VOL_CLS': _cls(sc['vol']), 'TECH_VOL': '%+.1f' % sc['vol'], 'TECH_VOL_N': ' · '.join(t['notes']['vol']) or '中性',
        })
        ma = t['ma']; kdj = t['kdj']; rsi = t['rsi']; macd = t['macd']; dmi3 = t['dmi']
        rows = [
            ('收盘价 / 近5日涨跌', '%s / %+.1f%%' % (_fmt(t['close']), t['chg5']), '数据日 %s（K线延时口径）' % t['date']),
            ('MA5/10/20/60', '%s / %s / %s / %s' % (_fmt(ma.get('5')), _fmt(ma.get('10')), _fmt(ma.get('20')), _fmt(ma.get('60'))),
             ('多头排列' if '多头排列' in t['notes']['trend'] else '空头排列' if '空头排列' in t['notes']['trend'] else '均线纠缠') + ('·站上年线' if '站上年线' in t['notes']['trend'] else '·年线下方')),
            ('MACD DIF/DEA/柱', '%s / %s / %s' % (_fmt(macd[0]), _fmt(macd[1]), _fmt(macd[2])), ' · '.join([n for n in t['notes']['mom'] if n.startswith('MACD')] + (['零轴上方强势区'] if '零轴上方' in t['notes']['mom'] else [])) or '零轴附近'),
            ('KDJ K/D/J', '%s / %s / %s' % (_fmt(kdj[0]), _fmt(kdj[1]), _fmt(kdj[2])), ' · '.join([n for n in t['notes']['mom'] if n.startswith('KDJ')]) or ('K>D 偏多' if (kdj[0] or 0) > (kdj[1] or 0) else 'K<D 偏空')),
            ('RSI 6/12/24', '%s / %s / %s' % (_fmt(rsi[0]), _fmt(rsi[1]), _fmt(rsi[2])), '超卖<20 超买>80'),
            ('BOLL 上/中/下轨', '%s / %s / %s' % (_fmt(t['boll'][0]), _fmt(t['boll'][1]), _fmt(t['boll'][2])), 'ATR约%.1f%%/日' % t['atr_pct']),
            ('DMI PDI/MDI/ADX', '%s / %s / %s' % (_fmt(dmi3[0]), _fmt(dmi3[1]), _fmt(dmi3[2])), 'ADX>25强趋势 / <20震荡钝化'),
            ('量比(5日均/20日均)', _fmt(t['vol_ratio5_20']), '放量>1.2 缩量<0.8'),
        ]
        if t['market'] == 'a':
            rows.append(('筹码获利比例 / 平均成本', '%s%% / %s' % (_fmt(t['profit_pct']), _fmt(t['avg_cost'])), '获利盘<20%超跌区 >90%兑现风险区'))
            rows.append(('主力净流入(当日/5日)', '%s / %s' % (_yi(t['main_flow']), _yi(t['main_flow5d'])), '正=净流入'))
        ph['TECH_IND_ROWS'] = ''.join('<tr><td>%s</td><td><strong>%s</strong></td><td>%s</td></tr>' % r for r in rows)
        # 定性论据：子代理撰写，缺失则用规则化兜底
        reasoning = tt.get('reasoning')
        if not reasoning:
            bits = []
            if '多头排列' in t['notes']['trend']: bits.append('均线呈多头排列且价格站上年线，中期趋势结构偏多')
            elif '空头排列' in t['notes']['trend']: bits.append('均线空头排列且价格受压年线之下，中期趋势结构偏弱')
            else: bits.append('均线系统纠缠，方向未明，处于震荡结构')
            if 'MACD金叉' in t['notes']['mom']: bits.append('MACD金叉动量修复')
            elif 'MACD死叉' in t['notes']['mom']: bits.append('MACD死叉动量走弱')
            if t.get('sideways'): bits.append('ADX低于20表明当前为震荡市，趋势类指标信号可靠性下降，宜降权处理')
            if t['market'] == 'a' and t['main_flow'] is not None: bits.append('主力资金当日%s%s' % ('净流入' if t['main_flow'] > 0 else '净流出', '，与价格方向%s' % ('一致加强' if (t['main_flow'] > 0) == (t['chg5'] >= 0) else '背离需警惕')))
            reasoning = ('；'.join(bits) + '。综合四维共振得 %+.1f 分，评级「%s」——结论以右侧纪律为准：不预测、只应对，跌破止损位无条件执行。' % (t['score'], t['rating']))
        ph['TECH_REASONING'] = reasoning
        ph['LEVEL_SUP'] = '%s / %s' % (_fmt(t['support'][0]) if t['support'] else '—', _fmt(t['support'][1]) if len(t['support']) > 1 else '—')
        ph['LEVEL_RES'] = '%s / %s' % (_fmt(t['resist'][0]) if t['resist'] else '—', _fmt(t['resist'][1]) if len(t['resist']) > 1 else '—')
        ph['LEVEL_STOP'] = str(t['stop'])
        ph['LEVEL_T12'] = '%s / %s%s' % (_fmt(t['t1']), _fmt(t['t2']), (' / ' + _fmt(t['t3'])) if t['t3'] else '')
        rr_pos = ('盈亏比 %s' % t['rr']) if t['rr'] else '盈亏比不足1.5，介入性价比低'
        pos_map = {'强烈看多': '≤8成', '偏多': '≤5成', '中性': '≤2成', '偏空': '0成(观望)', '强烈看空': '0成(规避)'}
        ph['LEVEL_RR_POS'] = '%s · 建议仓位 %s' % (rr_pos, pos_map.get(t['rating'], '≤2成'))
        pb = tt.get('playbook')
        if not pb:
            if t['rating'] in ('强烈看多', '偏多'):
                pb = '回踩 %s 一线缩量企稳可分批介入；放量突破 %s 加仓；收盘跌破 %s 无条件止损。' % (_fmt(t['support'][0]) if t['support'] else _fmt(t['ma'].get('20')), _fmt(t['resist'][0]) if t['resist'] else _fmt(t['hi20']), _fmt(t['stop']))
            elif t['rating'] == '中性':
                pb = '区间思路：回落至 %s 附近轻仓试错、接近 %s 减仓；收盘跌破 %s 离场观望，突破 %s 站稳再转右侧行动。' % (_fmt(t['support'][0]) if t['support'] else _fmt(t['lo20']), _fmt(t['resist'][0]) if t['resist'] else _fmt(t['hi20']), _fmt(t['stop']), _fmt(t['resist'][0]) if t['resist'] else _fmt(t['hi20']))
            else:
                pb = '反弹至 %s 一线减仓/回避左侧抄底；仅当重新收复 %s 且量能配合后才恢复观察；当前仓位建议 0 成。' % (_fmt(t['ma'].get('20')), _fmt(t['ma'].get('20')))
        ph['TECH_PLAYBOOK'] = pb
    # ch14 预测登记
    p = REG.get(slug)
    if p:
        status_map = {'pending': '待验证', 'hit': '命中(T1先达)✔', 'stopped': '破位止损✘', 'expired_neutral': '到期中性'}
        ph.update({
            'PRED_DATE': p['date'], 'PRED_BASE': _fmt(p['close']),
            'PRED_DIR': p['rating'], 'PRED_SCORE': '%+.1f' % p['score'],
            'PRED_LEVELS': '%s / %s / %s' % (_fmt(p['stop']), _fmt(p['t1']), _fmt(p['t2'])),
            'PRED_HORIZON': p['date'] + ' → ' + p['horizon_end'],
            'PRED_STOP': _fmt(p['stop']),
            'PRED_STATUS': status_map.get(p.get('status'), p.get('status', '待验证')),
            'PRED_RESULT': p.get('result') or '观察期内。到期或触发条件后回填：记录触发日期、触发价位与判定依据，同步更新全局战绩。',
        })
    else:
        ph['PRED_DATE'] = ph['PRED_BASE'] = '—'; ph['PRED_DIR'] = '—'; ph['PRED_SCORE'] = '—'
        ph['PRED_LEVELS'] = '—'; ph['PRED_HORIZON'] = '—'; ph['PRED_STOP'] = '—'
        ph['PRED_STATUS'] = '未登记'; ph['PRED_RESULT'] = '该标的技术数据待采集后自动登记预测。'
    # 全局战绩
    if REG:
        done = [v for v in REG.values() if v.get('status') in ('hit', 'stopped', 'expired_neutral')]
        pend = sum(1 for v in REG.values() if v.get('status') == 'pending')
        hit = sum(1 for v in REG.values() if v.get('status') == 'hit')
        stop = sum(1 for v in REG.values() if v.get('status') == 'stopped')
        neutral = len(done) - hit - stop
        if done:
            wr = hit * 100.0 / max(1, hit + stop)
            ph['GLOBAL_TRACK'] = '已判定 %d 笔：命中 %d · 止损 %d · 中性到期 %d；**方向胜率(命中/命中+止损) %.0f%%**；另有 %d 笔观察中。每季度用 _review.py 复核并回填，防止口径漂移。' % (len(done), hit, stop, neutral, wr, pend)
        else:
            ph['GLOBAL_TRACK'] = '本轮为第 1 批预测登记（%d 笔全部观察中），尚无可判定样本。首批观察期至 2026-10-24，届时运行回顾流程回填结果并计算首份胜率。' % pend
    else:
        ph['GLOBAL_TRACK'] = '尚无登记样本。'
    return ph

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
    # tech block (ch13 技术面评估 / ch14 预测登记与回顾)；长键先替换避免子串误伤
    tb = tech_block(slug)
    for k in sorted(tb, key=len, reverse=True):
        tpl = tpl.replace(k, str(tb[k]))
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