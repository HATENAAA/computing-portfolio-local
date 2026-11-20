"""Bilingual project summaries and links to the available displays."""

CASES = {
    'hsi': [
        ('Remote Sensing Image Super-Resolution Reconstruction Based on Deep Learning', '基于深度学习的遥感影像超分辨率重建'),
        ('Undergraduate thesis', '本科毕业论文'),
        ('I reproduced MCArb on MCNet, SSPSR and ERCSR, and developed a Python workflow for per-image evaluation on Pavia Centre and Chikusei after MATLAB preprocessing.',
         '在 MCNet、SSPSR 和 ERCSR 上复现 MCArb。经 MATLAB 预处理后，用 Python 对 Pavia Centre 和 Chikusei 逐图评测并汇总指标。'),
        ('Compare ERCSR reconstructions', '查看 ERCSR 重建对照'),
        ('Thesis archive · Table 4.1', '论文归档 · 表 4.1'),
    ],
    'vrfitai': [
        ('VRFitAI — VR Fitness Coaching and Training Management Platform', 'VRFitAI — VR健身指导与训练管理平台'),
        ('XR interaction lead · Primary web developer', 'XR交互负责人 · 网站主要开发者'),
        ('VRFitAI provides desktop and WebXR exercises, training records and rule-based adjustments. A session can resume after a refresh; repeating a save with the same session ID returns the existing record.',
         'VRFitAI 提供桌面和 WebXR 训练、训练记录及规则建议。页面刷新后可恢复训练，同一记录 ID 重试时返回已有记录。'),
        ('Open the training recovery demo', '打开训练恢复演示'),
        ('Desktop run and automated tests', '桌面运行记录与自动化测试'),
    ],
    'manufacturing': [
        ('Manufacturing Order and Inventory Management System', '制造订单与库存管理系统'),
        ('Full-stack development', '全栈系统开发'),
        ('The system handles order acceptance, material reservations, production reporting and reconciliation. Reconciliation checks stock balances against the ledger and active reservations.',
         '系统覆盖接单、物料预留、生产报工和库存对账。对账环节将库存余额与流水及有效预留逐项核对。'),
        ('Open the inventory reconciliation example', '打开库存对账示例'),
        ('Local demonstration · Sample integration tests', '本地演示 · 样例集成测试'),
    ],
    'firewatch': [
        ('Visual Flame Detection and Event Analysis System', '视觉火焰检测与事件分析系统'),
        ('Computer vision algorithm development', '计算机视觉算法开发'),
        ('The detector uses colour, edges, morphological closing and frame voting. Event evaluation compares alerts with annotations using one-to-one temporal IoU matching.',
         '结合颜色、边缘、形态学闭运算与滑动窗口投票检测火焰，并以一对一时间 IoU 将事件与标注匹配。'),
        ('View the video event timeline', '查看视频事件时间轴'),
        ('Four annotated videos · Source-separated split', '四段标注视频 · 按来源划分'),
    ],
    'signal': [
        ('Virtual Instrumentation and Signal Analysis System', '虚拟仪器与信号分析系统'),
        ('Digital signal processing system development', '数字信号处理系统开发'),
        ('The project includes a dual-channel virtual oscilloscope and Welch H1 estimates checked against a known filter. Excitation, coherence and stationarity determine which frequency bins are retained.',
         '项目包含双通道虚拟示波器，并以已知滤波器校验 Welch H1 频响。激励、相干性和平稳性决定哪些频点纳入比较。'),
        ('Open the aliasing example', '打开采样混叠演示'),
        ('27 simulations · Known Butterworth response', '27 组仿真 · 已知 Butterworth 响应'),
    ],
    'city': [
        ('Shanghai red heritage atlas', '上海红色文化地图'),
        ('Interactive mapping', '交互式地图开发'),
        ('Explore historic sites, follow themed walks or plan your own route using the offline pedestrian network.',
         '在上海街道底图上查看历史场址，选择主题路线，或使用离线步行路网规划两点与多站行程。'),
        ('Plan a walk', '打开步行地图'),
        ('Municipal address records · OpenStreetMap', '官方地址名录 · OpenStreetMap 底图'),
    ],
    'bathymetry': [
        ('Satellite bathymetry', '卫星测深回归'),
        ('Remote-sensing modelling and evaluation', '遥感样本建模与评价'),
        ('Linear regression and SVR are compared on complete held-out groups using synthetic depths. Public photon observations are documented separately.',
         '在线性回归与 SVR 的对照中，按完整分组留出测试样本。评价采用合成水深，公开光子观测单独列示。'),
        ('View held-out depth predictions', '查看留出组水深预测'),
        ('Synthetic evaluation', '合成样例评价'),
    ],
    'medical': [
        ('Xixin Health Screening Appointments and Reports', '熙心健康体检预约与报告系统'),
        ('Team project · Frontend implementation, asset research and content integration', '团队项目 · 前端制作、素材查找、内容整合'),
        ('The team system covers registration, clinic and package selection, appointment slots, order management, doctor-side appointment search and report publication, and patient report lookup.',
         '团队系统涵盖注册登录、医院与套餐选择、号源预约、订单管理、医生端预约查询与报告发布，以及用户端报告查询。'),
        ('Open the appointment demo', '打开体检预约演示'),
        ('Browser walkthrough · Fictional records', '网页演示 · 虚构记录'),
    ],
}

ACTION_ANCHORS = {
    'hsi': 'ercsr-comparison',
    'vrfitai': 'training-recovery',
    'manufacturing': 'inventory-discrepancy',
    'firewatch': 'video-events',
    'signal': 'valid-frequency-band',
    'city': 'offline-route',
    'bathymetry': 'held-out-predictions',
    'medical': 'sample-appointment',
}

ENTRY_ANCHORS = {**ACTION_ANCHORS, 'signal': 'alias-demo'}

RESULT_TITLES = {
    'hsi': ('Pavia Centre ×4 reconstruction results', 'Pavia Centre ×4 重建结果'),
    'vrfitai': ('Training studio and session recovery', '三维训练室与训练恢复'),
    'manufacturing': ('Inventory discrepancy and rollback', '库存差异与缺料回滚'),
    'firewatch': ('Flame event timelines', '火焰事件时间轴'),
    'signal': ('Welch H1 and valid frequency bands', 'Welch H1 与有效频段'),
    'city': ('Walking map and routes', '步行地图与路线'),
    'bathymetry': ('Held-out depth predictions', '留出组水深预测'),
    'medical': ('Screening appointment demo', '体检预约演示'),
}

# Each entry links to a demonstrated function or to labelled evidence about it.
FUNCTIONS = {
    'hsi': [
        ('ercsr-comparison', ('Reconstruction comparison', '重建图对照'), ('Same-area images, error maps and PSNR / SAM.', '同区域重建图、误差图及 PSNR / SAM。')),
        ('reconstruction-table', ('Model and dataset results', '模型与数据集指标'), ('Two datasets, two scales and six metrics.', '两个数据集、两种倍率、六项指标。')),
        ('ablation-results', ('Ablation and settings', '消融实验与参数'), ('Module comparisons, auxiliary scale and crop ratio.', '模块对照、辅助倍率和裁剪比例。')),
    ],
    'vrfitai': [
        ('studio-preview', ('Training studio', '三维训练室'), ('Rotate the room or inspect the strike pads.', '转动视角，近看击打靶与训练区。')),
        ('training-recovery', ('Session recovery and save retries', '训练恢复与保存重试'), ('Paused checkpoints, lost acknowledgements and one stored record.', '暂停恢复、回执丢失及重复提交结果。')),
        ('training-replay', ('Desktop session replay', '桌面训练回放'), ('Select a course, start, refresh and save.', '选课、开始、刷新及保存的运行截图。')),
        ('training-suggestions', ('Training adjustments', '训练建议'), ('Rule-based options, user confirmation and explanation.', '规则建议、用户确认及模型解释。')),
    ],
    'manufacturing': [
        ('inventory-discrepancy', ('Inventory reconciliation', '库存对账'), ('Stock, ledger and active reservations.', '在库、流水及有效预留。')),
        ('shortage-rollback', ('Shortage handling', '缺料处理'), ('Order behaviour when a material is short.', '部分物料不足时的事务结果。')),
        ('order-replay', ('Order and production stages', '订单与生产流程'), ('Acceptance, reservation, production and completion.', '接单、预留、报工与完工。')),
    ],
    'firewatch': [
        ('video-events', ('Video event matching', '视频事件匹配'), ('Ground truth, detections, false alarms and missed events.', '标注区间、检出、误报和漏检。')),
        ('event-video', ('Held-out video', '留出测试原视频'), ('Playback and direct seeks to the annotated and candidate times.', '播放视频并跳到标注起点和候选时刻。')),
        ('image-candidates', ('Single-frame candidates', '单帧候选区域'), ('Candidate boxes from the image workbench.', '图像工作台中的候选框。')),
    ],
    'signal': [
        ('alias-demo', ('Sampling and aliasing', '采样与混叠'), ('Change the input frequency and inspect the sampled waveform.', '切换输入频率并观察采样波形。')),
        ('valid-frequency-band', ('Frequency response', '频响估计'), ('H1 and the criteria for valid frequency bins.', 'H1 估计与有效频点筛选条件。')),
        ('h1-runs', ('Simulation results', '参数实验结果'), ('27 combinations of noise, window and overlap.', '27 组噪声、窗长及重叠率组合。')),
    ],
    'city': [
        ('offline-route', ('Walking route planner', '步行路线规划'), ('Choose two sites or optimize a multi-stop walk.', '选择起终点，或为自选场址安排步行顺序。')),
        ('route-catalogue', ('Themed routes', '主题路线'), ('Route order and place addresses.', '站点顺序和地点地址。')),
        ('place-search', ('Place index', '地点检索'), ('Search the site register by name or address.', '按名称或地址查询已核对的场址。')),
    ],
    'bathymetry': [
        ('held-out-predictions', ('Model comparison', '模型对照'), ('Linear regression and SVR prediction errors.', '线性回归和 SVR 的预测误差。')),
        ('depth-prediction-table', ('Sample-level predictions', '逐样本预测'), ('Reference depths, predictions and residuals.', '参考水深、预测值及残差。')),
        ('observations', ('Public photon observations', '公开光子观测'), ('Dataset fields and limits on model evaluation.', '数据字段与模型评估适用范围。')),
    ],
    'medical': [
        ('sample-appointment', ('Clinic, package and slot', '医院、套餐和号源'), ('Select a slot and create a sample booking.', '选择号源并创建示例预约。')),
        ('appointments', ('Order management', '订单管理'), ('Review bookings or cancel a pending appointment.', '查看记录或取消待检预约。')),
        ('doctor-demo', ('Doctor-side report entry', '医生端报告录入'), ('Save a report for a pending sample order.', '为待检示例订单保存报告。')),
        ('report', ('Patient report lookup', '用户端报告查询'), ('Read the summary and individual check items.', '查看总检结论和逐项明细。')),
    ],
}
