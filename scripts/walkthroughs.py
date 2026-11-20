"""Self-contained examples for the public project pages."""

import csv
from html import escape


def group(page, items, label, anchor, stepper=False):
    picker = page.select('workflow-picker', [(key, title) for key, title, _ in items])
    panels = ''.join(f'<section data-workflow-panel="{key}"><h3>{title}</h3>{body}</section>'
                     for key, title, body in items)
    controls = ''
    if stepper:
        controls = (f'<div class="actions step-controls">'
                    f'<button type="button" data-workflow-step="-1">{page.t("Previous step","上一步")}</button>'
                    f'<button type="button" data-workflow-step="1">{page.t("Next step","下一步")}</button></div>')
    return (f'<div id="{anchor}" data-workflow-picker><div class="workflow-controls" hidden>'
            f'<label>{label} {picker}</label>{controls}</div>{panels}</div>')


def paragraph(text):
    return '<p>' + text + '</p>'


def hsi(page, root, table):
    t = page.t
    def results(filename, scale):
        with (root / 'assets/evidence' / filename).open(newline='', encoding='utf-8') as stream:
            records = list(csv.reader(stream))[1:]
        rows = [(row[1].replace('- ', '-'), *row[2:]) for row in records if row[0] == scale+'×']
        return table([t('Method','方法'),'PSNR ↑ (dB)','SSIM ↑','CC ↑','RMSE ↓','SAM ↓ (°)','ERGAS ↓'],rows)
    def gallery(dataset):
        options = [
            ('HR_GroundTruth',t('High-resolution reference','高分辨率参考')),
            ('Bicubic_x4',t('Bicubic baseline','双三次插值基线')),
            ('MCArb_MCnet_x4','MCArb-MCNet'),
            ('MCArb_SSPSR_x4','MCArb-SSPSR'),
            ('MCArb_ERCSR_x4','MCArb-ERCSR'),
        ]
        prefix=f'hsi-sr-lab/thesis-final/images/{dataset}/'
        return '<details><summary>'+t('Open the ×4 reference and model outputs','展开 ×4 参考图与模型输出')+'</summary><div class="thumbs">'+''.join(
            page.img(prefix+name+'.png',label) for name,label in options)+'</div></details>'
    items=[]
    for code,dataset,file in [('pavia','Pavia Centre','pavia-table-4-1.csv'),('chikusei','Chikusei','chikusei-table-4-2.csv')]:
        for scale in ('4','8'):
            description=results(file,scale)
            if scale=='4':
                description+=gallery(code)
            items.append((code+scale,dataset+' ×'+scale,description))
    intro=t('MATLAB prepares paired low- and high-resolution cubes. Training covers three baselines and their MCArb variants. The Python evaluation compares reconstructed images with references across six metrics.','MATLAB 用于准备低、高分辨率成对的高光谱数据。训练覆盖三类基线及对应的 MCArb 模型，Python 评测流程对照重建结果与参考图像，计算六项指标。')
    ablations=[]
    for title,filename in [
        (t('Collaborative learning on Chikusei','Chikusei 协同学习'),'4.3_Chikusei_collaboration.csv'),
        (t('Collaborative learning on Pavia Centre','Pavia Centre 协同学习'),'4.4_Pavia_collaboration.csv'),
        (t('3D upsampling on Pavia Centre','Pavia Centre 三维上采样'),'4.5_Pavia_3D_ablation.csv'),
        (t('Cross-scale alignment on Pavia Centre','Pavia Centre 跨尺度对齐'),'4.6_Pavia_3DSPPM.csv'),
    ]:
        link=page.link('hsi-sr-lab/evidence/'+filename,t('Download the original table','下载原表'))
        with (root / 'hsi-sr-lab/evidence' / filename).open(newline='', encoding='utf-8-sig') as stream:
            headers,*rows=list(csv.reader(stream))
        ablations.append(f'<details><summary>{title}</summary>{table([escape(h) for h in headers],rows)}<p>{link}</p></details>')
    auxiliary_filename='hsi-auxiliary-table.csv'
    with (root / 'assets/evidence' / auxiliary_filename).open(newline='', encoding='utf-8') as stream:
        auxiliary=list(csv.reader(stream))[1:]
    aux_details=[]
    for panel,label in [('(a)',t('Auxiliary scale','辅助上采样倍率')),('(b)',t('Crop-area ratio','裁剪面积比例'))]:
        aux_details.append(f'<h3>{label}</h3>'+table([t('Reconstruction scale','重建倍率'),t('Variant','配置'),'PSNR ↑','SSIM ↑','CC ↑','RMSE ↓','SAM ↓','ERGAS ↓'],[row[1:] for row in auxiliary if row[0]==panel]))
    note=paragraph(t('The thesis adopted ×2 auxiliary upscaling and a 25% crop-area ratio as the joint configuration. Individual metrics can favour other crop ratios.','论文采用 ×2 辅助上采样与 25% 裁剪面积作为最终组合。单项指标在其他裁剪比例下也可能更好。'))
    download=paragraph(page.source(auxiliary_filename,t('Download transcribed Table 4.7','下载从论文原文整理的表 4.7')))
    ablations.append('<details><summary>'+t('Auxiliary scale and crop area','辅助倍率与裁剪面积')+'</summary>'+note+''.join(aux_details)+download+'</details>')
    return paragraph(intro)+group(page,items,t('Dataset and scale','数据集与倍率'),'reconstruction-table')+'<h3 id="ablation-results">'+t('Ablation and parameter results','消融与参数结果')+'</h3>'+''.join(ablations)


def vrfitai(page):
    t=page.t
    items=[]
    for key,image,title,body in [
        ('course','vr-flow-course.jpg',t('1 · Select a 30-second session','1 · 选择 30 秒课程'),t('Select the 30-second desktop trial from the course lobby.','在课程大厅选择「试练 30 秒」。')),
        ('active','vr-flow-active.jpg',t('2 · Start desktop practice','2 · 启动桌面训练'),t('The elapsed-time checkpoint is written while the session is active.','训练进行中保存计时检查点。')),
        ('paused','vr-flow-paused.jpg',t('3 · Refresh and continue','3 · 刷新后继续'),t('Refreshing restores the same session in a paused state. The user resumes it explicitly.','刷新后恢复同一场训练，界面暂停等待用户主动继续。')),
        ('summary','vr-flow-summary.jpg',t('4 · End and review the record','4 · 结束并查看记录'),t('After resuming and ending the session, the summary shows the active time and hits for that session. The record is saved.','继续训练后结束，结果页显示本次有效训练时间与命中数，并确认训练记录已保存。')),
    ]:
        items.append((key,title,paragraph(body)+page.img('assets/evidence/'+image,title)))
    return paragraph(t('Follow one 30-second desktop trial from the course lobby through refresh, resumption and saving.','以下四张截图来自同一场 30 秒桌面试练，记录选课、刷新恢复和保存。'))+group(page,items,t('Replay step','回放步骤'),'training-replay',stepper=True)


def manufacturing(page, table, record):
    t=page.t
    status=[t('Order','订单'),t('Status','状态'),t('Quantity','数量'),t('Version','版本')]
    items=[]
    for key,title,details in [
        ('submit',t('1 · Submit the order','1 · 提交订单'),t('The distributor submits the product, quantity and factory.','经销商提交产品、数量与工厂。')),
        ('accept',t('2 · Accept at the factory','2 · 工厂接单'),t('The factory accepts the order. The version changes and the transition appears in the audit history.','工厂接单后订单版本更新，状态转换写入审计历史。')),
    ]:
        row=record[key]
        items.append((key,title,paragraph(details)+table(status,[(row['product'],row['status'],row['quantity'],row['version'])])))
    rows=[(line['sku'],line['quantity'],line['held']) for line in record['reserve']['lines']]
    items.append(('reserve',t('3 · Reserve from the BOM','3 · 按物料清单预留'),paragraph(t('The order snapshots its bill of materials. The reservation quantities below come from the saved order.','订单保留专属物料清单快照。下表的预留数量来自实际保存的订单。'))+
        table([t('Material','物料'),t('Required','需求数量'),t('Reserved','已预留')],rows)))
    r=record['reconcile']
    items.append(('reconcile',t('4 · Reconcile stock and ledger','4 · 核对库存与流水'),paragraph(t('The application reconciles inventory balances, ledger entries and active reservations. The separate discrepancy and shortage tests are available above.','系统核对库存余额、流水与有效预留。上方可分别查看差异与缺料测试。'))+
        table([t('Materials checked','核对物料数'),t('Consistent','账实一致')],[(r['checked'],t('Yes','是') if r['consistent'] else t('No','否'))])))
    if 'production' in record:
        production=record['production']
        outcome=production['outcome']
        items.append(('production',t('5 · Schedule, report and complete','5 · 排程、报工与完工'),paragraph(t('The factory schedules a machine, reports six accepted parts, and closes the order. Stock and ledger still reconcile after completion.','工厂安排设备，报工六件合格品并完成订单。完工后库存与流水仍然一致。'))+
            table([t('Machine','设备'),t('Scheduled (min)','计划时长（分）'),t('Accepted','合格'),t('Rejected','不合格'),t('Final status','最终状态')],
                  [(production['device'],production['plannedMinutes'],production['good'],production['rejected'],outcome['status'])])))
    return paragraph(t('This order comes from one replay of the actual application with fictional factory data.','以下同一笔订单来自实际应用的运行回放，使用虚构工厂数据。'))+group(page,items,t('Transaction step','事务步骤'),'order-replay',stepper=True)+paragraph(page.source('manufacturing-flow.json',t('Download the recorded transaction values','下载事务记录数据')))


def firewatch(page, table, setup):
    t=page.t
    rows=[(r['id'],t('Validation','验证') if r['split']=='validation' else t('Held out','留出测试'),len(r['truth']),f"{r['duration']:.1f}") for r in setup['videos']]
    source=page.url('assets/evidence/furg-house6.mp4')
    licence=page.link('assets/public-data/furg-LICENSE.txt',t('Source licence','视频来源许可'))
    video=f'<video controls playsinline preload="none" width="640" data-fire-video aria-label="{t("Original house6 fire video","house6 火焰原视频")}"><source src="{source}" type="video/mp4"><a href="{source}">house6.mp4</a></video>'
    seek=f'<div class="actions" data-video-jumps hidden><button type="button" data-video-time="0">{t("Start of labelled event","标注起点")} · 0 s</button><button type="button" data-video-time="24">{t("ONNX candidate","ONNX 候选")} · 24 s</button></div>'
    return paragraph(t('The source-disjoint split was set before threshold selection. Validation was used to choose detection settings; the selected settings were then held fixed for event matching on the held-out videos.','先按来源划分视频，再用验证集选择检测设置。固定这些设置后，才在留出的测试视频上进行事件匹配。'))+table([t('Video','视频'),t('Split','划分'),t('Labelled events','标注事件'),t('Duration (s)','时长（秒）')],rows)+        '<section id="event-video"><h3>'+t('Held-out video','留出测试原视频')+'</h3>'+seek+'<figure class="sample-video">'+video+f'<figcaption>{t("FURG house6 · original held-out input · CC0 1.0","FURG house6 · 留出测试的原始输入 · CC0 1.0")} · {licence}</figcaption></figure></section>'+        paragraph(t('The recorded model candidate lasts from 24 to 25 seconds, inside the 0–30 second label. Compare the two intervals in the archived result above.','归档模型候选出现在 24–25 秒，在 0–30 秒的标注区间内。可与上方归档时间轴对照。'))


def signal(page, table, records):
    t=page.t
    rows=[(r['noise_std'],r['window'],f"{r['overlap']:.0%}",r['reliable_bins'],f"{r['gain_mae_db']:.5f}",f"{r['phase_mae_deg']:.5f}") for r in records]
    frequencies=page.select('alias-frequency',[(v,f'{v} Hz') for v in (274,450,512,600,750,1000)])
    caption=t('Adjust the input frequency. The line compares the input sine with its signed alias; both meet the sample markers.','切换输入频率。两条曲线分别表示输入正弦波及带符号的折叠频率，均通过相同采样点。')
    return paragraph(t('The Python workbench generates or loads paired signals, applies the configured filter, and then calculates the spectrum and Welch H1. The 27 experiment rows below compare known filter responses under different noise, window and overlap settings.','Python 工作台先生成或导入成对信号，选择滤波配置，再计算频谱及 Welch H1。下方 27 组实验以已知滤波器响应为参考，比较不同噪声、窗长和重叠率。'))+        f'<h3 id="alias-demo">{t("Sampling and aliasing","采样与混叠演示")}</h3><div data-alias hidden><label>{t("Input frequency","输入频率")} {frequencies}</label><p role="status" id="alias-result"></p><svg class="chart" viewBox="0 0 600 190" role="img" aria-label="{t("Input and sampled sine waves","输入及采样正弦波")}"><path d="M20 95H580" stroke="#9a9a9a"/><path id="alias-input" fill="none" stroke="#375e98" stroke-width="2"/><path id="alias-fold" fill="none" stroke="#ac6932" stroke-width="2" stroke-dasharray="4 4"/><g id="alias-samples" fill="#20242d"/></svg><p>{caption}</p></div>'+        f'<details id="h1-runs"><summary>{t("View all 27 H1 runs","查看全部 27 组 H1 实验")}</summary>'+table([t('Output noise σ','输出噪声 σ'),t('Window','窗长'),t('Overlap','重叠率'),t('Valid bins','有效频点'),'MAE (dB)','MAE (°)'],rows)+'</details>'


def bathymetry(page, table, record):
    t=page.t
    from pathlib import Path
    with (Path(__file__).resolve().parents[1]/"assets/evidence/bathymetry-input.csv").open() as f:
        inputs=list(csv.DictReader(f))
    samples=[]
    for index,source_row in enumerate(record['test_rows']):
        values=(record['test_depth_m'][index],record['predictions']['linear'][index],record['predictions']['svr'][index])
        samples.append((source_row,inputs[source_row]['group_id'],*(f'{value:.3f}' for value in values),f'{values[1]-values[0]:+.3f}',f'{values[2]-values[0]:+.3f}'))
    split=table([t('Partition','划分'),t('Groups','分组'),t('Rows','行数')],[(t('Training','训练'),', '.join(record['train_groups']),len(record['train_rows'])),(t('Held out','留出'),', '.join(record['test_groups']),len(record['test_rows']))])
    rows=table([t('Input row (zero-based)','输入行号（从 0 起）'),t('Group','分组'),t('Reference (m)','参考（m）'),t('Linear (m)','线性（m）'),'SVR (m)',t('Linear residual (m)','线性残差（m）'),t('SVR residual (m)','SVR 残差（m）')],samples)
    return paragraph(t('The synthetic reflectance table supplies B2, B3, B4 and B8. Models are fitted to the training groups, then used to predict the 30 withheld depths. Residuals below are predictions minus synthetic references.','输入是含 B2、B3、B4、B8 的合成反射率表。模型在训练分组上拟合，再给出 30 条留出样本的水深预测。下表残差等于预测减去合成参考值。'))+split+        paragraph(page.source('bathymetry-input.csv',t('Download the 120 input samples','下载 120 条输入样本')))+        '<details id="depth-prediction-table"><summary>'+t('Inspect all 30 held-out predictions','查看全部 30 条留出预测')+'</summary>'+rows+'</details>'


def city(page, locations, table):
    t=page.t
    routes=''.join('<li>'+escape(t(r['en'],r['name']))+' · '+' → '.join(escape(t(p['en'],p['name'])) for key in r['stops'] for p in locations['places'] if p['id']==key)+'</li>' for r in locations['routes'])
    rows=[(escape(t(p['en'],p['name'])),escape(t(p['address_en'],p['address'])),p['source']) for p in locations['places']]
    index='<ul class="site-register">'+''.join(f'<li><strong>{name}</strong> · {addr} <a href="{src}">{t("Address record","地址出处")} ↗</a></li>' for name,addr,src in rows)+'</ul>'
    return ('<details id="route-catalogue"><summary>'+t('Themed walks and stops','主题路线与站点')+'</summary><ul>'+routes+'</ul></details>'
        +paragraph(t('Walking itineraries are calculated on the OpenStreetMap pedestrian network. Compare distance and estimated time per route, or choose the stops for your own walk.','路线沿 OpenStreetMap 步行路网计算。可查看各段距离与全程参考时长，也可自选场址组合行程。'))
        +'<details id="place-search" data-place-search><summary>'+t('Search the address register','检索地址与出处')+'</summary><label hidden>'+t('Name or address','名称或地址')+' <input type="search"></label><p role="status" hidden>'+t('No matching sites.','无匹配地点。')+'</p>'+index+'</details><p>'+page.source('city-places.json',t('Download site records','下载场址记录'))+' · '+page.link('assets/atlas/SOURCES.txt',t('Basemap source and licence','底图来源与许可'))+'</p>')
