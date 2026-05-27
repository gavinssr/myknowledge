#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


SEVERITY_LABELS = {
    "critical": "严重风险",
    "high": "高风险",
    "medium": "中风险",
    "low": "低风险",
    "positive": "可借鉴",
}

CATEGORY_LABELS = {
    "flow_logic": "流程逻辑",
    "information_architecture": "信息架构",
    "visual_hierarchy": "视觉层级",
    "cta_strategy": "行动策略",
    "decision_cost": "决策成本",
    "trust_and_risk": "信任与风险",
    "copywriting": "文案表达",
    "state_feedback": "状态反馈",
    "error_recovery": "错误恢复",
    "conversion_pattern": "转化模式",
    "business_rule_exposure": "业务规则外显",
    "positive_reference": "正向参考",
}

PATTERNS = [
    "快速转化结构：人人租把低日租、优惠券、免押、热租榜和“可续租/可买”放在用户很早能看到的位置，降低进入商品详情后的第一层决策成本。",
    "生命周期状态：订单详情中的倒计时、四段进度条和底部动作清楚告诉用户当前处于哪一步、下一步是什么。",
    "证据链管理：发货视频、签收视频/图片、归还图片/视频和交易视频记录构成了高价值租赁设备的风控闭环。",
    "规则图像化：归还前用示例图说明需要拍哪些角度，比单纯文字规则更适合移动端执行。",
]

RISKS = [
    "不要让低日租掩盖全周期成本。用户最终需要同时理解首期、总租金、到期买断、押金减免和可能后扣费用。",
    "不要把风险提示都做成红色大块。反欺诈、违约、安全交易都重要，但同屏争夺注意力会削弱主任务。",
    "不要把实名、人脸、地址一致和本人签收拆成孤立提示。它们本质上是同一条风控任务链。",
    "不要在强调证据重要性的同时轻易允许跳过。若业务允许跳过，需要明确跳过后的纠纷处理风险。",
]

RECOMMENDATIONS = [
    "成本解释组件：在商详、下单和订单详情里统一展示“今日应付、全周期预计、押金/免押状态、到期买断价”，并解释这些金额之间的关系。",
    "风控任务组件：把实名、人脸、本人签收、地址一致、证据上传组织成可完成的任务列表，而不是散落在多个页面里的提示条。",
    "订单状态组件：复用“状态 + 进度 + 下一步动作 + 剩余时间”的结构，覆盖待付款、待发货、待收货、租用中、归还中和完成。",
    "证据上传策略：保留示例图，但对“跳过”明确后果；对于高价值设备，建议把最小证据要求设为必传。",
    "风险提示分层：将高频安全提示做成常驻轻量条，把详细解释收进二级面板或确认弹层，避免所有风险都用红色大块表达。",
]


def e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def read_json(name: str) -> dict[str, Any]:
    with (ROOT / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def list_html(items: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    rows = "\n".join(f"<li>{e(item)}</li>" for item in items)
    return f"<{tag}>{rows}</{tag}>"


def badge(point: dict[str, Any]) -> str:
    severity = str(point.get("severity", "medium"))
    return f'<span class="badge badge-{e(severity)}">{e(SEVERITY_LABELS.get(severity, severity))}</span>'


def category(point: dict[str, Any]) -> str:
    raw = str(point.get("category", ""))
    return CATEGORY_LABELS.get(raw, raw)


def render_metric_cards(counts: Counter[str]) -> str:
    order = [("high", "高风险"), ("medium", "中风险"), ("positive", "可借鉴")]
    cards = []
    for key, label in order:
        value = counts.get(key, 0)
        cards.append(f'<div class="metric metric-{key}"><span>{value}</span><p>{label}</p></div>')
    return "\n".join(cards)


def render_lanes(flow: list[dict[str, Any]]) -> str:
    lanes = []
    for item in flow:
        screens = "、".join(item.get("screens", []))
        lanes.append(
            f"""
            <div class="lane">
              <strong>{e(item.get("stage"))}</strong>
              <p>{e(item.get("notes"))}</p>
              <small>{e(screens)}</small>
            </div>
            """
        )
    return "\n".join(lanes)


def render_findings_table(points: list[dict[str, Any]]) -> str:
    rows = []
    for point in points:
        pid = point.get("point_id")
        sid = point.get("screen_id")
        rows.append(
            f"""
            <tr>
              <td><a href="#{e(pid)}">{e(pid)}</a></td>
              <td>{badge(point)}</td>
              <td>{e(category(point))}</td>
              <td><a href="#{e(sid)}">{e(point.get("screen_name"))}</a></td>
              <td><strong>{e(point.get("title"))}</strong><p>{e(point.get("insight"))}</p></td>
              <td>{e(point.get("recommendation"))}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def render_finding(point: dict[str, Any]) -> str:
    pid = point.get("point_id")
    return f"""
    <article class="finding" id="{e(pid)}">
      <div class="finding-head">
        <span class="point-id">{e(pid)}</span>
        {badge(point)}
        <span class="cat">{e(category(point))}</span>
      </div>
      <h4>{e(point.get("title"))}</h4>
      <dl>
        <dt>目标区域</dt><dd>{e(point.get("target"))}</dd>
        <dt>洞察</dt><dd>{e(point.get("insight"))}</dd>
        <dt>证据</dt><dd>{e(point.get("evidence"))}</dd>
        <dt>建议</dt><dd>{e(point.get("recommendation"))}</dd>
      </dl>
    </article>
    """


def render_screen_cards(points: list[dict[str, Any]]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in points:
        grouped[str(point.get("screen_id"))].append(point)

    cards = []
    for screen_id in sorted(grouped):
        screen_points = grouped[screen_id]
        screen_name = screen_points[0].get("screen_name", screen_id)
        findings = "\n".join(render_finding(point) for point in screen_points)
        cards.append(
            f"""
            <section class="screen-card" id="{e(screen_id)}">
              <div class="screen-media">
                <a href="screens/{e(screen_id)}.png" target="_blank" rel="noreferrer">
                  <img src="screens/{e(screen_id)}.png" alt="{e(screen_id)} {e(screen_name)} 截图">
                </a>
              </div>
              <div class="screen-notes">
                <p class="eyebrow">{e(screen_id)}</p>
                <h3>{e(screen_name)}</h3>
                {findings}
              </div>
            </section>
            """
        )
    return "\n".join(cards)


def main() -> None:
    data = read_json("analysis_points.json")
    manifest = read_json("screen_manifest.json")
    summary = data["summary"]
    points = data["points"]
    counts = Counter(point.get("severity", "medium") for point in points)
    flow = data.get("flow_structure", [])
    quality_notes = data.get("quality_notes", [])

    source_name = "人人租.pdf"
    source_file = data.get("source_file", "")
    if source_file:
        source_name = Path(str(source_file)).name

    appendix = [
        *quality_notes,
        f"自动切屏数量：{manifest.get('screen_count')}。切屏结果已通过 screen_contact_sheet.png 和 segmentation_check.png 视觉检查。",
        "每个分析点都保留 anchor.local_bbox 与 global_anchor_bbox，可在 analysis_points.json 中复核。",
        "部分小字号金额、长协议文本和被打码的收货地址/手机号不作为精确业务事实使用。",
        "本报告不判断实际合规性，只分析界面中可见提示、解释方式和用户理解成本。",
    ]

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>人人租竞品流程分析报告</title>
  <style>
    :root {{
      --bg: #f5f6f8;
      --surface: #ffffff;
      --ink: #171a1f;
      --muted: #5f6875;
      --line: #dfe3ea;
      --blue: #1769e0;
      --green: #198754;
      --amber: #b7791f;
      --orange: #c65d14;
      --red: #c53030;
      --shadow: 0 18px 48px rgba(23, 26, 31, .08);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      line-height: 1.65;
    }}
    a {{ color: var(--blue); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .layout {{ display: grid; grid-template-columns: 264px minmax(0, 1fr); min-height: 100vh; }}
    nav {{
      position: sticky;
      top: 0;
      height: 100vh;
      padding: 28px 22px;
      background: #111418;
      color: white;
      overflow: auto;
    }}
    nav h1 {{ font-size: 18px; line-height: 1.25; margin: 0 0 8px; }}
    nav p {{ color: #aeb7c4; margin: 0 0 24px; font-size: 13px; }}
    nav a {{ display: block; color: #e8edf5; padding: 8px 0; font-size: 14px; }}
    main {{ padding: 40px clamp(24px, 4vw, 64px) 72px; max-width: 1440px; width: 100%; }}
    .hero {{
      background: linear-gradient(135deg, #ffffff 0%, #eef5ff 100%);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: clamp(28px, 4vw, 48px);
      box-shadow: var(--shadow);
    }}
    .eyebrow {{ color: var(--muted); font-size: 13px; letter-spacing: 0; margin: 0 0 8px; }}
    h2 {{ margin: 44px 0 16px; font-size: 26px; line-height: 1.25; }}
    h3 {{ margin: 0 0 12px; font-size: 20px; line-height: 1.35; }}
    h4 {{ margin: 10px 0 12px; font-size: 16px; line-height: 1.45; }}
    .hero h1 {{ margin: 0; font-size: clamp(34px, 5vw, 58px); line-height: 1.08; letter-spacing: 0; }}
    .hero .summary {{ max-width: 920px; font-size: 18px; color: #303742; margin: 22px 0 0; }}
    .meta {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 24px; }}
    .pill {{ border: 1px solid var(--line); background: rgba(255,255,255,.72); border-radius: 999px; padding: 7px 12px; color: #374151; font-size: 13px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 12px; margin-top: 22px; }}
    .metric {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
    .metric span {{ font-size: 30px; font-weight: 760; display: block; line-height: 1; }}
    .metric p {{ margin: 6px 0 0; color: var(--muted); }}
    .section {{ background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 24px; box-shadow: 0 8px 28px rgba(23,26,31,.04); margin-top: 18px; }}
    .twocol {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .lane-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
    .lane {{ border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: #fbfcfe; }}
    .lane p {{ margin: 6px 0 8px; color: var(--muted); }}
    .lane small {{ color: #7a8490; font-size: 12px; }}
    .image-panel {{ background: #101214; border-radius: 10px; padding: 16px; overflow: auto; }}
    .image-panel img {{ display: block; max-width: 100%; min-width: 980px; border-radius: 4px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 12px 10px; vertical-align: top; text-align: left; }}
    th {{ color: #4b5563; font-weight: 680; background: #f8fafc; position: sticky; top: 0; }}
    td p {{ margin: 4px 0 0; color: var(--muted); }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; }}
    .badge {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 3px 9px; font-size: 12px; font-weight: 680; white-space: nowrap; }}
    .badge-positive {{ color: #0f6b3e; background: #e6f6ee; }}
    .badge-medium {{ color: #83520d; background: #fff4d6; }}
    .badge-high {{ color: #9a3d0a; background: #ffe8d6; }}
    .badge-low {{ color: #164c9c; background: #e7f0ff; }}
    .badge-critical {{ color: #991b1b; background: #fee2e2; }}
    .screen-card {{
      display: grid;
      grid-template-columns: minmax(180px, 270px) minmax(0, 1fr);
      gap: 24px;
      align-items: start;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 18px;
      margin-top: 18px;
      box-shadow: 0 8px 28px rgba(23,26,31,.04);
    }}
    .screen-media {{ background: #edf0f5; border-radius: 8px; padding: 10px; text-align: center; }}
    .screen-media img {{ max-width: 100%; max-height: 680px; object-fit: contain; border-radius: 4px; box-shadow: 0 10px 26px rgba(23,26,31,.16); }}
    .finding {{ border-top: 1px solid var(--line); padding-top: 16px; margin-top: 16px; }}
    .finding:first-of-type {{ border-top: 0; padding-top: 0; }}
    .finding-head {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
    .point-id {{ font-weight: 800; color: var(--blue); }}
    .cat {{ color: var(--muted); font-size: 13px; }}
    dl {{ display: grid; grid-template-columns: 84px minmax(0, 1fr); gap: 8px 12px; margin: 0; }}
    dt {{ color: var(--muted); font-weight: 680; }}
    dd {{ margin: 0; }}
    .list-card ul, .list-card ol {{ margin: 0; padding-left: 22px; }}
    .list-card li + li {{ margin-top: 8px; }}
    footer {{ margin-top: 44px; color: var(--muted); font-size: 13px; }}
    .anchor-alias {{ display: block; position: relative; top: -20px; visibility: hidden; }}
    @media (max-width: 980px) {{
      .layout {{ grid-template-columns: 1fr; }}
      nav {{ position: relative; height: auto; }}
      main {{ padding: 24px 16px 48px; }}
      .twocol, .screen-card {{ grid-template-columns: 1fr; }}
      .image-panel img {{ min-width: 720px; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <nav>
      <h1>人人租<br>竞品流程分析</h1>
      <p>HTML 阅读版 · {date.today().isoformat()}</p>
      <a href="#scope">输入与范围</a>
      <a href="#overview">流程结构</a>
      <a href="#conclusion">执行结论</a>
      <a href="#flow">标注总图</a>
      <a href="#findings">关键发现</a>
      <a href="#screens">分屏分析</a>
      <a href="#patterns">可借鉴模式</a>
      <a href="#risks">风险与建议</a>
      <a href="#appendix">附录</a>
    </nav>
    <main>
      <header class="hero" id="top">
        <p class="eyebrow">{e(summary.get("competitor"))} · {e(summary.get("flow_name"))}</p>
        <h1>人人租竞品流程分析报告</h1>
        <p class="summary">{e(summary.get("overall_assessment"))}</p>
        <div class="meta">
          <span class="pill">输入：{e(source_name)}</span>
          <span class="pill">屏幕：{e(manifest.get("screen_count"))} 个</span>
          <span class="pill">分析点：{len(points)} 个</span>
          <span class="pill">标注画布：{e(manifest.get("canvas_width"))} × {e(manifest.get("canvas_height"))}</span>
        </div>
        <div class="metrics">{render_metric_cards(counts)}</div>
      </header>

      <h2 id="scope">1. 输入与范围</h2>
      <section class="section list-card">
        <ul>
          <li>输入文件：{e(source_file)}</li>
          <li>输出目录：outputs/renrenzu-rental</li>
          <li>分析对象：已拼接的人人租移动端竞品流程图，覆盖首页、商品详情、下单配置、实名认证/人脸/免押、订单状态、账单、续租、买断、归还物流与证据上传。</li>
          <li>方法说明：先将 PDF 渲染为 canvas.png，再自动切分 {e(manifest.get("screen_count"))} 个屏幕截图；随后基于可见 UI 文案、层级、状态与业务信息生成结构化分析点。</li>
        </ul>
      </section>

      <h2 id="overview">2. 流程结构概览</h2>
      <section class="lane-grid">{render_lanes(flow)}</section>

      <h2 id="conclusion">3. 执行结论</h2>
      <section class="section twocol">
        <div class="list-card">
          <h3>核心发现</h3>
          {list_html(summary.get("primary_takeaways", []))}
        </div>
        <div class="list-card">
          <h3>设计机会</h3>
          {list_html(summary.get("design_opportunities", []))}
        </div>
      </section>

      <span id="image" class="anchor-alias" aria-hidden="true"></span>
      <h2 id="flow">4. 标注总图</h2>
      <section class="section">
        <p class="eyebrow">点击图片可打开原始大图。标注点 A1-A16 与下方关键发现表、分屏分析一一对应。</p>
        <div class="image-panel"><a href="annotated_flow.png" target="_blank" rel="noreferrer"><img src="annotated_flow.png" alt="人人租流程标注总图"></a></div>
      </section>

      <h2 id="findings">5. 关键发现列表</h2>
      <section class="section">
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>严重度</th><th>分类</th><th>页面</th><th>洞察</th><th>建议</th></tr></thead>
            <tbody>{render_findings_table(points)}</tbody>
          </table>
        </div>
      </section>

      <h2 id="screens">6. 分屏分析</h2>
      {render_screen_cards(points)}

      <h2 id="patterns">7. 值得学习的模式</h2>
      <section class="section list-card">{list_html(PATTERNS)}</section>

      <h2 id="risks">8. 风险与行动建议</h2>
      <section class="section twocol">
        <div class="list-card"><h3>需要避免的风险</h3>{list_html(RISKS)}</div>
        <div class="list-card"><h3>行动建议</h3>{list_html(RECOMMENDATIONS, ordered=True)}</div>
      </section>

      <h2 id="appendix">9. 附录：检测置信度与未解决歧义</h2>
      <section class="section list-card">{list_html(appendix)}</section>

      <footer>相关文件：<a href="analysis_points.json">analysis_points.json</a> · <a href="screen_manifest.json">screen_manifest.json</a> · <a href="screen_contact_sheet.png">screen_contact_sheet.png</a> · <a href="segmentation_check.png">segmentation_check.png</a> · <a href="report.md">report.md</a></footer>
    </main>
  </div>
</body>
</html>
"""

    (ROOT / "report.html").write_text(html_text, encoding="utf-8")


if __name__ == "__main__":
    main()
