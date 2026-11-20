# 基于深度学习的遥感影像超分辨率重建

## 本地重建工作台

打开本地应用即可运行三组 Pavia 航测场景裁片，比较最近邻、双线性和双三次重建。工作台以原始裁片为参考，在空间维按像元块取均值构造低分辨率输入。选区指标和像素光谱可单独检查，重建结果、低分辨率输入和评价报告可导出。也可上传成对的 HWC 数组评价自己的重建。

两幅原始 ROSIS 场景由 Pavia 大学提供。裁片坐标、原始阵列校验值和许可记录在 `scene_data/catalog.json`，数据采用学术归档标注的 CC BY-NC-SA 3.0。[数据归档与引用](https://doi.org/10.5281/zenodo.10638886)

## 论文复现实验

本科毕业论文。

复现MCArb框架（Zhang et al., IEEE TGRS 2025），以MCNet／SSPSR／ERCSR为主干，加入3DMetaUM、SAFAM及3DSPPM模块，开展空谱特征学习与多尺度高光谱重建。

在MATLAB中预处理Pavia Centre与Chikusei数据；开发Python评测流程，计算PSNR、SSIM、CC、RMSE、SAM和ERGAS，按逐图平均汇总，并生成重建图像和误差图。

开展协同学习、三维上采样和跨尺度特征对齐消融；在Pavia Centre的×4／×8下，替换为二维上采样使ERCSR的PSNR分别下降1.31／0.42 dB。×2辅助上采样倍率与25%裁剪面积比例取得较均衡结果，与原文一致。

Pavia Centre ×4／×8下，三类MCArb模型的PSNR、SSIM和CC均优于对应基线；MCArb-SSPSR在两数据集及两个尺度上的六项指标均改善（相较SSPSR-b，PSNR +0.21–0.36 dB），并分析空间质量与光谱保真度的权衡。

MCArb-SSPSR相较SSPSR-b，在两数据集及两个尺度的六项指标均改善，PSNR提升0.21–0.36 dB。

根目录运行“启动完整作品集.command”，或通过“启动作品.command”单独启动。应用地址：http://127.0.0.1:8782/。

最终毕设代码、重建图像和指标口径见thesis-final/README.md。MCArb原方法引用与许可见UPSTREAM_README.md和LICENSE。
