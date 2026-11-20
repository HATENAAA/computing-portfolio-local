"""Display a small, traceable excerpt of each project's core implementation."""
import json
from html import escape
from textwrap import dedent

# One excerpt per project. The team case also shows the backend side of the flow.
EXCERPTS = {
    'hsi': [
        ('hsi-sr-lab/thesis-final/source/test_eval.py', 116, 134, 'Python',
         ('Score each reconstructed cube', '逐图评价重建结果'),
         ('The evaluator handles the two model call signatures, converts the output to image layout, and accumulates the six metrics per sample.',
          '评测脚本统一基线与 MCArb 的模型调用，将输出转换为图像维度，再逐图累计六项指标。')),
    ],
    'vrfitai': [
        ('vrfitai/server/app.js', 133, 149, 'JavaScript',
         ('Keep one record when saving is retried', '保存重试沿用原训练记录'),
         ('A repeated session ID returns the existing record when the payload matches. Different content under the same ID raises a conflict.',
          '同一记录 ID 的重试内容一致时返回原记录，内容变化时返回冲突。')),
    ],
    'manufacturing': [
        ('manufacturing-platform/backend/src/main/java/com/hystu/springboot_/service/InventoryService.java', 37, 45, 'Java',
         ('Compare inventory, ledger and reservations', '核对在库、流水与预留'),
         ('Each material is checked against the ledger totals and active reservations. The RECON example above hits the stock-ledger mismatch branch.',
          '逐项核对物料与对应流水和有效预留。上方 RECON 样例对应库存余额与流水不一致这一分支。')),
    ],
    'firewatch': [
        ('firewatch/app/temporal.py', 38, 55, 'Python',
         ('Match predicted and labelled events', '匹配预测事件与标注'),
         ('Temporal overlap qualifies a candidate. One-to-one matching determines detected, false-positive and missed events.',
          '先以时间重叠筛选候选，再进行一对一匹配，统计检出、误报与漏检。')),
    ],
    'signal': [
        ('signal-lab/transfer.py', 12, 25, 'Python',
         ('Estimate H1 and select valid frequency bins', '估计 H1 并筛选有效频点'),
         ('Welch spectra feed the transfer estimate. Excitation, coherence, segment count and stationarity determine which bins are retained.',
          '用 Welch 谱估计频响，再按激励、相干性、分段数和平稳性筛选有效频点。')),
    ],
    'bathymetry': [
        ('bathymetry-lab/pipeline.py', 31, 45, 'Python',
         ('Fit and evaluate on separate groups', '隔离训练与留出组'),
         ('The same grouped split is used for both models. Each pipeline fits its scaler on training rows before predicting held-out depths.',
          '两种模型使用同一份分组划分，各自仅用训练行拟合缩放器，再预测留出样本。')),
    ],
    'city': [
        ('city-explorer/src/components/LeafletMap.vue', 157, 163, 'Vue / JavaScript',
         ('Keep the map usable when tiles fail', '底图失效后保留地图交互'),
         ('The error callback verifies which tile layer failed before switching to the offline grid.',
          '底图加载出错后，先判断出错的图层是否仍在使用，再切换到离线网格。')),
    ],
    'medical': [
        ('case-studies/medical/source/src/views/Report.vue', 141, 154, 'Vue / JavaScript',
         ('Front end · Load report details by order', '前端 · 按订单加载报告明细'),
         ('The report page fetches rows for the current order and separates flagged check items for the summary view.',
          '报告页按当前订单查询明细，并把标记为异常的检查项整理到总检结论。')),
    ],
}


def render(page, root):
    t = page.t
    excerpts = []
    for path, first, last, language, title, description in EXCERPTS[page.case]:
        lines = (root / path).read_text(encoding='utf-8').splitlines()
        if last > len(lines):
            raise ValueError(f'Implementation range exceeds {path}:{first}–{last}')
        excerpts.append((path.rsplit('/', 1)[-1], first, last, language, title, description,
                         '\n'.join(lines[first-1:last])))
    if page.case == 'medical':
        backend = json.loads((root / 'case-studies/medical/backend-excerpt.json').read_text(encoding='utf-8'))
        excerpts.append((backend['file'], backend['first'], backend['last'], 'Java',
                         ('Back end · Calculate daily capacity', '后端 · 计算每天的可约数量'),
                         ('The calendar subtracts booked orders from each weekday’s configured capacity and returns that day’s remainder.',
                          '预约日历根据医院的星期配额减去当天已有订单，返回可约余量。'),
                         backend['code']))
    cards = []
    for index, (file, first, last, language, title, description, code) in enumerate(excerpts):
        cards.append(
            f'<details class="implementation-excerpt"{" open" if index == 0 else ""}>'
            f'<summary>{t(*title)}</summary><p>{t(*description)}</p>'
            f'<figure class="source-code"><figcaption>{escape(file)} · {first}–{last} · {escape(language)}</figcaption>'
            f'<pre tabindex="0" aria-label="{t("Original code excerpt","原始代码片段")}"><code>{escape(dedent(code))}</code></pre></figure></details>')
    title = t('Core implementation', '核心实现')
    return f'<article class="evidence workflow" id="implementation"><h2>{title}</h2>{"".join(cards)}</article>'
