"""Build an offline, source-linked literature review from saved primary sources.

This script only parses the saved research material and renders the report. It
does not download datasets, load checkpoints, execute source code, or train models.
"""
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "sources"
CONTENT = json.loads((ROOT / "review_content.json").read_text())
SOURCES = {s["id"]: s for s in CONTENT["sources"]}
RECORDS = []


def number_pair(value):
    cleaned = value.replace("\\pm", "").replace("−", "-")
    nums = re.findall(r"[+-]?\d+(?:\.\d+)?", cleaned)
    return (float(nums[0]), float(nums[1]) if len(nums) > 1 else None) if nums else (None, None)


def record(protocol, task, model, mean, dispersion, metric, unit, source, table, raw):
    RECORDS.append(dict(protocol=protocol, task=task, model=model, mean=mean,
                        dispersion=dispersion, metric=metric, unit=unit,
                        source_id=source, source_url=SOURCES[source]["url"],
                        source_table=table, raw_value=raw))


nb = json.loads((SRC / "neuralbench-results-data.json").read_text())
names = {m["name"]: m["display"] for m in nb["models"]}
for task in nb["tasks"]:
    if task["device"] != "eeg":
        continue
    unit = "%" if task["metric_display"] in ["Balanced accuracy", "Top-5 accuracy (per-subject)"] else "0–1系数"
    for model, value in nb["results"].get(task["id"], {}).items():
        if value.get("mean") is not None:
            record("NeuralBench FT", task["display"], names.get(model, model),
                   value["mean"], value.get("std"), task["metric_display"], unit,
                   "NB-DATA", task["id"], json.dumps(value, ensure_ascii=False))

for table_index, protocol in [(4, "OmniEEG LP"), (6, "OmniEEG FT")]:
    table = json.loads((SRC / "omnieeg_tables.json").read_text())[table_index]
    header = table["rows"][0]
    for row in table["rows"][1:]:
        if len(row) != len(header):
            continue
        for model, value in zip(header[2:], row[2:]):
            mean, dispersion = number_pair(value)
            record(protocol, row[0], model, None if mean is None else mean * 100,
                   None if dispersion is None else dispersion * 100,
                   "Balanced accuracy", "%", "OMNI", f"Table {table_index+1}", value)

for table_index, protocol in [(17, "FAME paper LP"), (61, "FAME paper FT subset")]:
    table = json.loads((SRC / "fame_tables.json").read_text())[table_index]
    header = table["rows"][0]
    for row in table["rows"][1:]:
        if len(row) != len(header) or row[0].lower().startswith("average"):
            continue
        for model, value in zip(header[1:], row[1:]):
            mean, dispersion = number_pair(value)
            record(protocol, row[0], model, mean, dispersion, "Balanced accuracy", "%",
                   "FAME", "Table 1" if table_index == 17 else "Table 7", value)

table = json.loads((SRC / "reve_tables.json").read_text())[4]
for row in table["rows"][1:]:
    if len(row) != len(table["rows"][0]) or row[0].startswith("Avg"):
        continue
    for model, value in zip(table["rows"][0][1:], row[1:]):
        mean, dispersion = number_pair(value)
        record("REVE readout ablation LP", row[0], model, mean * 100, dispersion * 100,
               "Balanced accuracy", "%", "REVE", "Table 4", value)

for rec in RECORDS:
    if rec["mean"] is not None and rec["unit"] == "%":
        assert 0 <= rec["mean"] <= 100, rec
keys = [(r["protocol"], r["task"], r["model"]) for r in RECORDS]
assert len(keys) == len(set(keys)), "Duplicate dataset/model records"

groups = defaultdict(list)
for row in RECORDS:
    groups[row["protocol"]].append(row)
baseline = {p: "REVE-B (Pool)" if p.startswith("REVE readout") else "REVE" for p in groups}
evidence = []
for protocol, records in groups.items():
    tasks = sorted({r["task"] for r in records})
    for task in tasks:
        rows = [r for r in records if r["task"] == task and r["mean"] is not None]
        reve = next((r for r in rows if r["model"] == baseline[protocol]), None)
        candidates = [r for r in rows if r["model"] not in ["Chance", "Dummy"]]
        if reve and candidates:
            best = max(candidates, key=lambda r: r["mean"])
            evidence.append(dict(protocol=protocol, task=task, metric=reve["metric"],
                                 unit=reve["unit"], reve=reve["mean"],
                                 best_model=best["model"], best=best["mean"],
                                 gap=round(best["mean"]-reve["mean"], 6),
                                 source_url=reve["source_url"], source_table=reve["source_table"]))

bundle = dict(content=CONTENT, records=RECORDS, evidence=evidence,
              protocol_baselines=baseline, snapshot_commit="fe31393affab2590e59b0a7e1457aad1a1da908e")
(ROOT / "review_bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2))
with (ROOT / "benchmark_records.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(RECORDS[0]))
    writer.writeheader()
    writer.writerows(RECORDS)
with (ROOT / "reve_task_gaps.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(evidence[0]))
    writer.writeheader()
    writer.writerows(evidence)


def esc(value):
    return html.escape(str(value), quote=True)


def refs(ids):
    return " ".join(f'<a class="ref" href="{esc(SOURCES[i]["url"])}" target="_blank" rel="noreferrer">[{esc(i)}]</a>' for i in ids)


def listing(items):
    return "<ul>" + "".join(f"<li>{esc(v)}</li>" for v in items) + "</ul>"


def note_items(items):
    return "".join(f'<article class="finding"><h3>{esc(i["title"])}</h3><p>{esc(i["body"])} {refs(i["sources"])}</p></article>' for i in items)


model_rows = "".join(
    f'<tr data-search="{esc(m["name"]+" "+m["role"]+" "+m["design"])}">'
    f'<td class="model-name">{esc(m["name"])}<small>{esc(m["role"])} · {esc(m["priority"])}</small>{refs(m["source_ids"])}</td>'
    + "".join(f'<td>{esc(m[k])}</td>' for k in ["design", "evidence", "limits", "borrow"])
    + "</tr>" for m in CONTENT["models"]
)
bench_rows = "".join(
    "<tr>" + f'<td><strong>{esc(b["name"])}</strong><br>{refs(b["sources"])}</td>'
    + "".join(f'<td>{esc(b[k])}</td>' for k in ["use", "protocol", "limit"])
    + "</tr>" for b in CONTENT["benchmarks"]
)
route_items = "".join(
    f'<article class="stage"><div class="stage-name">{esc(s["name"])}</div>'
    f'<p class="purpose">{esc(s["why"])}</p><p>{esc(s["spec"])}</p>'
    f'<p class="gate"><strong>保留 / 停止条件：</strong>{esc(s["gate"])}</p></article>'
    for s in CONTENT["route"]
)
experiment_rows = "".join(
    "<tr>" + "".join(f'<td>{esc(e[k])}</td>' for k in ["id", "comparison", "question", "control", "decision"]) + "</tr>"
    for e in CONTENT["experiments"]
)
source_items = "".join(
    f'<li id="source-{esc(s["id"])}"><strong>{esc(s["id"])}</strong> '
    f'<a href="{esc(s["url"])}" target="_blank" rel="noreferrer">{esc(s["title"])}</a>'
    f'<small>{esc(s["location"])}</small></li>' for s in CONTENT["sources"]
)
document = r"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>REVE：评测驱动的技术路线</title><style>
:root{--bg:#f6f6f3;--paper:#fff;--ink:#17252d;--muted:#566570;--line:#d5dcd9;--accent:#146351;--soft:#e9f0ed}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}a{color:var(--accent);text-underline-offset:3px}header,main{max-width:1450px;margin:auto;padding:38px 42px}header{padding-bottom:22px}.eyebrow{font:12px/1.6 ui-monospace,monospace;letter-spacing:1.5px;color:var(--muted)}h1{font-size:30px;line-height:1.5;font-weight:650;max-width:1000px;margin:12px 0 18px}h2{font-size:22px;margin:0 0 15px}h3{font-size:16px;margin:0 0 7px}p{margin:8px 0 14px}.lead{font-size:17px;border-left:4px solid var(--accent);padding:10px 20px;max-width:1120px;background:var(--soft)}.muted,small{color:var(--muted)}small{display:block;font-size:12px;line-height:1.6;margin-top:7px}.ref{font-size:12px;white-space:nowrap}nav{display:flex;gap:20px;flex-wrap:wrap;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:13px 0;margin-top:25px}nav a{text-decoration:none;font-size:13px}main{padding-top:12px}section{margin-bottom:45px;scroll-margin-top:16px}.findings{display:grid;grid-template-columns:1fr 1fr;gap:20px 30px}.finding{padding:16px 0;border-top:1px solid var(--line)}.finding:first-child{grid-column:1/-1}.finding p{margin-bottom:0}.controls{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin:15px 0}.controls label{font-size:13px;color:var(--muted)}select,input{font:inherit;font-size:14px;min-height:35px;padding:5px 10px;color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:4px}select{max-width:100%}input{min-width:260px}table{width:100%;border-collapse:collapse;background:var(--paper);font-size:13px;line-height:1.75}th,td{text-align:left;vertical-align:top;padding:13px;border:1px solid var(--line)}th{font-size:12px;background:var(--soft);font-weight:650}td strong{font-weight:650}.table-wrap{overflow-x:auto}.model-table{min-width:1080px}.model-table td{min-width:180px}.model-table td:first-child{min-width:130px;width:130px}.model-name{font-weight:650}.model-name small{font-weight:400}.source-note{font-size:12px;color:var(--muted);padding:9px 0}.metric-note{font-size:13px;padding:12px 15px;background:var(--soft);border:1px solid var(--line)}.comparison{display:grid;grid-template-columns:minmax(300px,1fr) 1fr;gap:25px;margin:20px 0}.bars{background:var(--paper);padding:20px;border:1px solid var(--line)}.bar-row{display:grid;grid-template-columns:140px 1fr 65px;gap:10px;align-items:center;margin:9px 0;font-size:12px}.bar-track{background:var(--soft);height:14px}.bar-fill{height:100%;background:var(--muted)}.bar-row.reve .bar-fill{background:var(--accent)}.bar-row.reve{font-weight:650}.bar-caption{font-size:12px;color:var(--muted);margin-top:12px}.stats{padding:20px 0}.stats .value{font-size:24px;line-height:1.4;font-weight:650;color:var(--accent)}.pipeline{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:20px 0}.pipeline>div{border:1px solid var(--line);padding:15px;background:var(--paper)}.pipeline strong{display:block}.stage{border-top:1px solid var(--line);padding:22px 0}.stage-name{font-size:18px;font-weight:650}.purpose{color:var(--accent)}.gate{font-size:14px;padding:12px 15px;background:var(--soft)}ul{padding-left:23px}li{margin:9px 0}.source-list{columns:2;column-gap:45px;font-size:13px}.source-list li{break-inside:avoid;padding-bottom:8px}footer{border-top:1px solid var(--line);padding:20px 0;font-size:12px;color:var(--muted)}.subtle{font-size:13px;color:var(--muted)}
@media(max-width:800px){header,main{padding:22px 18px}h1{font-size:24px}.findings,.comparison,.pipeline{grid-template-columns:1fr}.source-list{columns:1}.bar-row{grid-template-columns:115px 1fr 60px}input{min-width:180px}.finding:first-child{grid-column:auto}}
@media print{body{background:white;font-size:11px}header,main{padding:15px 0;max-width:none}nav,.controls,.comparison{display:none}section{break-inside:auto}table{font-size:9px}.model-table{min-width:0}.model-table td{min-width:0}.source-list{columns:1}.stage,.finding{break-inside:avoid}a{color:inherit;text-decoration:none}h1{font-size:23px}h2{font-size:18px}}
</style></head><body><header><div class="eyebrow">OMNIEEG CHALLENGE / RESEARCH DECISION NOTE / 2026-11-13</div>
<h1>以 REVE 为起点：先定位弱项，再选择改进结构</h1>
<p class="lead">__DECISION__</p><p class="subtle">__SCOPE__</p>
<nav><a href="#findings">关键证据</a><a href="#evidence">逐任务比较</a><a href="#literature">14项模型比较</a><a href="#benchmarks">评测协议</a><a href="#route">具体路线</a><a href="#experiments">验证计划</a><a href="#sources">来源与局限</a></nav>
</header><main>
<section id="findings"><h2>由结果支持的判断</h2><div class="findings">__FINDINGS__</div></section>
<section id="evidence"><h2>逐任务结果：仅在同一协议内比较</h2>
<p>选择结果来源和任务，可以查看该任务的模型均值。这里的数字是公开报告结果；没有运行我们自己的实验。不同来源的分数不拼成排行榜。</p>
<div class="controls"><label>结果来源 <select id="protocol"></select></label><label>任务 <select id="task"></select></label></div>
<div id="metric-note" class="metric-note"></div><div class="comparison"><div class="bars"><h3 id="chart-title"></h3><div id="bars"></div><div class="bar-caption" id="bar-caption"></div></div><div class="stats" id="comparison-text"></div></div>
<div class="table-wrap"><table><thead><tr><th>模型</th><th>源表均值</th><th>源离散度字段</th><th>与REVE基线的差值</th></tr></thead><tbody id="result-body"></tbody></table></div><p id="result-source" class="source-note"></p>
<p class="subtle">NeuralBench 的分类/检索均值按百分数显示，宏F1和相关系数保持原始0–1量纲。OmniEEG原表0–1的BACC乘100转换为%。差值只在同任务同指标内计算。缺失或预训练排除项不计为0；源离散度不作显著性检验。</p>
</section>
<section id="literature"><h2>14项工作的设计、局限与可借鉴之处</h2><p>“可借鉴”表示研究假设；它与完整模型的公开成绩分开。P0为首先建立的基线，P1为优先验证模块，P2为后备，P3为本轮暂缓。</p><div class="controls"><label>筛选模型 <input id="model-search" placeholder="例如 REVE、频谱、语言、局部"></label><span class="subtle" id="model-count">14项</span></div>
<div class="table-wrap"><table class="model-table"><thead><tr><th>工作 / 优先级</th><th>关键设计</th><th>评测证据</th><th>局限与解释边界</th><th>我们借鉴什么</th></tr></thead><tbody id="model-body">__MODELS__</tbody></table></div></section>
<section id="benchmarks"><h2>四种评测体系的作用与边界</h2><div class="table-wrap"><table><thead><tr><th>体系</th><th>用途</th><th>协议</th><th>不能推导什么</th></tr></thead><tbody>__BENCHMARKS__</tbody></table></div><p class="metric-note">赛事目标：被试隔离8:1:1；三个指定种子分别重新划分；验证集BACC选权重；两个数据集等权形成分赛道分数；主赛道按名次积分累计。公开benchmark用于形成假设，最终选择按赛事验证协议执行。</p></section>
<section id="route"><h2>具体路线：读出修复 → 局部残差 → 从零预训练</h2>
<div class="pipeline"><div><strong>全局分支</strong>原生200 Hz输入 → REVE tokens → 结构化读出 → g_global</div><div><strong>局部分支（待验证）</strong>同一片段 → 多尺度滤波/局部功率 → 小型时空聚合 → g_local</div><div><strong>融合与提交</strong>全局logits + α × 局部logits → 每任务预测；决赛全部重新初始化</div></div>
__ROUTE__
<p class="metric-note">这是一个分阶段可删减的方案。若R0/R1已经修复缺口，或R2未胜过同容量对照，就停止增加模块。保留强REVE结果与正式比赛的原生接口；不将所有文献模块叠进一个模型。</p></section>
<section id="experiments"><h2>验证矩阵与保留条件</h2><div class="table-wrap"><table><thead><tr><th>编号</th><th>比较</th><th>研究问题</th><th>控制条件</th><th>如何判读</th></tr></thead><tbody>__EXPERIMENTS__</tbody></table></div>
<h3 style="margin-top:25px">项目级选型门槛（建议，非赛事规则）</h3>__ACCEPTANCE__
<h3>资源安排（建议，须吞吐短测）</h3>__BUDGET__
<p class="subtle">完整最终方案包含14×3=42个数据集—种子评测单元；多种读出和消融会额外增加运行数。无需对14项文献模型全部进行全量复现。</p>
</section>
<section id="sources"><h2>来源、版本与已知局限</h2>__LIMITATIONS__<ol class="source-list">__SOURCES__</ol>
<p>本地附带 <a href="benchmark_records.csv">完整公开结果CSV</a>、<a href="reve_task_gaps.csv">逐任务差距CSV</a>、<a href="review_bundle.json">结构化审阅数据</a>、<a href="sources/reve-page-9.png">REVE读出消融原页</a>和<a href="sources/fame-page-19.png">FAME独立评测原页</a>。源网页和PDF已保存在sources目录。静态数据固定至官方提交fe31393，网页后续更新不自动改变本报告。</p>
</section><footer>2026-11-13 / 文献审阅与方案设计已完成；模型训练、官方评测和赛事提交尚未执行。</footer></main>
<script id="review-data" type="application/json">__DATA__</script><script>
const D=JSON.parse(document.getElementById('review-data').textContent);
const protocols=[...new Set(D.records.map(r=>r.protocol))];
const protocol=document.getElementById('protocol'), task=document.getElementById('task');
function el(tag,txt){const e=document.createElement(tag);e.textContent=txt;return e;}
function fmt(v){return v==null?'—':v.toFixed(3).replace(/0+$/,'').replace(/\.$/,'');}
protocols.forEach(p=>{const o=el('option',p);o.value=p;protocol.append(o)});
function setTasks(){const old=task.value;task.replaceChildren();const list=[...new Set(D.records.filter(r=>r.protocol===protocol.value).map(r=>r.task))].sort();list.forEach(t=>{const o=el('option',t);o.value=t;task.append(o)});task.value=list.includes(old)?old:(list.includes('Schizophrenia')?'Schizophrenia':list[0]);render();}
function render(){
 const rows=D.records.filter(r=>r.protocol===protocol.value&&r.task===task.value).sort((a,b)=>(b.mean??-Infinity)-(a.mean??-Infinity));
 const ref=rows.find(r=>r.model===D.protocol_baselines[protocol.value]);
 const valid=rows.filter(r=>r.mean!=null&&!['Chance','Dummy'].includes(r.model));
 const best=valid[0];const m=rows[0];
 document.getElementById('metric-note').textContent='当前比较：'+protocol.value+' / '+task.value+' / '+m.metric+'（单位：'+m.unit+'）。全表均为同一来源、同一任务。';
 const body=document.getElementById('result-body');body.replaceChildren();
 rows.forEach(r=>{const tr=el('tr','');[r.model,fmt(r.mean),fmt(r.dispersion),r.mean!=null&&ref?.mean!=null?((r.mean-ref.mean>=0?'+':'')+fmt(r.mean-ref.mean)+(m.unit==='%'?' pp':'')):'—'].forEach(v=>tr.append(el('td',v)));body.append(tr)});
 const bars=document.getElementById('bars');bars.replaceChildren();const max=m.unit==='%'?100:1;
 const plotted=valid.slice(0,8);if(ref?.mean!=null&&!plotted.includes(ref))plotted.push(ref);
 plotted.forEach(r=>{const row=el('div','');row.className='bar-row'+(r.model===D.protocol_baselines[protocol.value]?' reve':'');const label=el('span',r.model),track=el('div',''),fill=el('div','');track.className='bar-track';fill.className='bar-fill';fill.style.width=Math.max(0,Math.min(100,r.mean/max*100))+'%';track.append(fill);row.append(label,track,el('span',fmt(r.mean)));bars.append(row)});
 document.getElementById('chart-title').textContent=task.value+' · '+m.metric;
 document.getElementById('bar-caption').textContent='纵向：模型；横向：'+m.metric+'（'+m.unit+'），0–'+max+'。展示均值最高的8个非Chance/Dummy模型，并补入未包含的REVE基线；不画推断性误差条。';
 const text=document.getElementById('comparison-text');text.replaceChildren();
 if(ref?.mean!=null){const v=el('div',fmt(ref.mean)+(m.unit==='%'?'%':''));v.className='value';text.append(v,el('p',D.protocol_baselines[protocol.value]+' · 源表均值'));text.append(el('p','当前任务最高均值：'+best.model+' '+fmt(best.mean)+(m.unit==='%'?'%':'')));text.append(el('p','与该任务最高均值的差距：'+fmt(best.mean-ref.mean)+(m.unit==='%'?' 个百分点':'')+'。该差距用于提出假设，不自动证明统计显著或模块因果。'));}else{text.append(el('p','源表未给REVE可比较值；不计算REVE差距。'));}
 const source=document.getElementById('result-source');source.replaceChildren(el('span','来源：'+m.source_table+' · '));const a=el('a',m.source_id);a.href=m.source_url;a.target='_blank';a.rel='noreferrer';source.append(a);
}
protocol.addEventListener('change',setTasks);task.addEventListener('change',render);setTasks();
document.getElementById('model-search').addEventListener('input',e=>{const q=e.target.value.toLowerCase();let count=0;document.querySelectorAll('#model-body tr').forEach(tr=>{const yes=tr.textContent.toLowerCase().includes(q);tr.hidden=!yes;if(yes)count++});document.getElementById('model-count').textContent=count+' / 14项';});
</script></body></html>"""
replacements = {
    "__DECISION__": esc(CONTENT["decision"]), "__SCOPE__": esc(CONTENT["scope"]),
    "__FINDINGS__": note_items(CONTENT["findings"]), "__MODELS__": model_rows,
    "__BENCHMARKS__": bench_rows, "__ROUTE__": route_items,
    "__EXPERIMENTS__": experiment_rows, "__ACCEPTANCE__": listing(CONTENT["acceptance"]),
    "__BUDGET__": listing(CONTENT["budget"]), "__LIMITATIONS__": listing(CONTENT["limitations"]),
    "__SOURCES__": source_items,
    "__DATA__": json.dumps(bundle, ensure_ascii=False).replace("<", "\\u003c")
}
for key, value in replacements.items():
    document = document.replace(key, value)
assert not re.search(r"__[A-Z]+__", document), "Unfilled report token"
(ROOT / "REVE_评测驱动技术路线_20261113.html").write_text(document)

manifest = []
for path in sorted(SRC.iterdir()):
    if path.is_file():
        body = path.read_bytes()
        manifest.append(dict(file=str(path.relative_to(ROOT)), bytes=len(body), sha256=hashlib.sha256(body).hexdigest()))
(ROOT / "source_checksums.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
print(json.dumps({"records":len(RECORDS), "protocol_tasks":{p:len({r['task'] for r in rows}) for p,rows in groups.items()},
                  "models_reviewed":len(CONTENT['models']), "report":str(ROOT / "REVE_评测驱动技术路线_20261113.html")},ensure_ascii=False,indent=2))
