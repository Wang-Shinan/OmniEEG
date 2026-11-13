"""Render a self-contained Canvas from the reviewed, locally saved evidence."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
full = json.loads((ROOT / "review_bundle.json").read_text())
data = dict(content=full["content"], protocol_baselines=full["protocol_baselines"], records=[
    {k:r[k] for k in ["protocol", "task", "model", "mean", "dispersion", "metric", "unit", "source_id", "source_table"]}
    for r in full["records"]
])
template = r'''import { useState, useHostTheme, Stack, Row, Grid, H1, H2, H3, Text, Table, Pill, Link, Callout, Divider } from "cursor/canvas";

type Source = {id:string; title:string; url:string; location:string};
type Model = {name:string; role:string; design:string; evidence:string; limits:string; borrow:string; priority:string; source_ids:string[]};
type Benchmark = {name:string; use:string; protocol:string; limit:string; sources:string[]};
type Finding = {title:string; body:string; sources:string[]};
type Route = {name:string; why:string; spec:string; gate:string};
type Experiment = {id:string; comparison:string; question:string; control:string; decision:string};
type Content = {title:string; date:string; scope:string; decision:string; sources:Source[]; models:Model[]; benchmarks:Benchmark[]; findings:Finding[]; route:Route[]; experiments:Experiment[]; acceptance:string[]; budget:string[]; limitations:string[]};
type Result = {protocol:string; task:string; model:string; mean:number|null; dispersion:number|null; metric:string; unit:string; source_id:string; source_table:string};
const DATA: {content:Content; protocol_baselines:Record<string,string>; records:Result[]} = __DATA__;
const C = DATA.content;
const SOURCES = Object.fromEntries(C.sources.map(s => [s.id, s]));
const REPORT = "/Users/wangshinan/Desktop/OmniEEG/research/reve_route_20261113/REVE_评测驱动技术路线_20261113.html";
const fmt = (x: number | null) => x === null ? "—" : x.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");

function Refs({ids}: {ids: string[]}) {
  return <Row gap={8} wrap>{ids.map(id => <Link key={id} href={SOURCES[id].url}>[{id}]</Link>)}</Row>;
}

export default function ReveReview() {
  const theme = useHostTheme();
  const [tab, setTab] = useState("关键判断");
  const [protocol, setProtocol] = useState("NeuralBench FT");
  const [task, setTask] = useState("Schizophrenia");
  const [model, setModel] = useState("REVE");
  const protocols = Array.from(new Set(DATA.records.map(r => r.protocol)));
  const tasks = Array.from(new Set(DATA.records.filter(r => r.protocol === protocol).map(r => r.task))).sort();
  const activeTask = tasks.includes(task) ? task : tasks[0];
  const rows = DATA.records.filter(r => r.protocol === protocol && r.task === activeTask).sort((a,b) => (b.mean ?? -Infinity) - (a.mean ?? -Infinity));
  const source = rows[0];
  const baselineName = DATA.protocol_baselines[protocol];
  const baseline = rows.find(r => r.model === baselineName);
  const selected = C.models.find(m => m.name === model) || C.models[0];
  const selectStyle = { color: theme.text.primary, background: theme.bg.editor, border: `1px solid ${theme.stroke.primary}`, padding: "7px 10px", borderRadius: 4, maxWidth: "100%", font: "inherit", fontSize: 13 };
  const nav = ["关键判断", "逐任务证据", "14项模型", "评测协议", "具体路线", "实验与预算"];
  return <Stack gap={20} style={{padding:24, maxWidth:1280, margin:"0 auto", color:theme.text.primary}}>
    <Text size="small" tone="secondary">OMNIEEG / 2026-11-13 / 公开结果审阅，尚未运行本项目实验</Text>
    <H1>以 REVE 为起点：用评测决定改什么</H1>
    <Text style={{fontSize:16, lineHeight:1.8}}>{C.decision}</Text>
    <Row gap={8} wrap>{nav.map(t => <Pill key={t} active={t===tab} onClick={() => setTab(t)}>{t}</Pill>)}</Row>
    <Divider />

    {tab === "关键判断" && <Stack gap={20}>
      <Callout tone="info" title="当前决定">先核验 REVE 适配和读出，再测试一个局部时频残差分支；频段平衡目标独立消融。公开权重成绩不能证明从零预训练成绩。</Callout>
      {C.findings.map((f,i) => <Stack key={f.title} gap={8} style={{borderTop:i ? `1px solid ${theme.stroke.tertiary}` : undefined,paddingTop:i ? 18 : 0}}><H2>{f.title}</H2><Text>{f.body}</Text><Refs ids={f.sources}/></Stack>)}
      <Link href={REPORT}>打开完整离线报告及数据下载入口</Link>
    </Stack>}

    {tab === "逐任务证据" && <Stack gap={14}>
      <H2>同一协议、同一任务内比较</H2>
      <Row gap={16} wrap>
        <label>结果来源 <select aria-label="结果来源" style={selectStyle} value={protocol} onChange={e => setProtocol(e.target.value)}>{protocols.map(p=><option key={p} value={p}>{p}</option>)}</select></label>
        <label>任务 <select aria-label="任务" style={selectStyle} value={activeTask} onChange={e=>setTask(e.target.value)}>{tasks.map(t=><option key={t} value={t}>{t}</option>)}</select></label>
      </Row>
      <Text weight="semibold">{activeTask} · {source.metric} · 单位：{source.unit}</Text>
      <Text tone="secondary">{baseline?.mean != null ? `${baselineName}：${fmt(baseline.mean)}。差值按“该模型均值 − 基线均值”计算。` : "源表没有可比的REVE值，不计算REVE差距。"}</Text>
      <Table headers={["模型","源表均值","源离散度字段","与REVE基线的差值"]} rows={rows.map(r=>[r.model,fmt(r.mean),fmt(r.dispersion),r.mean!==null && baseline?.mean!=null ? `${r.mean-baseline.mean>=0?"+":""}${fmt(r.mean-baseline.mean)}${r.unit==="%"?" pp":""}`:"—"])} columnAlign={["left","right","right","right"]} striped />
      <Text size="small" tone="secondary">{protocol} / {source.source_table}。NeuralBench 百分数与0–1系数保持各自量纲；OmniEEG BACC由0–1乘100转为%。缺失项不计为0，源离散度不作显著性推断。</Text>
      <Refs ids={[source.source_id]}/>
      <Callout tone="warning">NeuralBench部分任务采用同被试留概念划分；FAME子集的被试隔离描述不充分。不同来源的分数不能相减，表内胜负也不能自动归因于某个模块。</Callout>
    </Stack>}

    {tab === "14项模型" && <Stack gap={16}>
      <H2>关键设计、证据、局限与借鉴</H2>
      <Row gap={7} wrap>{C.models.map(m=><Pill key={m.name} active={m.name===model} onClick={()=>setModel(m.name)}>{m.name}</Pill>)}</Row>
      <Row gap={12} wrap><H3>{selected.name}</H3><Pill>{selected.role}</Pill><Pill>{selected.priority}</Pill></Row>
      <Grid columns="repeat(auto-fit,minmax(280px,1fr))" gap={24}>
        <Stack gap={8}><H3>关键设计</H3><Text>{selected.design}</Text><H3>公开评测证据</H3><Text>{selected.evidence}</Text></Stack>
        <Stack gap={8}><H3>解释边界</H3><Text>{selected.limits}</Text><H3>可借鉴之处（待验证）</H3><Text>{selected.borrow}</Text></Stack>
      </Grid>
      <Refs ids={selected.source_ids}/>
      <Divider/>
      <Table headers={["工作","作用","优先级"]} rows={C.models.map(m=>[m.name,m.role,m.priority])} />
      <Text size="small" tone="secondary">P0：首先建立的基线；P1：优先验证模块；P2：后备；P3：本轮暂缓。不是完整模型性能排序。</Text>
    </Stack>}

    {tab === "评测协议" && <Stack gap={18}>
      <H2>四种评测体系分别回答什么</H2>
      {C.benchmarks.map(b=><Stack key={b.name} gap={7}><H3>{b.name}</H3><Text>{b.use}</Text><Text tone="secondary">协议：{b.protocol}</Text><Text>边界：{b.limit}</Text><Refs ids={b.sources}/><Divider/></Stack>)}
      <Callout tone="info" title="赛事协议">按被试8:1:1隔离；三个指定种子分别重新划分；验证BACC选权重；两个数据集等权形成分赛道分数；主赛道按名次积分累计。外部benchmark不替代赛事协议。</Callout>
    </Stack>}

    {tab === "具体路线" && <Stack gap={20}>
      <H2>REVE全局表征 + 轻量局部时频残差</H2>
      <Grid columns="repeat(auto-fit,minmax(240px,1fr))" gap={14}>
        {[['全局分支','200Hz EEG → REVE tokens → 结构化读出 → g_global'],['局部分支（待验证）','同一片段 → 多尺度滤波/功率 → 小型时空聚合 → g_local'],['融合','logits = Wg·g_global + α·Wl·g_local；α从0学习']].map(([title,body])=><Stack key={title} gap={6} style={{padding:16, background:theme.fill.tertiary}}><H3>{title}</H3><Text>{body}</Text></Stack>)}
      </Grid>
      {C.route.map(s=><Stack key={s.name} gap={8}><H3>{s.name}</H3><Text tone="secondary">{s.why}</Text><Text>{s.spec}</Text><Text weight="medium">保留/停止条件：{s.gate}</Text><Divider/></Stack>)}
      <Callout tone="warning">决赛所有模块随机初始化。复赛公开REVE权重、外部预训练LLM、预训练位置模块或教师蒸馏都不能默认带入从零训练阶段。</Callout>
    </Stack>}

    {tab === "实验与预算" && <Stack gap={20}>
      <H2>每个组件都对应一个可证伪的问题</H2>
      <Table headers={["编号","比较","问题","控制条件","保留条件"]} rows={C.experiments.map(e=>[e.id,e.comparison,e.question,e.control,e.decision])} />
      <H3>项目选型门槛（建议，非赛事规则）</H3>{C.acceptance.map(a=><Text key={a}>{a}</Text>)}
      <H3>资源预算（建议，须实测）</H3>{C.budget.map(b=><Text key={b}>{b}</Text>)}
      <H3>证据局限</H3>{C.limitations.map(l=><Text key={l} tone="secondary">{l}</Text>)}
    </Stack>}
    <Divider/>
    <Text size="small" tone="secondary">{C.scope} NeuralBench静态数据固定至fe31393；所有新增配置均为设计起点，未宣称实测有效。</Text>
    <Link href={REPORT}>完整报告、23条来源与CSV</Link>
  </Stack>;
}
'''
code = template.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
target = Path('/Users/wangshinan/.cursor/projects/Users-wangshinan-Desktop-OmniEEG/canvases/REVE-route-review.canvas.tsx')
target.write_text(code)
print(target)
print('bytes:',len(code.encode()))
