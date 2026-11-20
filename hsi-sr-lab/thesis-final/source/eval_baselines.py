import scipy.io as sio
import numpy as np
import torch
import torch.nn.functional as F
import os
import pywt  # 新增：用于 Wavelet 方法
from metrics import quality_assessment


def wavelet_upsample(lr_img, scale_factor):
    """
    基于小波逆变换(IDWT)的高光谱图像上采样
    lr_img: (H, W, C), numpy 数组
    """
    out = lr_img.copy()
    # 计算需要迭代的次数 (例如 4x 是 2次 2倍上采样)
    levels = int(np.log2(scale_factor))

    for _ in range(levels):
        H, W, C = out.shape
        new_out = np.zeros((H * 2, W * 2, C), dtype=np.float32)
        for i in range(C):
            LL = out[:, :, i] * 2.0  # 能量补偿
            LH = np.zeros_like(LL)
            HL = np.zeros_like(LL)
            HH = np.zeros_like(LL)
            # 使用 Haar 小波进行逆变换
            new_out[:, :, i] = pywt.idwt2((LL, (LH, HL, HH)), 'haar')
        out = new_out
    return out


def evaluate_traditional(mat_path, mat_key, scale_list=[4, 8]):
    if not os.path.exists(mat_path):
        print(f"找不到文件: {mat_path}")
        return

    print(f"\n{'=' * 75}")
    print(f" Dataset: {os.path.basename(mat_path)} | Key: {mat_key}")
    print(f"{'=' * 75}")

    try:
        data = sio.loadmat(mat_path)
        hr_batch = data[mat_key].astype(np.float32)

        # 归一化到 [0, 1]
        if hr_batch.max() > 1.0:
            hr_batch /= hr_batch.max()

        # 确保是 4 维 (N, H, W, C)
        if hr_batch.ndim == 3:
            hr_batch = np.expand_dims(hr_batch, axis=0)

        N, H, W, C = hr_batch.shape
        print(f"成功加载数据: 包含 {N} 张图像, 尺寸为 {H}x{W}, 通道数为 {C}")

    except Exception as e:
        print(f"加载数据失败: {e}")
        return

    for scale in scale_list:
        print(f"\n--- 正在计算 {scale}x 尺度 (对 {N} 张图取平均) ---")

        # 用于累加每张图的指标 (新增 Wavelet)
        methods = ['Bilinear', 'Bicubic', 'Wavelet']
        sum_metrics = {m: {'MPSNR': 0, 'MSSIM': 0, 'CrossCorrelation': 0, 'RMSE': 0, 'SAM': 0, 'ERGAS': 0} for m in
                       methods}

        for i in range(N):
            hr_img = hr_batch[i]  # (H, W, C)

            # --- 1. 模拟退化 (Bicubic 下采样) ---
            hr_tensor = torch.from_numpy(hr_img).permute(2, 0, 1).unsqueeze(0).float()
            lr_tensor = F.interpolate(hr_tensor, scale_factor=1 / scale, mode='bicubic', align_corners=False)

            # 准备 LR numpy 用于 Wavelet
            lr_np = lr_tensor.squeeze(0).permute(1, 2, 0).numpy()

            # --- 2. 传统方法放大 ---
            # Bilinear & Bicubic
            sr_bil = F.interpolate(lr_tensor, size=(H, W), mode='bilinear', align_corners=False)
            sr_bic = F.interpolate(lr_tensor, size=(H, W), mode='bicubic', align_corners=False)

            sr_bil_np = np.clip(sr_bil.squeeze(0).permute(1, 2, 0).numpy(), 0.0, 1.0)
            sr_bic_np = np.clip(sr_bic.squeeze(0).permute(1, 2, 0).numpy(), 0.0, 1.0)

            # Wavelet
            sr_wav_np = np.clip(wavelet_upsample(lr_np, scale), 0.0, 1.0)

            # --- 3. 计算指标 (乘以 255 以对齐论文 RMSE 尺度) ---
            res_list = [
                ('Bilinear', quality_assessment(hr_img * 255.0, sr_bil_np * 255.0, data_range=255.0, ratio=scale)),
                ('Bicubic', quality_assessment(hr_img * 255.0, sr_bic_np * 255.0, data_range=255.0, ratio=scale)),
                ('Wavelet', quality_assessment(hr_img * 255.0, sr_wav_np * 255.0, data_range=255.0, ratio=scale))
            ]

            for method_name, res in res_list:
                for k in sum_metrics[method_name].keys():
                    sum_metrics[method_name][k] += res[k]

        # --- 4. 打印平均结果 ---
        header = f"{'Method':<10} | {'MPSNR':<7} | {'MSSIM':<7} | {'CC':<7} | {'RMSE':<7} | {'SAM':<7} | {'ERGAS':<7}"
        print(header)
        print("-" * len(header))

        for method in methods:
            m = sum_metrics[method]
            print(f"{method:<10} | {m['MPSNR'] / N:.4f}  | {m['MSSIM'] / N:.4f}  | "
                  f"{m['CrossCorrelation'] / N:.4f}  | {m['RMSE'] / N:.4f}  | "
                  f"{m['SAM'] / N:.4f}  | {m['ERGAS'] / N:.4f}")


if __name__ == '__main__':
    # 路径配置
    pavia_path = r'E:\Graduation Design\final\MCArb_HSI_SR-main\dataset\Pavia\test\Pavia_test.mat'
    chikusei_path = r'E:\Graduation Design\final\MCArb_HSI_SR-main\dataset\Chikusei\test\Chikusei_test.mat'

    # 执行评估
    evaluate_traditional(pavia_path, mat_key='hr', scale_list=[4, 8])
    evaluate_traditional(chikusei_path, mat_key='hr', scale_list=[4, 8])