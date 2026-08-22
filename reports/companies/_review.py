# -*- coding: utf-8 -*-
"""预测回顾验证工具（事后回顾，提高胜率）：
对 _review_registry.json 中 status=pending 的登记逐一判定：
  - 观察期内任一日 low <= stop  -> stopped（破位止损，记录触发日/价）
  - 观察期内任一日 high >= t1   -> hit（第一目标先达）
  - 两者同日均触发             -> 以盘中更先触及者计（无法分辨时按保守原则计 stopped）
  - 均未触发且已过 horizon_end -> expired_neutral（到期中性，不计入胜负）
判定后回填 status/checked/result，并把复盘日志追加到 company_data/_review_log.md。

用法: python _review.py [--dry]
"""
import io, sys, os, json, time, subprocess
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'company_data')
REG_PATH = os.path.join(DATA_DIR, '_review_registry.json')
LOG_PATH = os.path.join(DATA_DIR, '_review_log.md')
DRY = '--dry' in sys.argv


def run_cli(args):
    cmd = ['npx.cmd', '-y', 'westock-data-skillhub@1.0.5'] + args
    for i in range(2):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True,
                               encoding='utf-8', errors='replace',
                               shell=True, timeout=180)
            out = (p.stdout or '') + (p.stderr or '')
        except Exception as e:
            out = str(e)
        if 'fetch failed' not in out or i == 1:
            return out
        time.sleep(3)
    return out


def parse_md_table(text):
    rows = []
    header = None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('|'):
            if header is not None:
                break
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if header is None:
            if len(cells) >= 2 and not set(''.join(cells)) <= set('-: '):
                header = cells
            continue
        if set(''.join(cells)) <= set('-: '):
            continue
        rows.append({header[i]: cells[i] for i in range(min(len(header), len(cells)))})
    return rows


def rowkey(row):
    return row.get('code') or row.get('symbol') or ''


def _f(x):
    try:
        return float(str(x).replace(',', ''))
    except Exception:
        return None


def judge(reg):
    pend = {k: v for k, v in reg.items() if v.get('status') == 'pending'}
    if not pend:
        print('无待判定登记。')
        return []
    codes = ','.join(v['wc'] for v in pend.values())
    print('拉取 %d 笔登记的日K...' % len(pend))
    txt = run_cli(['kline', codes, '--period', 'day', '--limit', '60'])
    rows = [r for r in parse_md_table(txt) if rowkey(r)]
    by_code = {}
    for r in rows:
        by_code.setdefault(rowkey(r), []).append(r)
    results = []
    today = datetime.now().strftime('%Y-%m-%d')
    for slug, p in pend.items():
        bars = sorted(by_code.get(p['wc'], []), key=lambda r: r.get('date', ''))
        verdict, trig_d, trig_px = None, None, None
        for b in bars:
            d = b.get('date', '')
            hi, lo = _f(b.get('high')), _f(b.get('low'))
            if d < p['date']:          # 只看登记日之后的K线
                continue
            hit_stop = lo is not None and lo <= p['stop']
            hit_t1 = hi is not None and hi >= p['t1']
            if hit_stop and hit_t1:
                verdict, trig_d, trig_px = 'stopped', d, p['stop']   # 同日双触，保守计止损
                break
            if hit_stop:
                verdict, trig_d, trig_px = 'stopped', d, p['stop']
                break
            if hit_t1:
                verdict, trig_d, trig_px = 'hit', d, p['t1']
                break
        if verdict is None and bars and today > p['horizon_end']:
            last_close = _f(bars[-1].get('close')) or p['close']
            pnl = (last_close - p['close']) / p['close'] * 100
            verdict, trig_d, trig_px = 'expired_neutral', today, last_close
            extra = '期末收盘 %.2f，区间涨跌 %+.1f%%' % (last_close, pnl)
        else:
            extra = ''
        if verdict:
            label = {'hit': '命中(T1先达)', 'stopped': '破位止损',
                     'expired_neutral': '到期中性'}[verdict]
            result = '%s于%s触及%.2f%s' % (label, trig_d, trig_px,
                                          ('，' + extra) if extra else '')
            if not DRY:
                p['status'], p['checked'], p['result'] = verdict, trig_d, result
            print('[%s] %s %s -> %s | %s' % (verdict.upper(), slug, p['wc'], label, result))
        else:
            print('[PENDING ] %s %s 继续观察（期限至 %s）' % (slug, p['wc'], p['horizon_end']))
        results.append((slug, verdict))
    hit = sum(1 for _, s in results if s == 'hit')
    stop = sum(1 for _, s in results if s == 'stopped')
    neu = sum(1 for _, s in results if s == 'expired_neutral')
    wr = hit * 100.0 / max(1, hit + stop)
    print('\n本轮判定：%d 命中 / %d 止损 / %d 中性；方向胜率 %.0f%%' % (hit, stop, neu, wr))
    return results


def main():
    reg = json.load(open(REG_PATH, encoding='utf-8'))
    results = judge(reg)
    if DRY or not results:
        return
    json.dump(reg, open(REG_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    lines = ['', '## 回顾 %s' % datetime.now().strftime('%Y-%m-%d %H:%M'),
             '- 判定明细见上方控制台输出；登记文件已同步回填。',
             '- 提示：运行 `python _render.py` 刷新各公司页第14章展示。']
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('已回填 %s 并追加复盘日志 %s' % (os.path.basename(REG_PATH), os.path.basename(LOG_PATH)))


if __name__ == '__main__':
    main()
