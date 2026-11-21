"""Build standalone evidence pages from the same archives as the local workbenches."""
import csv, json, posixpath, shutil
from html import escape
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from review_cases import ACTION_ANCHORS, CASES, ENTRY_ANCHORS, FUNCTIONS, RESULT_TITLES
import walkthroughs
import medical_exhibit

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'assets/evidence'
PROJECTS={p['id']:p for p in json.loads((ROOT/'assets/projects.json').read_text(encoding='utf-8'))}
def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def rows(cells):
    return ''.join('<tr>'+''.join(f'<td>{escape(str(v))}</td>' for v in row)+'</tr>' for row in cells)
def table(headers,values):
    return '<div class="table-scroll"><table><thead><tr>'+''.join(f'<th scope="col">{h}</th>' for h in headers)+'</tr></thead><tbody>'+rows(values)+'</tbody></table></div>'
class Page:
    def __init__(self,dest,case,lang):
        self.dest,self.case,self.lang=dest,case,lang
        self.path=self.location(case,lang)
    def location(self,case,lang):
        if case:
            return f'projects/review/{case}-{lang}.html'
        return f'index.html?lang={lang}#top'
    def t(self,en,zh):return zh if self.lang=='zh' else en
    def url(self,target):return posixpath.relpath(target, PurePosixPath(self.path).parent)
    def link(self,target,label,css=''):
        return f'<a class="{css}" href="{self.url(target)}">{label}</a>'
    def img(self,target,label):
        dimensions={
            'fire-image-candidates.jpg': (1440, 900),
            'signal-h1.jpg': (1374, 343),
            'patient-runtime.jpg': (860, 532),
            'doctor-runtime.jpg': (826, 411),
        }
        width,height=dimensions.get(Path(target).name,(1280,720) if Path(target).name.startswith('vr-flow-') else (480,480))
        src=self.url(target)
        return f'<figure><a href="{src}"><img src="{src}" alt="{escape(label)}" width="{width}" height="{height}" loading="lazy"></a><figcaption>{label}</figcaption></figure>'
    def source(self,name,label):return self.link('assets/evidence/'+name,label)
    def select(self,id,options):
        return f'<select id="{id}">'+''.join(f'<option value="{value}">{name}</option>' for value,name in options)+'</select>'
    def group(self,items):
        buttons=''.join(f'<button type="button" data-choice="{i}" aria-pressed="{str(i==0).lower()}">{b}</button>' for i,(b,_,_) in enumerate(items))
        panels=''.join(f'<div class="panel" data-panel="{i}"><h3>{title}</h3>{body}</div>' for i,(_,title,body) in enumerate(items))
        return f'<div data-switch><div class="tabs" hidden>{buttons}</div>{panels}</div>'
    def hsi(self):
        t=self.t
        with (ROOT/'hsi-sr-lab/evidence/4.1_Pavia_comparison.csv').open() as f:data=list(csv.reader(f))[1:]
        chosen=[(r[1],r[2],r[6]) for r in data if r[0]=='4×' and r[1] in ['ERCSR','MCArb-ERCSR']]
        assert chosen==[('ERCSR','29.1482','5.8337'),('MCArb-ERCSR','29.2129','5.8700')]
        s=table([t('Method','方法'),'PSNR ↑ (dB)','SAM ↓ (°)'],chosen+[(t('Candidate − baseline','候选 − 基线'),'+0.0647','+0.0363')])
        s+='<p>'+t('Both numbers rose. Higher PSNR indicates less spatial reconstruction error; the larger spectral angle indicates worse spectral agreement. The thesis averages each metric per image.','两列数值均上升。PSNR 越高，空间重建误差越低；光谱角越大，光谱一致性越差。论文先逐图计算各项指标，再按图像数平均。')+'</p>'
        base='hsi-sr-lab/thesis-final/images/pavia/'
        for suffix,label in [('',t('Archived reconstruction','归档重建图')),('_error',t('Archived error map','归档误差图'))]:
            imgs='<div class="thumbs">'+''.join(self.img(base+model+'_x4'+suffix+'.png',model.replace('_','-')+' · '+label) for model in ('ERCSR','MCArb_ERCSR'))+'</div>'
            s+=('<div data-crop><button hidden type="button" aria-pressed="false">'+t('Magnify the same area in both images','同步放大两幅图的中心区域')+'</button>'+imgs+'</div>') if not suffix else '<details><summary>'+label+'</summary>'+imgs+'</details>'
        layer_a=self.url(base+'ERCSR_x4.png')
        layer_b=self.url(base+'MCArb_ERCSR_x4.png')
        s+=f'<details class="comparison"><summary>{t("Slide across the same reconstruction", "滑动对照同一位置")}</summary><div class="wipe"><img src="{layer_b}" alt="MCArb-ERCSR"><img src="{layer_a}" alt="ERCSR" class="baseline"></div><label>{t("ERCSR coverage","ERCSR 显示比例")} <input type="range" min="0" max="100" value="50"> <output>50%</output></label></details>'
        s+='<h3>'+t('Across backbones','其他主干对照')+'</h3><p>'+t('MCArb-SSPSR improved all six metrics relative to SSPSR-b on both datasets at ×4 and ×8. PSNR gains ranged from 0.21 to 0.36 dB. The thesis averages its metrics per image. The separate workbench can also give scenes equal weight.','与 SSPSR-b 比较，MCArb-SSPSR 在两个数据集的 ×4、×8 上六项指标均改善，PSNR 增益为 0.21–0.36 dB。工作台的场景等权评价先在各场景内对图像平均，再对场景等权汇总。')+'</p>'
        return s+self.source('pavia-table-4-1.csv',t('Pavia Centre · full Table 4.1 (CSV)','Pavia Centre · 完整表 4.1（CSV）'))+' · '+self.source('chikusei-table-4-2.csv',t('Chikusei · Table 4.2','Chikusei · 表 4.2'))+' · '+self.link('hsi-sr-lab/thesis-final/source/LICENSE',t('Source licence','代码许可'))+'<p>'+t('Method: MCArb, Zhang et al., IEEE TGRS (2025). Images and tabulated runs are from my thesis archive.','复现方法为 Zhang 等发表于 IEEE TGRS（2025）的 MCArb。图像和表格来自我的论文实验归档。')+'</p>'
    def vrfitai(self):
        t=self.t
        images='<div class="thumbs training-captures">'+self.img('assets/evidence/vr-flow-active.jpg',t('Desktop browser before refresh · training in progress','刷新前的桌面浏览器实拍 · 训练进行中'))+self.img('assets/evidence/vr-flow-paused.jpg',t('Same desktop session after refresh · paused, with Continue available','同一桌面训练刷新后 · 暂停，等待继续'))+'</div>'
        s=self.group([(t('Refresh','刷新'),t('Restore a paused checkpoint','恢复成暂停状态'),images+'<p>'+t('These two captures show the same 30-second desktop practice before and after refresh. After refresh, the session is paused until the user selects Continue.','两张图记录同一场 30 秒桌面试练。刷新后停在暂停状态，等待点击「继续训练」。')+'</p><p>'+t('A separate timing test recorded one hit before refresh. After simulating 100 seconds away, the restored timer still reads 7.5 seconds. Resuming and training for another 2.5 seconds produces 10 active seconds.','独立计时测试中，刷新前命中一次。模拟离开 100 秒后，恢复时仍为 7.5 秒。继续训练 2.5 秒后，有效时长为 10 秒。')+'</p>'),
        (t('Lost acknowledgement','回执丢失'),t('Retry the original payload','用原内容重试'),'<p>'+t('The recovery fixture stores 8 active seconds and 3 hits. Reopening storage preserves the same UUID and all payload fields until the pending save is cleared.','测试记录包含 8 秒有效时长和 3 次命中。刷新后待提交记录保留原 UUID 和全部字段，直到待保存状态清除。')+'</p>'),
        (t('Server history','服务端记录'),t('Two submissions, one stored session','两次提交，一条记录'),'<strong>201 → 200</strong><p>'+t('A separate API test submits the same 30-second, five-hit session twice. The first response creates the record; the retry returns it. History contains one row.','独立接口测试将同一条 30 秒、5 次命中的记录提交两次。首次创建成功，重试返回原记录，历史列表只有一行。')+'</p>')])
        scene=self.url('assets/studio/studio-preview.html')+'?lang='+self.lang
        scene_label=t('Explore the training studio','浏览三维训练室')
        preview=f'<section id="studio-preview"><h3>{scene_label}</h3><iframe class="studio-preview" loading="lazy" src="{scene}" title="{scene_label}"></iframe></section>'
        s+='<p>'+self.source('vr-recovery-tests.txt',t('Recovery and save test cases','训练恢复与保存测试用例'))+'</p>'
        return preview+s+'<h3 id="training-suggestions">'+t('Training suggestions','训练建议')+'</h3><p>'+t('After at least three comparable sessions, the rule system may suggest one difficulty step or a duration change of up to 20%. The user confirms the adjustment. DeepSeek provides explanations. These desktop tests cover record integrity; headset tracking and training effectiveness require separate evaluation.','至少三次可比训练后，规则可以建议调整一级难度，或将时长调整最多 20%，由用户确认。DeepSeek 提供解释。以上桌面测试核对记录一致性；头显追踪与训练效果需要单独评价。')+'</p>'
    def manufacturing(self):
        t=self.t; labels=[t('Material','物料'),t('Balance','在库'),t('Ledger','流水'),t('Active reservation','有效预留')]
        discrepancy=table(labels,[('RECON',11,10,2)])+'<p>'+t('The test increases only the stock balance. Reconciliation reports the mismatch and leaves the balance at 11 for investigation.','测试只将库存余额加一。对账指出余额与流水不一致，保留在库数 11 供后续排查。')+'</p>'
        steps=self.group([
            (t('Discrepancy','差异'),t('One material checked · discrepancy +1','已核对一种物料 · 差异 +1'),discrepancy),
            (t('Baseline','基准'),t('One material checked · consistent','已核对一种物料 · 一致'),table(labels,[('RECON',10,10,2)])),
            (t('Empty factory','空工厂'),t('Zero materials checked','核对物料数为零'),'<p>'+t('The live workbench shows an explicit empty result when the factory has no stock or ledger entries to reconcile.','工厂尚无可核对的物料或流水时，工作台明确显示空结果。')+'</p>'),
        ])
        return steps+'<p>'+self.source('inventory-test.txt',t('Reconciliation test','对账测试'))+' · '+self.source('inventory-rollback-test.txt',t('Rollback test','回滚测试'))+'</p><p>'+t('Project-level MySQL deployment tests verified concurrent oversell prevention, shortage rollback and ledger consistency. The local demonstration uses preloaded fictional factory records.','MySQL 部署测试验证了并发超卖防护、缺料回滚及库存流水一致性。本地演示基于预置的虚构工厂数据，可查看库存余额、收发流水与有效预留。')+'</p><details id="shortage-rollback"><summary>'+t('Inspect a shortage rollback','查看缺料回滚')+'</summary><p>'+t('An order needs two units each of M1 and M2. Ten units of M1 are available, with only one of M2. The request returns HTTP 409. M1 ends with zero reserved units, no reservation or ledger rows are added, and the order version stays at 1.','订单对 M1、M2 各需两件。M1 有十件，M2 只有一件，预留请求返回 HTTP 409。回滚后 M1 预留仍为零，无新增预留或流水，订单版本仍为 1。')+'</p>'+'</details>'
    def firewatch(self):
        t=self.t;report=read('firewatch/app/static/research-report.json')
        vals=[]
        for k,method in report['methods'].items():
            m=method['test_iou_sensitivity']['0.5'];vals.append([t('Rules','规则') if k=='rule' else 'ONNX',m['tp'],m['fp'],m['fn']])
        video=next(x for x in report['methods']['model']['test_iou_sensitivity']['0.5']['videos'] if (x.get('id') or x.get('video'))=='house6')
        candidate=video['events'][0]
        start,end=candidate['start'],candidate['end']
        s='<div class="timeline"><div>'+t('Annotated event','标注事件')+' · 0–30 s<i></i></div><div>ONNX · '+f'{start:g}–{end:g} s<i class="candidate" style="--offset:{start/30:.4%};--duration:{(end-start)/30:.4%}"></i></div></div>'
        s+='<p>'+t('The one-second candidate falls inside the 30-second house6 event. Temporal IoU is 1/30, about 0.033, below the 0.5 matching threshold. The held-out pair contains only one annotated event.','house6 的候选只覆盖标注时段中的一秒，时间 IoU 为 1/30（约 0.033），低于 0.5 匹配阈值。两段留出视频共有一个标注事件。')+'</p>'
        s+=table([t('Method','方法'),t('Matched events','检出事件'),t('False alarms','误报事件'),t('Missed events','漏检事件')],vals)
        image=self.img('assets/evidence/fire-image-candidates.jpg',t('Image workbench candidate regions · FURG Car1 validation frame at 7 s · CC0 source image','图像工作台候选区域 · FURG Car1 验证视频第 7 秒 · 原画面 CC0'))
        variants=[]
        for threshold in report['methods']['model']['test_iou_sensitivity']:
            metrics=report['methods']['model']['test_iou_sensitivity'][threshold]
            variants.append((threshold, 'IoU ≥ '+threshold, table(['TP','FP','FN'],[(metrics['tp'],metrics['fp'],metrics['fn'])])))
        s+='<details><summary>'+t('Inspect other matching thresholds','对照不同匹配阈值')+'</summary>'+self.group(variants)+'<p>'+t('These thresholds match the same archived predictions against the held-out labels.','各阈值使用同一批归档预测，与留出集标注匹配。')+'</p></details>'
        return s+'<p>'+self.source('flame-evaluation-setup.json',t('Video split and annotated intervals','视频划分与标注区间'))+' · '+self.source('flame-results.json',t('Archived event evaluation','归档事件评测'))+'</p><details id="image-candidates"><summary>'+t('View image candidates','查看图像候选区域')+'</summary>'+image+'<p>'+t('The local workbench measures box IoU on 32 annotated FURG frames. The video timeline above matches event intervals.','另用 FURG 的 32 帧标注图像评测检测框，采用空间 IoU。上方视频按时间区间匹配。')+'</p>'+self.link('assets/public-data/furg-source.json','FURG / CC0')+'</details>'
    def signal(self):
        t=self.t;data=read('assets/evidence/signal-sweep.json')['rows']
        subset=[r for r in data if r['window']==1024 and r['overlap']==.5]
        panels=[]
        for r in subset:
            panels.append((t('Noise σ','噪声 σ')+' '+str(r['noise_std']),t('Valid frequency bins','有效频点')+f" · {r['reliable_bins']}",table([t('Gain MAE','增益 MAE'),t('Phase MAE','相位 MAE')],[(f"{r['gain_mae_db']:.4f} dB",f"{r['phase_mae_deg']:.4f}°")])))
        vi=self.link('signal-lab/original/Virtual_Oscilloscope.vi',t('Download the original LabVIEW VI','下载原 LabVIEW VI'))
        scope='<p>'+t('The original dual-channel virtual oscilloscope displays and measures a pair of signals. The Python workbench estimates the filter response from paired inputs and outputs. This example uses numerically simulated signals.','原 LabVIEW 双通道虚拟仪器用于观察与测量两路信号。Python 工作台使用成对的输入与输出估计滤波器频响。此例采用数值仿真信号。')+' '+vi+'</p>'
        band=self.img('assets/evidence/signal-h1.jpg',t('Python H1 workbench · theoretical response overlaid with the estimate; grey ranges mark screened-out bins.','Python H1 工作台 · 理论与估计叠加，灰色标示屏蔽频点。'))
        checks='<p>'+t('Bins are screened for weak input excitation or coherence below 0.8. Fewer than four Welch segments or a failed stationarity check masks the full estimate.','输入激励不足或相干性低于 0.8 的频点被屏蔽。Welch 分段少于四段或平稳性筛查未通过时，整段估计被屏蔽。')+'</p>'
        return scope+band+checks+'<details><summary>'+t('Compare the noise settings','比较噪声设置')+'</summary><p>'+t('Compare output noise levels with window length and overlap held at 1,024 samples and 50%. Errors are computed only over valid bins between 10 and 180 Hz.','固定 1,024 点窗和 50% 重叠，比较不同输出噪声。误差仅在 10–180 Hz 的有效频点计算。')+'</p>'+self.group(panels)+self.source('signal-sweep.json',t('All 27 simulation settings and results','查看 27 组仿真条件与结果'))+'</details><h3>'+t('Sampling example','采样示例')+'</h3><p>'+t('A 750 Hz sine sampled at 1,024 Hz exceeds the 512 Hz Nyquist limit. Its observed peak folds to 274 Hz. The local workbench runs this preset and marks the folded frequency. The H1 results above come from simulation.','750 Hz 正弦信号以 1,024 Hz 采样时超过 512 Hz 奈奎斯特频率，折叠峰出现在 274 Hz。本地工作台可直接运行该预设。上述 H1 结果来自仿真。')+'</p>'
    def city(self):
        t=self.t
        atlas=self.url('assets/atlas/index.html')+'?lang='+self.lang
        label=t('Shanghai historic sites street map','上海红色文化街区地图')
        return (f'<p><a href="{atlas}">{t("Open full map", "打开完整地图")} ↗</a></p>'
                f'<iframe class="embedded-atlas" src="{atlas}" title="{label}"></iframe>')
    def bathymetry(self):
        t=self.t;r=read('assets/evidence/bathymetry-example.json');truth=r['test_depth_m'];pred=r['predictions'];vals=truth+pred['linear']+pred['svr'];lo=int(min(vals));hi=int(max(vals))+1
        def px(v):return 65+(v-lo)/(hi-lo)*285
        def py(v):return 235-(v-lo)/(hi-lo)*185
        dots=''.join(f'<circle data-sample="{i}" cx="{px(x):.2f}" cy="{py(y):.2f}" r="{3 if k=="linear" else 4}" stroke="{color}" fill="{color if k=="linear" else "none"}"/>' for k,color in [('linear','#17658e'),('svr','#b5632f')] for i,(x,y) in enumerate(zip(truth,pred[k])))
        svg=f'<svg class="chart" viewBox="0 0 420 290" role="img" aria-label="{t("Synthetic reference and predicted depths","合成参考水深与预测值")}"><text x="10" y="22">{t("Predicted depth (m)","预测水深（米）")}</text><path d="M65 50V235H350" fill="none" stroke="#68727a"/><path d="M65 235L350 50" stroke="#7d8792" stroke-dasharray="3 4"/>{dots}<text x="44" y="239">{lo}</text><text x="44" y="54">{hi}</text><text x="65" y="253">{lo}</text><text x="344" y="253">{hi}</text><text x="80" y="279">{t("Synthetic reference depth (m)","合成参考水深（米）")}</text></svg>'
        select=self.select('sample-index',[(i,str(row)) for i,row in enumerate(r['test_rows'])])
        sampledata=escape(json.dumps([[x,pred['linear'][i],pred['svr'][i]] for i,x in enumerate(truth)]), quote=True)
        probe=f'<div data-depth-samples="{sampledata}" hidden><label>{t("Inspect input row (zero-based)", "查看输入行（从 0 起）")} {select}</label> <output aria-live="polite"></output></div>'
        return '<h3>'+t('Synthetic depth predictions','合成样例预测')+'</h3><div class="pair"><figure>'+svg+'<figcaption>'+t('Solid circles: linear regression. Rings: SVR.','实心圆为线性回归，空心圆为 SVR。')+'</figcaption>'+probe+'</figure><div><h3>'+t('120 generated samples · 8 groups','120 条合成样本 · 8 组')+'</h3><p>'+t('Six groups fit the models and preprocessing. Two complete groups (30 rows) were held out.','六组用于拟合模型和预处理。另两组整组留出，共 30 行。')+'</p><p>'+t('Holding out complete groups limits leakage from related samples.','以完整分组留出，减少同组关联样本进入训练与测试带来的数据泄漏。')+'</p></div></div><details><summary>'+t('Open errors and sample-level results','查看误差与逐样本结果')+'</summary>'+table([t('Model','模型'),'RMSE (m)','MAE (m)'],[(k.upper(),f"{v['rmse_m']:.3f}",f"{v['mae_m']:.3f}") for k,v in r['metrics'].items()])+self.source('bathymetry-example.json',t('Synthetic run · rows and predictions','合成实验 · 行号与预测'))+'</details><section id="observations"><h3>'+t('Public photon observations','公开光子观测')+'</h3><p>'+t('The archived Li dataset includes 33,688 non-empty photon observations. Its MSL height column and the absence of matched B2/B3/B4/B8 bands prevent using this file directly as a measured regression benchmark.','Li 公开数据归档含 33,688 条非空光子观测。数据列是相对平均海平面的高度，且缺少配对的 B2/B3/B4/B8 波段，因此尚不能作为实测回归基准。')+'</p>'+self.link('assets/public-data/reef-metadata.json',t('Archived file and field notes','归档文件与字段说明'))+' · <a href="https://zenodo.org/records/19937366">Zenodo v1</a> · <a href="https://zenodo.org/records/19942496">Zenodo v2</a>'+'</section>'
    def medical(self):
        return medical_exhibit.demo(self)

    def workflow(self):
        case=self.case
        if case=='hsi':
            return walkthroughs.hsi(self,ROOT,table)
        if case=='vrfitai':
            return walkthroughs.vrfitai(self)
        if case=='manufacturing':
            return walkthroughs.manufacturing(self,table,read('assets/evidence/manufacturing-flow.json'))
        if case=='firewatch':
            return walkthroughs.firewatch(self,table,read('assets/evidence/flame-evaluation-setup.json'))
        if case=='signal':
            return walkthroughs.signal(self,table,read('assets/evidence/signal-sweep.json')['rows'])
        if case=='bathymetry':
            return walkthroughs.bathymetry(self,table,read('assets/evidence/bathymetry-example.json'))
        if case=='city':
            return walkthroughs.city(self,read('assets/evidence/city-places.json'),table)
        return medical_exhibit.architecture(self,table)

    def function_index(self):
        t=self.t
        links=''.join(
            f'<li><a href="#{target}"><strong>{t(*name)}</strong><span>{t(*description)}</span></a></li>'
            for target,name,description in FUNCTIONS[self.case]
        )
        return (f'<nav class="function-index" id="overview" aria-labelledby="overview-title">'
                f'<h2 id="overview-title">{t("Project functions", "项目功能")}</h2><ul>{links}</ul></nav>')

    def local_tasks(self):
        t=self.t
        tasks={
            'hsi': [('/', 'Run aerial-image interpolation', '用航测裁片做插值实验')],
            'vrfitai': [('/', 'Open the app for 30-second practice', '进入应用试练 30 秒')],
            'manufacturing': [('/login', 'Open demo sign-in', '登录演示工厂')],
            'firewatch': [('/model', 'Single-image model comparison', '单图模型对照'),
                          ('/evaluation', '32-frame box evaluation', '32 帧检测框评测'),
                          ('/static/research.html', 'Video event evaluation', '视频事件时间评测')],
            'signal': [('/?preset=alias', 'Observe sampling aliasing', '观察采样混叠'),
                       ('/?preset=ecg', 'Load recorded ECG', '载入真实波形')],
            'bathymetry': [('/', 'Compare models', '比较模型'),
                           ('/?view=forecast', 'Predict new samples', '预测新样本'),
                           ('/?view=observations', 'Inspect photon tracks', '查看光子轨迹')],
            'medical': [('/', 'Run full system', '运行完整系统'),
                        ('/doctor.html', 'Open doctor workspace', '打开医生端')],
        }
        links=[]
        for path,en,zh in tasks.get(self.case, []):
            fallback=self.url(f'projects/offline.html?project={self.case}&path={quote(path, safe="")}')
            links.append(f'<a hidden data-local-only data-app="{self.case}" data-app-path="{path}" href="{fallback}">{t(en,zh)} ↗</a>')
        return ''.join(links)

    def write(self):
        t=self.t
        k=self.case
        anchor=ACTION_ANCHORS[k]
        other='zh' if self.lang=='en' else 'en'
        return_target=f'index.html?lang={self.lang}#project-{k}'
        nav=self.link(return_target,t('All projects','全部项目'),'catalog-return')
        alternate=self.link(self.location(k,other),t('中文','English'))
        materials=self.link('projects/'+k+'.html',t('Full project materials (Chinese)','完整项目资料'),'btn')
        if k=='medical':
            materials=''
        title,role,summary,action,kind=[t(*v) for v in CASES[k]]
        date=PROJECTS[k]["date"]
        byline=escape(role+(f' · {date}' if date else ''))
        award=(f'<p class="project-honour">{t("Outstanding Project · Summer Practicum", PROJECTS[k]["award"])}</p>'
               if PROJECTS[k].get('award') else '')
        workflow=t('Process and results','过程与结果')
        sections=(('overview',t('Functions','项目功能')),(anchor,t('Demo and evidence','演示与证据')),('workflow',workflow))
        chapter_links=''.join(f'<a href="#{section}">{label}</a>' for section,label in sections)
        chapters=f'<nav class="reading-nav" aria-label="{t("On this project page","本项目章节")}" data-reading-nav>{chapter_links}</nav>'
        content=(f'<section class="hero"><p class="role">{byline}</p><h1>{title}</h1>{award}<p>{summary}</p>'
                 f'<div class="actions hero-actions"><a class="btn primary project-entry" href="#{ENTRY_ANCHORS[k]}">{action} →</a><a class="btn" href="#overview">{t("Project functions","项目功能")}</a>{materials}{self.local_tasks()}</div></section>{chapters}{self.function_index()}'
                 f'<article class="evidence" id="{anchor}"><div id="evidence"></div><p class="source">{kind}</p>'
                 f'<h2>{t(*RESULT_TITLES[k])}</h2>{getattr(self,k)()}</article>'
                 f'<article class="evidence workflow" id="workflow"><div id="implementation" aria-hidden="true"></div><h2>{workflow}</h2>{self.workflow()}</article>')
        sequence=list(CASES)
        i=sequence.index(k)
        previous,next_case=sequence[(i-1)%len(sequence)],sequence[(i+1)%len(sequence)]
        prev_link=self.link(self.location(previous,self.lang),'← '+t(*CASES[previous][0]))
        next_link=self.link(self.location(next_case,self.lang),t(*CASES[next_case][0])+' →')
        out=self.dest/self.path
        out.parent.mkdir(parents=True,exist_ok=True)
        medical_script=(f'<script defer src="{self.url("assets/medical-demo.js")}"></script>'
                        if k=='medical' else '')
        out.write_bytes(f'''<!doctype html>
<html lang="{'en' if self.lang=='en' else 'zh-CN'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title} · Jiawei Wang</title>
  <link rel="icon" href="data:,">
  <link rel="stylesheet" href="{self.url('assets/review.css')}">
  <script defer src="{self.url('assets/review.js')}"></script>
  {medical_script}
</head>
<body class="{k}">
  <header class="mast"><strong>{nav}</strong><nav>{alternate}</nav></header>
  <main>{content}</main>
  <footer class="foot"><nav aria-label="{t('Project navigation','项目导航')}">{prev_link} {nav} {next_link}</nav></footer>
</body>
</html>
'''.encode('utf-8'))

def prepare_evidence():
    import atlas_data
    atlas_data.render()
    for src,target in [('4.1_Pavia_comparison.csv','pavia-table-4-1.csv'),('4.2_Chikusei_comparison.csv','chikusei-table-4-2.csv')]:
        shutil.copyfile(ROOT/'hsi-sr-lab/evidence'/src,DATA/target)
    shutil.copyfile(ROOT/'firewatch/app/static/research-report.json',DATA/'flame-results.json')
    def excerpt(name,start,end):
        content=(ROOT/name).read_text(encoding='utf-8').split(start,1)[1].split(end,1)[0]
        return name+'\n\n'+start+content.rstrip()+'\n'
    workflow='manufacturing-platform/backend/src/test/java/com/hystu/springboot_/WorkflowTests.java'
    (DATA/'inventory-test.txt').write_text(excerpt(workflow,'@Test void reconciliationChecksAllLedgerRowsAndActiveReservations','@Test void reconciliationEnforces'))
    (DATA/'inventory-rollback-test.txt').write_text(excerpt(workflow,'@Test void shortageRollsBackEarlierLinesAndAudit','@Test void reservationSnapshotSurvivesBomEditAndRelease'))
    rec='vrfitai/tests/recovery.test.js';api='vrfitai/tests/api.test.js'
    (DATA/'vr-recovery-tests.txt').write_text('\n'.join([excerpt(rec,'test("refresh restores elapsed','test("draft storage'),excerpt(rec,'test("unacknowledged save','test("malformed'),excerpt(api,'test("session save, retry','test("invalid session')]))

def write_medical_demo(dest, lang):
    page = Page(dest, 'medical', lang)
    t = page.t
    filename = t('demo-en.html', 'demo.html')
    title = t('Health screening appointments and reports', '体检预约与报告')
    out = dest / 'case-studies' / 'medical' / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(f'''<!doctype html>
<html lang="{t('en','zh-CN')}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <link rel="icon" href="data:,">
  <link rel="stylesheet" href="../../assets/review.css">
  <script defer src="../../assets/medical-demo.js"></script>
</head>
<body class="medical" data-project="medical">
<main>
  <section class="hero">
    <h1>{title}</h1>
    <nav aria-label="{t('Demo sections','演示功能')}">
      <a href="#sample-appointment">{t('Book an appointment','体检预约')}</a>
      <a href="#appointments">{t('My appointments','我的预约')}</a>
      <a href="#doctor-demo">{t('Doctor view','医生端')}</a>
      <a href="#report">{t('Report centre','报告中心')}</a>
    </nav>
  </section>
  <article class="evidence" id="sample-appointment">
    <h2>{t('Book an appointment','体检预约')}</h2>
    {medical_exhibit.demo(page)}
  </article>
</main>
</body>
</html>'''.encode('utf-8'))


def render(dest=ROOT):
    prepare_evidence()
    for lang in ('en','zh'):
        write_medical_demo(dest, lang)
        for case in CASES:
            Page(dest,case,lang).write()


if __name__=='__main__':
    render()
