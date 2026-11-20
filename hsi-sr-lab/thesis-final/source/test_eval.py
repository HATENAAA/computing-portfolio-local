import torch
import numpy as np
import os
from torch.utils.data import DataLoader
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

# # 1. 设置数据集: 'Pavia', 'Chikusei'
# DATASET_NAME = 'Chikusei'
DATASET_NAME = 'Pavia'

# 2. 设置放大倍率: 2, 4, 8
SCALE = 4

# 3. 设置模型名称
# 固定倍率: 'MCnet', 'SSPSR', 'SSPSR-b', 'ERCSR'
# Meta模型: 'ad_meta_MCnet', 'ad_meta_SSPSR', 'ad_meta_ERCSR'
# MODEL_NAME ='ERCSR'
# MODEL_NAME = 'MCnet'
# MODEL_NAME = 'SSPSR'
# MODEL_NAME ='SSPSR-b'
# MODEL_NAME ='ad_meta_ERCSR'
MODEL_NAME = 'ad_meta_MCnet'
# MODEL_NAME = 'ad_meta_SSPSR'

# 4. 新增：统一设置 Meta 模型的上采样模式
# 建议将你需要的模式写在这里，方便第 7 步打印输出
# 例如: 'Meta_upsample_3d_3' 或 'Meta_upsample_com_3d_2'
UPMODE = 'Meta_upsample_3d_3'
# UPMODE ='Meta_upsample_com_3d_2'
# UPMODE = 'Meta_upsample'

# 5. 设置权重路径
WEIGHT_PATH = r'E:\Graduation Design\final\MCArb_HSI_SR-main\checkpoints\MCnet\Pavia\Meta_upsample_3d_3_adapt_x4\20260403-13-17\net_x4.pth'

# =====================================================================

def evaluate_model():
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print(f"正在使用设备: {device}")
    print(f"当前评估配置 => 数据集: {DATASET_NAME}, 缩放倍率: x{SCALE}, 模型: {MODEL_NAME}")

    # ================= 1. 自动配置数据集 =================
    if DATASET_NAME == 'Pavia':
        n_colors = 102
        test_mat_path = 'dataset/Pavia/test/Pavia_test.mat'
    elif DATASET_NAME == 'Chikusei':
        n_colors = 128
        test_mat_path = 'dataset/Chikusei/test/Chikusei_test.mat'
    else:
        raise ValueError(f"不支持的数据集: {DATASET_NAME}")

    if not os.path.exists(test_mat_path):
        test_mat_path = test_mat_path.replace('dataset/', 'datasets/')

    test_set = HSTestData(image_dir=test_mat_path)
    test_loader = DataLoader(test_set, batch_size=1, shuffle=False)

    # ================= 2. 初始化模型 (使用全局定义的 UPMODE) =================
    print('正在构建模型...')
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
    checkpoint = torch.load(WEIGHT_PATH, map_location=device)
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
    total_metrics = {'MPSNR': 0, 'MSSIM': 0, 'CrossCorrelation': 0, 'RMSE': 0, 'SAM': 0, 'ERGAS': 0 }
    num_images = 0

    with torch.no_grad():
        for lrx8, lrx4, lrx2, hr in test_loader:
            if SCALE == 2: lr = lrx2.to(device)
            elif SCALE == 4: lr = lrx4.to(device)
            elif SCALE == 8: lr = lrx8.to(device)
            hr = hr.to(device)

            is_meta_model = 'meta' in MODEL_NAME.lower()
            if is_meta_model:
                out = net(lr, n_scale=SCALE)
            else:
                out = net(lr)

            sr = out[0] if isinstance(out, (list, tuple)) else out

            # 维度转换 (B,C,H,W) -> (H,W,C)
            sr_np = sr.squeeze(0).permute(1, 2, 0).cpu().numpy()
            hr_np = hr.squeeze(0).permute(1, 2, 0).cpu().numpy()
            sr_np = np.clip(sr_np, 0.0, 1.0)

            # 计算指标 (乘以 255 以获得论文标准的 RMSE)
            scores = quality_assessment(x_true=hr_np * 255, x_pred=sr_np * 255, data_range=255.0, ratio=SCALE)

            for k in total_metrics.keys():
                total_metrics[k] += scores[k]
            num_images += 1

    # ================= 7. 打印结果 =================
    print("=" * 40)
    print(f"评估报告 | 数据集: {DATASET_NAME} | 模型: {MODEL_NAME} | 缩放: x{SCALE}")
    if is_meta_model:
        print(f"Meta 模式: {UPMODE}")
    print(f"共测试 {num_images} 张图像。")
    print("-" * 40)

    display_names = {
        'MPSNR': 'PSNR',
        'MSSIM': 'SSIM',
        'CrossCorrelation': 'CC',
        'SAM': 'SAM',
        'ERGAS': 'ERGAS',
        'RMSE': 'RMSE'
    }

    for k, v in total_metrics.items():
        name = display_names.get(k, k)
        print(f"Average {name:<15}: {v / num_images:.4f}")
    print("=" * 40)

if __name__ == "__main__":
    evaluate_model()