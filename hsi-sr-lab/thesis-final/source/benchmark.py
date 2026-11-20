import argparse
import torch
import time
from thop import profile
import os

# 从你的 model 文件夹中导入模型
from model.ad_meta_MCnet import ad_meta_MCnet
from model.ad_meta_ERCSR import ad_meta_ERCSR
from model.ad_meta_SSPSR import ad_meta_SSPSR


# 如果你也想评测基线模型，可以取消下面三行的注释并在字典中加入它们
from model.MCnet import MCnet
from model.ERCSR import ERCSR
from model.SSPSR import SSPSR

def benchmark_model(model, input_tensor, scale, device):
    """
    评测模型的 FLOPs, Params, GPU Memory 和 ExecTime
    """
    model = model.to(device)
    model.eval()
    input_tensor = input_tensor.to(device)

    print(f"\n" + "=" * 50)
    print(f"📊 正在评测模型...")
    print(f"🔹 输入形状: {input_tensor.shape} (Batch, Channels, Height, Width)")
    print(f"🔹 缩放倍率: {scale}x")
    print("=" * 50)

    # ==========================================
    # 1. 测量 FLOPs (G) 和 Params (M)
    # ==========================================
    print("⏳ 正在计算 FLOPs 和 Params...")
    try:
        with torch.no_grad():
            # 注意：如果你的模型 forward 有多个参数，需要用元组传入
            flops, params = profile(model, inputs=(input_tensor, scale), verbose=False)
        flops_G = flops / 1e9  # 转换为 Gigaflops (10^9)
        params_M = params / 1e6  # 转换为 Millions (10^6)
    except Exception as e:
        print(f"❌ FLOPs 计算失败: {e}")
        flops_G, params_M = 0, 0

    # ==========================================
    # 2. 测量 ExecTime (s) (执行时间)
    # ==========================================
    print("⏳ 正在测试执行时间 (含预热)...")
    warmup_iters = 10
    measure_iters = 50

    with torch.no_grad():
        # 预热 GPU
        for _ in range(warmup_iters):
            _ = model(input_tensor, scale)

    if device.type == 'cuda':
        torch.cuda.synchronize()
    start_time = time.time()

    with torch.no_grad():
        for _ in range(measure_iters):
            _ = model(input_tensor, scale)

    if device.type == 'cuda':
        torch.cuda.synchronize()
    end_time = time.time()

    exec_time = (end_time - start_time) / measure_iters  # 平均每次前向传播的秒数

    # ==========================================
    # 3. 测量 GPU Memory (M) (显存占用峰值)
    # ==========================================
    print("⏳ 正在测试显存占用峰值...")
    mem_M = 0
    if device.type == 'cuda':
        torch.cuda.reset_peak_memory_stats(device)
        with torch.no_grad():
            _ = model(input_tensor, scale)
        max_mem_bytes = torch.cuda.max_memory_allocated(device)
        mem_M = max_mem_bytes / (1024 * 1024)  # 转换为 MB

    # ==========================================
    # 打印最终结果
    # ==========================================
    print("\n" + "🌟" * 25)
    print(f"🏆 评测结果摘要")
    print("🌟" * 25)
    print(f"⚙️ FLOPs (G):    {flops_G:.4f}")
    print(f"📦 Params (M):   {params_M:.4f}")
    print(f"💾 Mem (MB):     {mem_M:.4f}")
    print(f"⏱️ ExecTime (s): {exec_time:.4f}")
    print("🌟" * 25 + "\n")


def main():
    parser = argparse.ArgumentParser(description="MCArb 复杂度与效率评测脚本")
    parser.add_argument("--model_title", type=str, default="ERCSR", choices=['MCnet', 'SSPSR', 'ERCSR'],
                        help="要评测的模型")
    parser.add_argument("--dataset_name", type=str, default="Pavia", help="数据集名称 (用于确定通道数)")
    parser.add_argument("--upmode", type=str, default="Meta_upsample", help="上采样模块类型")
    parser.add_argument("--experts", type=int, default=4, help="专家数量")
    parser.add_argument("--scale", type=int, default=4, choices=[2, 4, 8], help="测试的缩放倍率 (4或8)")
    parser.add_argument("--spatial_size", type=int, default=64, help="测试输入的空间大小 (默认 64x64)")
    parser.add_argument("--cuda", type=str, default="0", help="使用的 GPU ID")

    args = parser.parse_args()

    # 设置设备
    os.environ['CUDA_VISIBLE_DEVICES'] = args.cuda
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if device.type == 'cpu':
        print("⚠️ 警告: 未检测到 GPU，显存测试将失效，时间测试可能不准。")

    # 获取数据集通道数 (与你 main.py 逻辑一致)
    colors_dict = {'HoustonU': 48, 'Pavia': 102, 'Chikusei': 128, 'Washington': 191, 'CAVE': 31, 'Harvard': 31}
    if args.dataset_name not in colors_dict:
        raise ValueError(f"未知数据集 {args.dataset_name}")
    colors = colors_dict[args.dataset_name]

    # 构建模型
    print(f"🛠️ 正在构建模型 {args.model_title} (Upmode: {args.upmode})...")
    model_dict = {
        'MCnet': ad_meta_MCnet,
        'SSPSR': ad_meta_SSPSR,
        'ERCSR': ad_meta_ERCSR
    }

    net = model_dict[args.model_title](
        n_colors=colors,
        upmode=args.upmode,
        experts=args.experts
    )

    # 创建虚拟输入张量 [Batch=1, Channels, Height, Width]
    # 在论文中测试 FLOPs 通常使用单张图片(B=1)，空间大小使用典型的 Patch 大小（如 64x64）
    dummy_input = torch.randn(1, colors, args.spatial_size, args.spatial_size)

    # 运行评测
    benchmark_model(net, dummy_input, args.scale, device)


if __name__ == "__main__":
    main()