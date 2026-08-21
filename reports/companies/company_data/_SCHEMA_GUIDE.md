# 单公司 12 维度深度分析 · 数据文件产出规范

你要为「产业链报告」里的某一家公司联网研究并生成一份数据文件。**文件路径：`company_data/<slug>.py`**，内容是一个 Python 字典 `D = {...}`。

## 第一步：必读
1. 读 `.trae/skills/company-deep-research/SKILL.md`——了解 12 个维度、数据源分层（一级财报>二级研报>三级财经平台>线索，财务数字优先回原始财报核对）、经营/会计/一次性切分、Bull/Base/Bear。
2. 读 `company_data/mindray.py`——这是「范例」，字段命名、每个字段的数据形态（尤其 `list` 字段的顺序）必须严格照抄范例。

## 数据源纪律（硬性）
- 财务事实（营收/净利/毛利率/ROE/市值/股本/资产负债表）优先回到该公司年报/半年报/公告/交易所披露核对，不凭印象。
- 市值/股价/PE/PB 用第三方(东财/同花顺/雪球/新浪/亿牛网)但须标注日期口径，能回交易所核对就核对。
- 预测类（2026~2028E、Bull/Base/Bear、行情隐含）必须标注"估算/一致预期/AI估算"之一，禁止把预测当事实。
- 「券商评价」子项：优先列**外资大行**(高盛/摩根士丹利/瑞银/杰富瑞/美银/花旗/大摩等)的目标价与评级；内资研报目标价普遍偏乐观需打折，明确写"外资优先"。若查不到某外资覆盖就注明"某外资未覆盖"。
- 每个数据字段尽力标注"数据截至/引用日期"，不同日期数据不要假装同步。

## 输出字段（字典 D 的键，顺序可不同，但字段名必须一致）
除 `company/code/prev/next/title/chain_anchor/companies_link` 之外（这些由渲染器自动从 companies.json 填充，**不要写**），其余字段都在 D 里：

- `sidebar_sub`: 文本，如 `"创新药企 · 数据截至2026.08.21"`
- `sector_desc`: 一行公司定位，如 `"CXO龙头 · 全球前三 · 一体化CRDMO"`
- `kpi`: dict，含 `mcap/mcap_date/pe/pe_date/pct/pe_med/g26/g26_note`（市值、PE-TTM、近5年分位、5年中位、2026E净利增速）
- `tldr`: dict，含 `pitch/fund/val/pricein/watch/scen`（一句话/基本面/估值/市场隐含预期/核心看点/情景结论）
- `blurb`: HTML 字符串（公司画像，`<strong>...</strong>` 开头）
- `fin`: dict，含 `rev/ni/core/gm/roe/ocf` 各为一个 list，顺序 = [FY2023, FY2024, FY2025, 2026E, 2027E]（没有的填 `"—"`）。**采样例 mindray.py 的顺序，不要写 5 个以上列**
- `fund_business`: HTML 字符串（业务结构/产品/客户/竞争对手/管理层/资产负债）
- `fund_split`: HTML `<ul>` 列表（经营/会计/一次性切分）
- `val_rows`: list of 3元组 `(指标, 数值, 说明/日期)`，12 行左右（股价/市值/EV/PE-TTM/PE-26E/27E/28E/PB/PS/EV-EBITDA/FCF Yield/PEG）
- `val_note`: HTML 字符串（估值注意与口径说明）
- `hist_rows`: list of 3元组 `(维度, 数值, 位置判断)`（PE中位/最高最低/当前分位/PB等）
- `hist_take`: HTML 字符串（当前处过去5年什么位置）
- `fc`: dict，含 `note_a/note_market/note_ai` 及 `rev/gm/ni/eps` 各 list，顺序 = [2025A, 2026E, 2027E, 2028E]
- `potential`: HTML 字符串（按公司类型：CRO/创新药/AI/模式动物/器械/IVD/原料药/流通/药店 差异抓取潜指标；末尾必须有一个 `<div class="callout warn"><div class="label">经营/会计/一次性切分</div>...</div>`）
- `growth_rows`: list of 3元组 `(增长驱动, 对2027贡献pct, 说明)`
- `growth_take`: HTML 字符串
- `pricein`: HTML 字符串，内含一个 `<div class="callout key"><div class="label">反推：当前价格隐含了什么</div>...</div>`
- `moat`: HTML 字符串（`<ul>`，末尾一个 `<div class="callout key"><div class="label">竞争对手能否复制？</div>...</div>`）
- `catalysts`: HTML 字符串（`<p><strong>时点</strong> · 事件 — 影响</p>` 若干条，给具体日期/时点）
- `risks`: HTML `<table>` 字符串（thead: 风险/影响口径/说明）
- `verdict`: dict，含 `bull/base/bear` 各为4元组 `(假设, 2028净利, 合理估值倍率, 对应股价)`，及 `rr`（收益风险比）、`falsify`（什么会证伪Base）
- `timing`: dict，含 4 个键：
  - `sector`: HTML 字符串（该细分行业整体估值分位 + 景气度处周期的哪个阶段）
  - `rows`: list of 3元组 `(维度, 当前信号, 择时判断)`——恰好 4 行：技术面 / 基本面 / 情绪面 / 政策影响
  - `broker`: HTML 字符串（外资大行目标价与评级优先，内资存疑，标注"外资优先"）
  - `verdict`: HTML 字符串（介入结论：明确给 `分批建仓/轻仓试仓/等回落/等企稳信号/暂不介入` 之一 + 建议仓位 + 加仓触发 + 止损）
- `src`: dict，含 `t1/t2/t3/t4`（数据来源层级各一段）
- `confidence`: HTML 字符串（各维度信心百分比 + 已回源/待核实项说明）
- `sources`: list of str（来源清单，含渠道/报告名，尽量给来源主体）

## 编写注意
- HTML 字符串里的普通引号直接用 `"`，若内含另一个 `"` 用 `"` 或转义；避免用单引号包裹含撇号的内容。
- 数值不确定处用 `约/≈/~` 并标注 `估`；不要编造精确到异常可信的假数字。
- 篇幅参考 mindray.py（约 8~12KB），`fund_business/fund_split/classes` 等要写实质内容，不要空壳。
- 写完用 `python -c`（在项目目录）打印 `len(D)` 检查非空即可，无需渲染。

## 完成信号
返回一句简短的总结：`公司名(slug)，数据截至日期，主要结论一句话(介入结论)，信心水平`。