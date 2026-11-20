# 毕业论文实验材料

论文：《基于深度学习的遥感影像超分辨率重建》。项目周期：2025年10月—2026年5月。

- `source/test_eval.py`、`source/testeval2.py`：逐图计算六项指标，再按图像数求平均。
- `source/visualize.py`：真值、插值基线、网络重建与误差图。
- `source/matlab_code/`：高光谱数据预处理。
- `images/pavia/`、`images/chikusei/`：最终归档中的×4重建图和误差图。
- `manifest.json`：逐文件SHA-256，可核对最终归档副本。

运行训练和评价时，在配置区设置本机数据集、模型与权重路径。`test_eval.py`使用255量程；`testeval2.py`使用0–1量程及对应指标参数，应分别保留其配置。数据集与检查点由本机完整毕设目录提供，未重复打包多GB数据。训练、评价和可视化代码按原文件保存。

方法：Zhang et al., Meta-Collaborative Learning for Arbitrarily Scaled Hyperspectral Image Super-Resolution, IEEE TGRS, 2025。源代码许可见`source/LICENSE`。

交互评价工具可上传HWC数组，查看波段、像素光谱和ROI六指标。experiment_eval.py提供按场景分组的结果组织，不替代论文逐图平均口径。
