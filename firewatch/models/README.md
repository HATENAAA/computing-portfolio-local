# 火焰定位模型

默认权重来自 [CCTV-AI 发布页](https://huggingface.co/fiacecson20/cctv-ai-fire-smoke/tree/343990e42d99a5d27e9f35fc7c80880dc5f43f45)，输入为 320×320。模型包含 fire 和 smoke，当前任务只评价 fire（类别 0）。发布者声明权重为 MIT，基础模型及 ONNX 内嵌元数据标注 AGPL-3.0，原模型说明随权重保存。视频事件研究另用图像分类器。

评测材料来自 [FURG 原始视频与逐帧矩形标注](https://github.com/steffensbola/furg-fire-dataset/tree/6aff09d7baa27425f31d1df685284c26cbffe7af)。运行 `python scripts/build_box_samples.py` 可从随附原文件重新生成样本，按每段可解码视频的首末帧等距抽取 8 帧。目录 app/static/furg 中的 catalog.json 记录来源、划分与哈希。

## 替换模型

1. 使用你有权使用的火焰／烟雾检测权重，记录来源、许可证、训练集和独立测试集。训练或导出可参考 [Ultralytics ONNX 导出教程](https://academy.ultralytics.com/courses/train-your-first-yolo/export-for-deployment) 与 [导出格式文档](https://docs.ultralytics.com/modes/export)。遵守所用代码与权重的许可要求。
2. 导出静态单批次、FP32、正方形输入的ONNX文件。输入边长128～1280，且为32倍数。预处理为等比例letterbox填充值114，BGR转RGB，float32除以255，NCHW。
3. 复制config.example.json为自己目录中的config.json，填写本机模型相对路径、实际SHA256、类别顺序、目标类别索引和输出协议。可用 `shasum -a 256 fire.onnx` 计算SHA256。不要照抄示例的类别顺序；它必须和真实训练类别一致。
4. 将模型和填写好的config.json放在本项目models目录，启动时会默认读取。也可在启动前设置 `FIREWATCH_MODEL_CONFIG=/绝对路径/config.json` 指定其他位置。更新已加载的模型或配置后需要重启。打开 `/model` 上传图像。

支持两种明确的协议，不自动猜测：

- `yolov8-raw`：形状 `[1,4+C,N]`，前四项为输入像素坐标下的中心x、中心y、宽、高，随后为C个已经归一化的类别分数；不含objectness项。适用于符合此格式、未内嵌NMS的YOLOv8／相同输出布局模型，不支持分割、姿态或OBB输出。
- `xyxy6`：形状 `[1,N,6]`，每行为输入像素坐标下的x1、y1、x2、y2、置信度和整数类别索引。需确认导出文件实际采用此协议；不假定所有YOLO版本相同。

推理执行OpenCV DNN CPU，使用类别内NMS、padding去除、坐标反投影和边界裁剪。输出布局、非有限值、分数范围、类别映射或模型哈希不符时明确报错，不静默回退成规则结果。OpenCV不保证支持所有ONNX算子；不兼容时须调整导出设置或另做推理后端适配。

报告包含输入和模型SHA256、输入大小、类别表、阈值、输出协议和单次耗时。单次CPU时间不是性能基准。图像与视频均可选择已配置的模型。视频任务由所选模型形成候选事件，同时保存规则基线、分歧帧、模型哈希和后处理参数；两种得分不混用。模型事件阈值重放仅支持不低于原分析阈值的参数，低分框没有保存时不伪造重推理结果。

`tests/fixtures/synthetic_detector.onnx` 是446字节的恒定输出测试图，只用于验证真实ONNX加载、前向计算和坐标映射。它没有学习火焰，不能作为业务模型或演示真实识别能力。生成工具仅安装在作者工作目录，运行项目和测试无需安装onnx／PyTorch。
