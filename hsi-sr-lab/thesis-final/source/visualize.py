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

try:
    from model.SSPSR2 import SSPSR_o  # 训练脚本中 SSPSR 对应 SSPSR_o
except ImportError:
    SSPSR_o = None


def load_hsi_data(file_path):
    print(f"📂 加载 Patch 数据: {file_path}")
    data = sio.loadmat(file_path)
    lr = data.get('lr').astype(np.float32)
    hr = data.get('hr').astype(np.float32)

    # --- 归一化逻辑 ---
    # 如果数据最大值远大于 1，说明是原始 DN 值，需要归一化
    if lr.max() > 1.1:
        print(f"📢 检测到数据范围 [0, {lr.max()}], 正在自动归一化到 [0, 1]")
        lr = lr / lr.max()
        hr = hr / hr.max()
    # ---------------------

    if lr.ndim == 3 and lr.shape[-1] > 20:
        lr = np.transpose(lr, (2, 0, 1))
        hr = np.transpose(hr, (2, 0, 1))

    return torch.from_numpy(lr).unsqueeze(0), torch.from_numpy(hr).unsqueeze(0)


def extract_pseudo_color(hsi_tensor, bands=(66, 23, 1), ref_min=None, ref_max=None):
    img = hsi_tensor.squeeze().cpu().numpy()
    if img.ndim == 3 and img.shape[0] > 20:
        img = img.transpose(1, 2, 0)

    rgb = img[:, :, list(bands)].astype(np.float32)

    # 使用百分比截断，增加可视化的稳健性，防止极端噪点导致图片全黑
    if ref_min is None or ref_max is None:
        v_min = np.percentile(rgb, 2)
        v_max = np.percentile(rgb, 98)
    else:
        v_min, v_max = ref_min, ref_max

    rgb = (rgb - v_min) / (v_max - v_min + 1e-8)
    return np.clip(rgb, 0, 1)


def save_image(img_array, save_path, bbox=None):
    h, w = img_array.shape[:2]
    plt.figure(figsize=(w / 100, h / 100), dpi=300)
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


def load_model_weights(model, weights_path, is_sspsr=False):
    print(f"🔄 正在加载权重: {weights_path}")
    checkpoint = torch.load(weights_path, map_location='cpu')
    state_dict = checkpoint['state_dict'] if 'state_dict' in checkpoint else checkpoint

    # 1. 移除 module. 前缀
    state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}

    # 2. 获取当前模型的所有参数名，用于模糊匹配
    model_keys = [n for n, _ in model.named_parameters()]
    new_state_dict = {}

    for k, v in state_dict.items():
        name = k
        if is_sspsr:
            # 策略 A：解决最顽固的 upsample 命名冲突
            # 如果权重里叫 branch.upsample.0 但模型里没有这个，尝试映射到 trunk
            if 'branch.upsample' in name and name not in model_keys:
                # 尝试查找模型中对应的 upsample 键名
                # 常见对应关系：branch.upsample.0 -> trunk.upsample.2
                name = name.replace('branch.upsample.0', 'trunk.upsample.2')

            # 策略 B：全局 branch -> trunk 映射（如果模型是按 trunk 命名的）
            if 'branch.' in name and name not in model_keys:
                potential_name = name.replace('branch.', 'trunk.')
                if potential_name in model_keys:
                    name = potential_name

        new_state_dict[name] = v

    # 3. 执行加载
    missing_keys, unexpected_keys = model.load_state_dict(new_state_dict, strict=False)

    if is_sspsr:
        # 重点检查上采样层是否加载成功
        upsample_missing = [k for k in missing_keys if 'upsample' in k]
        if upsample_missing:
            print(f"❌ 严重警告：上采样权重匹配失败！Missing: {upsample_missing}")
            print(f"💡 提示：权重文件中的键名是: {[k for k in state_dict.keys() if 'upsample' in k]}")
            print(f"💡 提示：模型期待的键名是: {[k for k in model_keys if 'upsample' in k]}")
        else:
            print("✅ SSPSR 权重映射修复成功！所有关键层已对齐。")

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
    colors = colors_dict.get(args.dataset_name, 102)

    bands_dict = {
        'Pavia': (67, 24, 0),
        'HoustonU': (40, 20, 10),
        'Chikusei': (70, 100, 36)
    }
    vis_bands = bands_dict.get(args.dataset_name, (20, 10, 0))

    try:
        bbox_coords = tuple(map(int, args.bbox.split(',')))
    except:
        bbox_coords = None

    lr_tensor, hr_tensor = load_hsi_data(args.test_img_path)
    print(f"DEBUG: LR Shape: {lr_tensor.shape}, HR Shape: {hr_tensor.shape}")
    lr_tensor, hr_tensor = lr_tensor.to(device), hr_tensor.to(device)

    # 提取 HR 极值用于统一归一化
    hr_rgb_raw = hr_tensor.squeeze().cpu().numpy().transpose(1, 2, 0)[:, :, list(vis_bands)]
    ref_min, ref_max = hr_rgb_raw.min(), hr_rgb_raw.max()

    img_hr = extract_pseudo_color(hr_tensor, vis_bands, ref_min, ref_max)
    save_image(img_hr, os.path.join(args.save_dir, "HR_GroundTruth.png"), bbox=None)

    sr_bicubic = F.interpolate(lr_tensor, scale_factor=args.scale, mode='bicubic', align_corners=False)
    img_bicubic = extract_pseudo_color(sr_bicubic, vis_bands, ref_min, ref_max)
    save_image(img_bicubic, os.path.join(args.save_dir, f"Bicubic_x{args.scale}.png"), bbox=None)
    save_error_map(sr_bicubic, hr_tensor, os.path.join(args.save_dir, f"Bicubic_x{args.scale}_error.png"),
                   bbox=bbox_coords)

    # 1. 基线模型
    if args.baseline_weight:
        if args.model_title == 'MCnet':
            net_base = MCnet(n_colors=colors, n_conv=1).to(device)
        elif args.model_title == 'SSPSR':
            # ❗ 核心修复点 1：对齐训练代码，SSPSR 参数对应 SSPSR_o 类
            # ❗ 核心修复点 2：移除 res_scale=0.1，使用类默认值（通常为 1.0）
            net_base = SSPSR_o(n_colors=colors, n_scale=args.scale).to(device)
        elif args.model_title == 'SSPSR_b':
            # ❗ 核心修复点 1：对齐训练代码，SSPSR-b 参数对应 SSPSR 类
            # ❗ 核心修复点 2：移除 res_scale=0.1，使用类默认值
            net_base = SSPSR(n_colors=colors, n_scale=args.scale).to(device)
        elif args.model_title == 'ERCSR':
            net_base = ERCSR(n_colors=colors).to(device)

        is_sspsr = args.model_title in ['SSPSR', 'SSPSR_b']
        net_base = load_model_weights(net_base, args.baseline_weight, is_sspsr).eval()

        with torch.no_grad():
            sr_base = net_base(lr_tensor)
            if isinstance(sr_base, tuple): sr_base = sr_base[0]
            print(f"📊 基线模型 SR 数值范围: Min={sr_base.min().item():.4f}, Max={sr_base.max().item():.4f}, Mean={sr_base.mean().item():.4f}")

        # 钳制负值和超限值
        sr_base = torch.clamp(sr_base, 0, 1.0)
        img_base = extract_pseudo_color(sr_base, vis_bands, ref_min, ref_max)
        save_image(img_base, os.path.join(args.save_dir, f"{args.model_title}_x{args.scale}.png"), bbox=None)
        save_error_map(sr_base, hr_tensor, os.path.join(args.save_dir, f"{args.model_title}_x{args.scale}_error.png"),
                       bbox=bbox_coords)

    # 2. MCArb 模型
    if args.mcarb_weight:
        if args.model_title == 'MCnet':
            net_mcarb = ad_meta_MCnet(n_colors=colors, n_feats=64, upmode='Meta_upsample_3d_3', experts=4).to(device)
        elif args.model_title in ['SSPSR', 'SSPSR_b']:
            net_mcarb = ad_meta_SSPSR(n_colors=colors, n_feats=256, upmode='Meta_upsample_com_3d_2', experts=4).to(device)
        elif args.model_title == 'ERCSR':
            net_mcarb = ad_meta_ERCSR(n_colors=colors, n_feats=64, upmode='Meta_upsample_3d_3', experts=4).to(device)

        net_mcarb = load_model_weights(net_mcarb, args.mcarb_weight).eval()
        with torch.no_grad():
            sr_mcarb = net_mcarb(lr_tensor, args.scale)
            if isinstance(sr_mcarb, tuple): sr_mcarb = sr_mcarb[0]
            print(f"📊 MCArb模型 SR 数值范围: Min={sr_mcarb.min().item():.4f}, Max={sr_mcarb.max().item():.4f}, Mean={sr_mcarb.mean().item():.4f}")

        # 钳制负值和超限值
        sr_mcarb = torch.clamp(sr_mcarb, 0, 1.0)
        img_mcarb = extract_pseudo_color(sr_mcarb, vis_bands, ref_min, ref_max)
        save_image(img_mcarb, os.path.join(args.save_dir, f"MCArb_{args.model_title}_x{args.scale}.png"),
                   bbox=None)
        save_error_map(sr_mcarb, hr_tensor,
                       os.path.join(args.save_dir, f"MCArb_{args.model_title}_x{args.scale}_error.png"),
                       bbox=bbox_coords)

    print("\n🎉 所有图像处理完毕！")


if __name__ == "__main__":
    main()