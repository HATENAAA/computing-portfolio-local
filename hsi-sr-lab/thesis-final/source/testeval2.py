import torch
import numpy as np
import os
from torch.utils.data import DataLoader

# 假设你的数据和评测指标在这些文件里
from data import HSTestData
from metrics import quality_assessment

# ----------------- 导入所有可用模型 -----------------
from model.MCnet import MCnet
from model.SSPSR import SSPSR
from model.SSPSR2 import SSPSR_o
from model.ERCSR import ERCSR
from model.ad_meta_MCnet import ad_meta_MCnet
from model.ad_meta_SSPSR import ad_meta_SSPSR
from model.ad_meta_ERCSR import ad_meta_ERCSR

# =====================================================================
#                          全局配置区 (在此处切换实验设置)
# =====================================================================

# 1. 设置数据集: 'Pavia', 'Chikusei'
# DATASET_NAME = 'Chikusei'
DATASET_NAME = 'Pavia'

# 2. 设置放大倍率: 2, 4, 8
SCALE = 4

# 3. 设置模型名称
# 固定倍率: 'MCnet', 'SSPSR', 'SSPSR-b', 'ERCSR'
# Meta模型: 'ad_meta_MCnet', 'ad_meta_SSPSR', 'ad_meta_ERCSR'
# MODEL_NAME = 'ad_meta_SSPSR'
MODEL_NAME = 'ad_meta_MCnet'

# 4. 设置 Meta 模型的上采样模式 (仅对 ad_meta_ 系列有效)
# UPMODE = 'Meta_upsample_com_3d_2'
UPMODE = 'Meta_upsample_3d_3'

# 5. 设置权重路径
# ⚠️ 强烈建议：将这里的 net_last.pth 改为你训练过程中保存的 PSNR 最高的 best 权重
WEIGHT_PATH = r'E:\Graduation Design\final\MCArb_HSI_SR-main\checkpoints\MCnet\Pavia\Meta_upsample_3d_3_adapt\20260402-16-59-25p\net_x4.pth'


# =====================================================================

def evaluate_model():
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️ 正在使用设备: {device}")
    print(f"📊 当前评估配置 => 数据集: {DATASET_NAME}, 缩放倍率: x{SCALE}, 模型: {MODEL_NAME}")

    # ================= 1. 自动配置数据集 =================
    if DATASET_NAME == 'Pavia':
        n_colors = 102
        test_mat_path = 'dataset/Pavia/test/Pavia_test.mat'
    elif DATASET_NAME == 'Chikusei':
        n_colors = 128
        test_mat_path = 'dataset/Chikusei/test/Chikusei_test.mat'
    else:
        raise ValueError(f"不支持的数据集: {DATASET_NAME}")

    # 兼容不同的路径命名习惯
    if not os.path.exists(test_mat_path):
        test_mat_path = test_mat_path.replace('dataset/', 'datasets/')

    test_set = HSTestData(image_dir=test_mat_path)
    test_loader = DataLoader(test_set, batch_size=1, shuffle=False)

    # ================= 2. 初始化模型 =================
    print('🛠️ 正在构建模型...')
    if MODEL_NAME == 'MCnet':
        net = MCnet(n_colors=n_colors, n_scale=SCALE)
    elif MODEL_NAME == 'SSPSR-b':
        net = SSPSR(n_colors=n_colors, n_scale=SCALE)
    elif MODEL_NAME == 'SSPSR':
        net = SSPSR_o(n_colors=n_colors, n_scale=SCALE)
    elif MODEL_NAME == 'ERCSR':
        net = ERCSR(n_colors=n_colors, n_scale=SCALE)
    elif MODEL_NAME == 'ad_meta_MCnet':
        net = ad_meta_MCnet(n_colors=n_colors, upmode=UPMODE)
    elif MODEL_NAME == 'ad_meta_SSPSR':
        net = ad_meta_SSPSR(n_colors=n_colors, upmode=UPMODE)
    elif MODEL_NAME == 'ad_meta_ERCSR':
        net = ad_meta_ERCSR(n_colors=n_colors, upmode=UPMODE)
    else:
        raise ValueError(f"未定义的模型初始化逻辑: {MODEL_NAME}")

    net = net.to(device)

    # ================= 3. 加载权重 =================
    print(f"🔄 正在加载权重: {WEIGHT_PATH}")
    checkpoint = torch.load(WEIGHT_PATH, map_location=device)
    # 处理 DataParallel 带来的 module. 前缀
    if 'module.' in list(checkpoint.keys())[0]:
        from collections import OrderedDict
        new_state_dict = OrderedDict()
        for k, v in checkpoint.items():
            new_state_dict[k.replace('module.', '')] = v
        net.load_state_dict(new_state_dict)
    else:
        net.load_state_dict(checkpoint)
    net.eval()

    # ================= 4. 初始化指标记录器 =================
    total_metrics = {'MPSNR': 0, 'MSSIM': 0, 'SAM': 0, 'ERGAS': 0, 'RMSE': 0, 'CrossCorrelation': 0}
    num_images = 0

    print("⏳ 正在进行测试评估，请稍候...")
    with torch.no_grad():
        for lrx8, lrx4, lrx2, hr in test_loader:
            # 根据测试倍率选择对应的输入 LR
            if SCALE == 2:
                lr = lrx2.to(device)
            elif SCALE == 4:
                lr = lrx4.to(device)
            elif SCALE == 8:
                lr = lrx8.to(device)
            else:
                raise ValueError("不支持的 Scale")

            hr = hr.to(device)

            # 模型前向推理
            is_meta_model = 'meta' in MODEL_NAME.lower()
            if is_meta_model:
                out = net(lr, n_scale=SCALE)
            else:
                out = net(lr)

            # 处理多输出模型 (取第一个输出为重建图像)
            sr = out[0] if isinstance(out, (list, tuple)) else out

            # ================= 5. 数据后处理与评测 =================
            # 维度转换 (B,C,H,W) -> (H,W,C) 并转回 CPU
            sr_np = sr.squeeze(0).permute(1, 2, 0).cpu().numpy()
            hr_np = hr.squeeze(0).permute(1, 2, 0).cpu().numpy()

            # 严格限幅到 [0, 1] 范围
            sr_np = np.clip(sr_np, 0.0, 1.0)
            hr_np = np.clip(hr_np, 0.0, 1.0)

            # 🚀 核心修改点：严格对齐论文中的评测参数
            scores = quality_assessment(
                x_true=hr_np,
                x_pred=sr_np,
                data_range=1.0,  # 保持在 0-1 范围计算
                ratio=SCALE,  # 传入真实的缩放倍率，用于边缘裁剪 (Border Shaving)
                multi_dimension=False,  # 逐波段计算 SSIM 然后求均值
                block_size=8  # 局部窗口大小设为 8
            )

            # 累加结果 (动态兼容 metrics 字典的键名)
            for k in total_metrics.keys():
                # 如果 quality_assessment 返回的是 'PSNR' 而不是 'MPSNR'，做一下兼容匹配
                key_in_scores = k if k in scores else (k[1:] if k.startswith('M') and k[1:] in scores else k)
                if key_in_scores in scores:
                    total_metrics[k] += scores[key_in_scores]
                elif k == 'CrossCorrelation' and 'CC' in scores:
                    total_metrics[k] += scores['CC']

            num_images += 1

    # ================= 6. 打印最终结果 =================
    print("\n" + "=" * 45)
    print(f"🏆 评估报告 | 数据集: {DATASET_NAME} | 缩放: x{SCALE}")
    print(f"🧠 模型: {MODEL_NAME}")
    if is_meta_model:
        print(f"⚙️ Meta 模式: {UPMODE}")
    print(f"🖼️ 共测试了 {num_images} 张图像。")
    print("-" * 45)

    display_names = {
        'MPSNR': 'PSNR ↑',
        'MSSIM': 'SSIM ↑',
        'CrossCorrelation': 'CC ↑',
        'SAM': 'SAM ↓',
        'ERGAS': 'ERGAS ↓',
        'RMSE': 'RMSE ↓'
    }

    for k, v in total_metrics.items():
        name = display_names.get(k, k)
        avg_score = v / num_images
        print(f"指标 {name:<12}: {avg_score:.4f}")
    print("=" * 45 + "\n")


if __name__ == "__main__":
    evaluate_model()