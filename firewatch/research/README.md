# 视频事件评测

数据：[FURG](https://github.com/steffensbola/furg-fire-dataset)，附CC0许可。下载4段原视频与对应XML：Car1、non_fire_patrolbot_onboard为验证；house6、cleaner为测试。来源分组不跨集合；模型训练集未知，不能认证与模型训练数据独立。每秒采样1帧，每段最多120秒，所有采样和事件真值保留在public-probe/manifest.json。

模型：[Fire-Detection-Engine-ONNX](https://huggingface.co/prithivMLmods/Fire-Detection-Engine-ONNX)，固定revision 02bd7f981aac3e27a75f83e0a3b97dfadaffc228，Apache-2.0。附实际量化权重、预处理、来源和许可。它是ViT图像分类器，不提供检测框；空间IoU只评价规则基线。这里不采用发布者的精度宣称。

安装原项目依赖后，额外执行 `python -m pip install -r requirements-research.txt`，在firewatch目录运行：

```
python scripts/public_experiment.py research/public-furg research/models/fire-classifier-quantized.onnx
python scripts/benchmark.py research/public-probe/manifest.json --out research/new-replay.json
```

第一条重新执行CPU模型与规则；第二条只复算保存的分数轨迹。输出目录public-probe是本次固定探针，重跑前请复制保存，正式实验使用新的目录和报告版本。

阈值0.2/0.5/0.8与确认1/3/5帧只在验证集选择；冻结后测试时间IoU为0.25/0.5/0.75。测试确认帧消融是描述性分析，不重新选部署参数。事件误报/小时分母是完整已标注分析时长，不能称为纯背景误报率；延迟仅定义于成功匹配事件，未匹配时为null，不填0。采样区间采用一帧至下一采样时刻，末尾截至分析终点。

结果保留失败：IoU=0.5下规则TP=0/FP=0/FN=1；模型TP=0/FP=2/FN=1。零误报的规则同时完全漏检，不能声称有效。模型误报/小时约48.1553，仅为短视频时长折算，没有稳定总体率的统计意义。灯光、夕阳、反光、橙色物体的完整困难负样本独立覆盖仍未补齐。

逐视频场景、误报类别、未匹配事件、确认帧与IoU敏感性在public-probe/report.json；默认网站 `/static/research.html` 可查看本次对照。原始视频与模型可运行不代表已达到部署性能。
