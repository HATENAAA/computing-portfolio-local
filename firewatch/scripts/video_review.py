"""Self-contained, escaped review page with evidence for negative rule results."""
import html
import json


def render_review(report, rows):
    if report.get("decision_engine")=="model":
        from scripts.model_review import render_model_review
        return render_model_review(report,rows)
    esc=lambda value: html.escape(str(value),quote=True)
    d=report['diagnostics'];cfg=report['config'];events=report['events']
    if events:
        headline=f"已生成 {len(events)} 个候选事件"
        explanation='候选事件由连续采样帧通过颜色、面积及边缘规则后形成，请结合下方图像人工复核。'
    elif not d['candidate_frames']:
        headline='视频已处理，未形成候选事件'
        explanation=(f"{report['sampled_frames']} 个采样帧均未通过完整规则。"
            f"边缘颜色支持比例最高为 {d['max_edge_ratio']:.1%}，当前门槛为 {cfg['edge_ratio']:.0%}。"
            if d['reason_counts']['edge_below_threshold']==report['sampled_frames'] else
            '所有采样帧均未通过完整规则，具体筛选原因见下方统计。')
    else:
        headline='有单帧候选，未达到连续确认条件'
        explanation=f"最长连续命中 {d['longest_candidate_run']} 帧，需要连续 {report['on_frames']} 帧才能形成事件。"
    event_rows=''.join(f"<tr><td>事件 {i+1:02d}</td><td>{e['start']:.2f} s</td><td>{e['confirmed_at']:.2f} s</td><td>{e['end']:.2f} s</td></tr>" for i,e in enumerate(events))
    event_content=(f'<div class="table-wrap"><table><thead><tr><th>候选事件</th><th>起始</th><th>确认</th><th>结束</th></tr></thead><tbody>{event_rows}</tbody></table></div>' if events else
        '<div class="empty">本次没有事件区间。请查看规则得分与代表帧；0 个候选事件不等于画面中没有火焰。</div>')
    figures=''.join(f'''<figure><a href="{esc(s['file'])}" target="_blank" rel="noopener"><img loading="lazy" src="{esc(s['file'])}" alt="{s['time_s']:.2f} 秒的规则区域叠加图"></a><figcaption><b>{s['time_s']:.2f} s</b><span>{'规则命中' if s['candidate'] else '未通过完整规则'}</span><small>边缘支持 {s['best_edge_ratio']:.1%} · 颜色区域 {s['area_ratio']:.1%}</small></figcaption></figure>''' for s in report['review_frames'])
    duration=max(rows[-1]['time_s'],.01)
    def points(key):
        return ' '.join(f"{48+832*r['time_s']/duration:.1f},{185-150*r[key]:.1f}" for r in rows)
    threshold_y=185-150*cfg['edge_ratio']
    ticks=''.join(f'<text x="{48+832*f:.1f}" y="210" text-anchor="middle">{duration*f:.1f}s</text>' for f in (0,.25,.5,.75,1))
    evaluation=('<p>本次未提供人工事件标注，因此未计算 Precision / Recall。标注仅用于评价，不是检测运行的前提。</p>' if 'event_evaluation' not in report else
        '<pre>'+esc(json.dumps(report['event_evaluation'],ensure_ascii=False,indent=2))+'</pre>')
    reasons=''.join(f'<span>{label} <b>{d["reason_counts"][key]}</b> 帧</span>' for key,label in [('no_color_region','无有效颜色区域'),('area_below_threshold','区域面积不足'),('edge_below_threshold','边缘支持不足'),('candidate','完整规则命中')])
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FireWatch · 视频分析报告</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f6fa;color:#253147;font:14px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}a{{color:#2563b9;text-decoration:none}}a:hover{{text-decoration:underline}}header{{background:#fff;border-bottom:1px solid #e0e7ef;padding:16px max(24px,calc((100vw - 1120px)/2));display:flex;gap:24px;align-items:center}}header b{{font-size:16px;letter-spacing:.02em}}header span{{color:#778399;flex:1}}main{{max-width:1120px;margin:30px auto;padding:0 24px 40px}}.top{{display:flex;justify-content:space-between;align-items:center;gap:24px}}h1{{font-size:28px;line-height:1.3;margin:0 0 8px}}.muted,small{{color:#738096}}.exports{{display:flex;gap:10px;flex-wrap:wrap}}.exports a{{background:#fff;border:1px solid #dce4ee;border-radius:9px;padding:8px 14px;white-space:nowrap}}.insight{{border-left:4px solid #4777c7;background:#edf3ff;padding:18px 22px;margin:24px 0;border-radius:4px 12px 12px 4px}}.insight strong{{font-size:17px}}.insight p{{margin:6px 0 0}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.stats div,section{{background:#fff;border:1px solid #e0e7ef;border-radius:14px}}.stats div{{padding:18px 22px}}.stats b{{font-size:28px;display:block}}section{{margin:20px 0;padding:22px}}h2{{font-size:17px;margin:0 0 8px}}section>p{{margin:4px 0 16px;color:#738096}}.legend{{display:flex;gap:22px;color:#64748b}}.legend i{{display:inline-block;width:18px;border-top:3px solid #3776ca;vertical-align:middle;margin-right:7px}}.legend .area{{border-color:#28a59c}}.legend .threshold{{border-color:#df9870;border-top-style:dashed}}svg{{width:100%;height:auto;display:block;font-size:11px;fill:#778399}}.reasons{{display:flex;gap:12px 24px;flex-wrap:wrap;border-top:1px solid #edf1f5;padding-top:12px;color:#64748b}}.empty{{background:#f7f9fc;border:1px dashed #d9e2ed;border-radius:10px;padding:20px;color:#64748b}}table{{border-collapse:collapse;width:100%;text-align:left}}td,th{{padding:12px;border-bottom:1px solid #edf1f5}}.table-wrap{{overflow:auto}}.frames{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}figure{{margin:0;border:1px solid #e0e7ef;border-radius:10px;overflow:hidden}}img{{width:100%;aspect-ratio:16/9;object-fit:contain;background:#131b29;display:block}}figcaption{{padding:10px 12px}}figcaption span{{float:right;font-size:12px;color:#738096}}figcaption small{{display:block;margin-top:3px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}.filename{{overflow-wrap:anywhere}}footer{{color:#738096;font-size:12px;margin-top:20px}}@media(max-width:720px){{.top{{display:block}}.exports{{margin-top:16px}}.frames{{grid-template-columns:repeat(2,1fr)}}.stats{{gap:8px}}.stats div{{padding:12px}}.stats b{{font-size:24px}}header{{gap:12px}}header span{{display:none}}main{{padding:0 14px}}section{{padding:16px}}}}
</style></head><body><header><b>▧ FireWatch</b><span>视频工作区 / 分析报告</span><a href="/video">返回视频任务 →</a></header><main>
<div class="top"><div><h1>视频分析报告</h1><div class="muted filename">{esc(report['source'])} · 已分析 {report['duration_analyzed_s']:.2f} 秒{' · 已达到分析时长上限' if report['truncated'] else ''}</div></div><nav class="exports"><a href="video-report.json">完整 JSON</a><a href="timeline.csv">逐帧 CSV</a></nav></div>
<div class="insight"><strong>{headline}</strong><p>{explanation}</p></div>
<div class="stats"><div><span class="muted">采样帧</span><b>{report['sampled_frames']}</b></div><div><span class="muted">规则命中帧</span><b>{d['candidate_frames']}</b></div><div><span class="muted">候选事件</span><b>{len(events)}</b></div></div>
<section><h2>规则得分时间线</h2><p>蓝线为四种边缘算子的最高颜色支持比例，绿线为颜色候选区域占比。两者均不是模型置信度。</p><div class="legend"><span><i></i>边缘支持</span><span><i class="area"></i>颜色区域</span><span><i class="threshold"></i>边缘门槛 {cfg['edge_ratio']:.0%}</span></div>
<svg viewBox="0 0 920 225" role="img" aria-label="逐帧边缘支持与颜色区域占比时间线"><path d="M48 35H880 M48 110H880 M48 185H880" stroke="#e9eef5" fill="none"/><text x="8" y="39">100%</text><text x="14" y="114">50%</text><text x="20" y="189">0%</text><path d="M48 {threshold_y:.1f}H880" stroke="#df9870" stroke-dasharray="6 5"/><polyline points="{points('area_ratio')}" stroke="#28a59c" stroke-width="2" fill="none"/><polyline points="{points('best_edge_ratio')}" stroke="#3776ca" stroke-width="2.5" fill="none"/>{ticks}</svg>
<div class="reasons">{reasons}</div></section>
<section><h2>候选事件</h2><p>连续 {report['on_frames']} 个采样帧命中后确认，连续 {report['off_frames']} 帧未命中后结束。</p>{event_content}</section>
<section><h2>代表帧复核</h2><p>按时间间隔保留代表帧，并补充最高边缘得分帧。橙色叠加与框仅表示颜色候选区域，未命中帧也会显示；点击可查看大图。</p><div class="frames">{figures}</div></section>
<section><h2>分析参数与评价</h2><p>亮度门槛 {cfg['brightness']} / 255 · 边缘支持门槛 {cfg['edge_ratio']:.0%} · 最小区域占比 {cfg['min_area_ratio']:.1%} · 目标采样上限 {report['sample_hz']:g} 帧 / 秒</p>{evaluation}<p>需要尝试其他参数时，可返回视频任务重新上传。降低门槛会增加候选，也可能增加误报，应通过独立标注视频比较。</p></section>
<footer>本项目使用颜色、亮度与边缘规则，尚未接入训练好的火焰检测模型。报告用于候选复核，不确认火灾或证明检测准确率。</footer></main></body></html>'''
