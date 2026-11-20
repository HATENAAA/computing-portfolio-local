import argparse
import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import scipy.io as sio

# 导入你的模型 (请确保路径与你的项目结构一致)
from model.ad_meta_MCnet import ad_meta_MCnet
from model.ad_meta_ERCSR import ad_meta_ERCSR
from model.ad_meta_SSPSR import ad_meta_SSPSR

from model.MCnet import MCnet
from model.ERCSR import ERCSR
from model.SSPSR import SSPSR
from model.SSPSR2 import SSPSR_o  # 对应 SSPSR-b


def load_hsi_data(file_path):
    print(f"📂 加载 Patch 数据: {file_path}")
    data = sio.loadmat(file_path)
    # 强制不进行任何额外归一化，直接取 makepatch 生成的 0-1 数据
    lr = data.get('lr').astype(np.float32)
    hr = data.get('hr').astype(np.float32)

    # MATLAB 生成的默认形状是 (H, W, C)，如果是这样需要转置为 PyTorch 格式
    if lr.shape[-1] > 20:  # 粗略判断最后一个维度是不是通道数
        lr = lr.transpose(2, 0, 1)
        hr = hr.transpose(2, 0, 1)

    return torch.from_numpy(lr).unsqueeze(0), torch.from_numpy(hr).unsqueeze(0)


def extract_pseudo_color(hsi_tensor, bands=(66, 23, 1), ref_min=None, ref_max=None):
    """
    提取伪彩色图像。
    引入 ref_min 和 ref_max 强制所有图像在同一标准下归一化。
    """
    img = hsi_tensor.squeeze().cpu().numpy()
    if img.ndim == 3 and img.shape[0] > 20:  # 确保通道在最后以便绘图
        img = img.transpose(1, 2, 0)

    # 提取指定波段
    rgb = img[:, :, list(bands)].astype(np.float32)

    # 如果没有提供参考极值，则使用自身的极值（通常是 HR 会提供）
    v_min = ref_min if ref_min is not None else rgb.min()
    v_max = ref_max if ref_max is not None else rgb.max()

    # 核心：使用统一基准进行线性拉伸
    rgb = (rgb - v_min) / (v_max - v_min + 1e-8)

    # 适度增强对比度 (可选，仅为显示更清晰，不改变频域特征)
    # 原先复杂的 gamma 等操作已移除，防止失真
    rgb = np.clip(rgb, 0, 1)

    return rgb


def save_image(img_array, save_path, bbox=None):
    # 根据图像比例自动计算 figsize，防止变形
    h, w = img_array.shape[:2]
    fig_w, fig_h = w / 100, h / 100

    plt.figure(figsize=(fig_w, fig_h), dpi=300)
    plt.imshow(img_array)

    if bbox is not None:
        x, y, bw, bh = bbox
        rect = patches.Rectangle((x, y), bw, bh, linewidth=1.5, edgecolor='red', facecolor='none')
        plt.gca().add_patch(rect)

    plt.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
    plt.close()


def save_error_map(sr_tensor, hr_tensor, save_path, bbox=None):
    diff = torch.abs(sr_tensor - hr_tensor)
    diff_map = diff.mean(dim=1).squeeze().cpu().numpy()

    # 热力图的量程可以根据实际误差情况微调
    # 如果大部分区域是蓝色，说明模型表现很好
    fixed_vmax = 0.2

    h, w = diff_map.shape[:2]
    plt.figure(figsize=(w / 100, h / 100), dpi=300)

    plt.imshow(diff_map, cmap='jet', vmin=0, vmax=fixed_vmax)

    if bbox is not None:
        x, y, bw, bh = bbox
        rect = patches.Rectangle((x, y), bw, bh, linewidth=1.5, edgecolor='red', facecolor='none')
        plt.gca().add_patch(rect)

    plt.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f"🎨 热力图已保存: {os.path.basename(save_path)}")


def load_model_weights(model, weights_path):
    print(f"🔄 加载权重: {weights_path}")
    checkpoint = torch.load(weights_path, map_location='cpu')
    state_dict = checkpoint['state_dict'] if 'state_dict' in checkpoint else checkpoint
    new_state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
    model.load_state_dict(new_state_dict, strict=True)
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_title", type=str, default="ERCSR", choices=['MCnet', 'SSPSR', 'SSPSR_b', 'ERCSR'])
    parser.add_argument("--dataset_name", type=str, default="Pavia")
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--test_img_path", type=str, required=True)
    parser.add_argument("--baseline_weight", type=str)
    parser.add_argument("--mcarb_weight", type=str)
    parser.add_argument("--save_dir", type=str, default="./visual_results")
    parser.add_argument("--cuda", type=str, default="0")
    parser.add_argument("--bbox", type=str, default="30,30,40,40", help="红框坐标: x,y,w,h")
    args = parser.parse_args()

    os.environ['CUDA_VISIBLE_DEVICES'] = args.cuda
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    os.makedirs(args.save_dir, exist_ok=True)

    colors_dict = {'HoustonU': 48, 'Pavia': 102, 'Chikusei': 128}
    colors = colors_dict[args.dataset_name]

    # 原作中的波段选择
    bands_dict = {
        'Pavia': (67, 24, 0),  # 原文提及的 Pavia 可视化波段
        'HoustonU': (40, 20, 10),
        'Chikusei': (70, 50, 30)
    }
    vis_bands = bands_dict.get(args.dataset_name, (20, 10, 0))

    try:
        bbox_coords = tuple(map(int, args.bbox.split(',')))
    except:
        bbox_coords = None

    lr_tensor, hr_tensor = load_hsi_data(args.test_img_path)
    lr_tensor, hr_tensor = lr_tensor.to(device), hr_tensor.to(device)

    # ==========================================
    # 0. 提取 HR 的极值作为统一归一化参考
    # ==========================================
    hr_rgb_raw = hr_tensor.squeeze().cpu().numpy().transpose(1, 2, 0)[:, :, list(vis_bands)]
    ref_min = hr_rgb_raw.min()
    ref_max = hr_rgb_raw.max()

    # 渲染 GT
    img_hr = extract_pseudo_color(hr_tensor, vis_bands, ref_min, ref_max)
    save_image(img_hr, os.path.join(args.save_dir, "HR_GroundTruth.png"), bbox=bbox_coords)

    # 渲染 Bicubic
    sr_bicubic = F.interpolate(lr_tensor, scale_factor=args.scale, mode='bicubic', align_corners=False)
    img_bicubic = extract_pseudo_color(sr_bicubic, vis_bands, ref_min, ref_max)
    save_image(img_bicubic, os.path.join(args.save_dir, f"Bicubic_x{args.scale}.png"), bbox=bbox_coords)
    save_error_map(sr_bicubic, hr_tensor, os.path.join(args.save_dir, f"Bicubic_x{args.scale}_error.png"),
                   bbox=bbox_coords)

    # ==========================================
    # 1. 基线模型推理 (Baseline Models)
    # ==========================================
    if args.baseline_weight:
        if args.model_title == 'MCnet':
            net_base = MCnet(n_colors=colors, n_conv=1).to(device)
        elif args.model_title == 'SSPSR':
            net_base = SSPSR(n_colors=colors, n_scale=args.scale, res_scale=0.1).to(device)
        elif args.model_title == 'SSPSR_b':
            net_base = SSPSR_o(n_colors=colors, n_scale=args.scale, res_scale=0.1).to(device)
        elif args.model_title == 'ERCSR':
            net_base = ERCSR(n_colors=colors).to(device)

        net_base = load_model_weights(net_base, args.baseline_weight).eval()
        with torch.no_grad():
            sr_base = net_base(lr_tensor)
            if isinstance(sr_base, tuple): sr_base = sr_base[0]

        sr_base = torch.clamp(sr_base, 0, 1.0)
        img_base = extract_pseudo_color(sr_base, vis_bands, ref_min, ref_max)
        save_image(img_base, os.path.join(args.save_dir, f"{args.model_title}_x{args.scale}.png"), bbox=bbox_coords)
        save_error_map(sr_base, hr_tensor, os.path.join(args.save_dir, f"{args.model_title}_x{args.scale}_error.png"),
                       bbox=bbox_coords)

    # ==========================================
    # 2. MCArb 模型推理 (MCArb Adapters)
    # ==========================================
    if args.mcarb_weight:
        if args.model_title == 'MCnet':
            net_mcarb = ad_meta_MCnet(n_colors=colors, n_feats=64, upmode='Meta_upsample_3d_3', experts=4).to(device)
        elif args.model_title in ['SSPSR', 'SSPSR_b']:
            net_mcarb = ad_meta_SSPSR(n_colors=colors, n_feats=256, upmode='Meta_upsample_3d_3', experts=4).to(device)
        elif args.model_title == 'ERCSR':
            net_mcarb = ad_meta_ERCSR(n_colors=colors, n_feats=64, upmode='Meta_upsample_3d_3', experts=4).to(device)

        net_mcarb = load_model_weights(net_mcarb, args.mcarb_weight).eval()
        with torch.no_grad():
            sr_mcarb = net_mcarb(lr_tensor, args.scale)
            if isinstance(sr_mcarb, tuple): sr_mcarb = sr_mcarb[0]

        sr_mcarb = torch.clamp(sr_mcarb, 0, 1.0)
        img_mcarb = extract_pseudo_color(sr_mcarb, vis_bands, ref_min, ref_max)
        save_image(img_mcarb, os.path.join(args.save_dir, f"MCArb_{args.model_title}_x{args.scale}.png"),
                   bbox=bbox_coords)
        save_error_map(sr_mcarb, hr_tensor,
                       os.path.join(args.save_dir, f"MCArb_{args.model_title}_x{args.scale}_error.png"),
                       bbox=bbox_coords)

    print("\n🎉 所有图像处理完毕！")


if __name__ == "__main__":
    main()