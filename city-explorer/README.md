# 上海红色文化地图

作品集内嵌地图和本地应用共用根目录的 `assets/atlas`。地图收录多个城区的历史场址，可选择主题步行路线、规划两点行程、检索和收藏站点，或组合自选路线。自选路线可调整站序，缩短从首站出发的步行距离。

步行距离沿 OpenStreetMap 路网计算，用时按 4.5 公里／小时估算。场址详情附官方资料与对应地图要素链接。地图数据来源和许可见 `assets/atlas/SOURCES.txt`。

地址和主题路线在 `assets/evidence/city-places.json` 中维护。更新路线或地址资料后，从作品集根目录运行 `python3 scripts/atlas_data.py`，再重新构建本地应用。更新底图、点位或步行网络时，使用 `python3 scripts/build_atlas_network.py --help` 查看生成选项。
