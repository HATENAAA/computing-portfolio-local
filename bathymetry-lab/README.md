# 卫星测深回归分析

双击仓库根目录的 `Launch Project.command`，选择「7 Satellite Bathymetry」。

- **比较模型**打开时自动用固定种子的合成样本拟合线性回归和 SVR，以完整分组留出测试样本。点击散点或选择 CSV 行，可核对参考水深和预测残差。
- **预测新样本**用当前模型对三条示例反射率进行预测，也可选择自己的波段 CSV。页面预览前 12 条预测，下载包含全部行、训练范围检查和负值标记。
- **查看光子轨迹**可切换波束、轨迹段，查看沿轨距离和相对平均海平面的高度。数据来自 Fengyu Li 的珊瑚礁光子点表，CC BY 4.0。[Zenodo v1 数据归档](https://zenodo.org/records/19937366)

自有训练 CSV 需要 B2、B3、B4、B8、depth_m、group_id、photon_date、image_date。depth_m 为非负水深，单位米，日期格式为 YYYY-MM-DD。同组样本应来自同一轨道、场景或空间块。预测 CSV 只要求四个波段，单位可分别选择反射率或 DN（比例因子 0.0001、偏移量 0）。

光子剖面来自随作品集提供的 assets/public-data/reef-points.csv。运行 scripts/build_profiles.py 可复建离线图表：按波束和超过 60 秒的观测间隔分段，计算全段高度统计，再从按沿轨距离排序的每段等序抽取至多 320 个点。原始高度和配对水深的语义不同；回归评价使用标注 CSV 的 depth_m。
