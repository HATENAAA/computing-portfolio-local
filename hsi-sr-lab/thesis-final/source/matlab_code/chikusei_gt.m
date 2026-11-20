%% MATLAB 脚本：生成高质量 Chikusei LR 测试 Patch
clc; clear; close all;

% 1. 参数设置
input_file = 'HyperspecVNIR_Chikusei_20140729.mat'; % 原始文件名
save_name = 'test_patch_chikusei_matlab_x4_2.mat';   % 输出文件名
scale = 4;
patch_size = 88; % 与 Pavia 保持一致，方便在可视化时对比

% 2. 加载数据
if ~exist(input_file, 'file')
    error('错误：找不到原始数据 %s。', input_file);
end

fprintf('正在加载 Chikusei 原始数据（文件较大，请稍候...）\n');
% 加载后变量名为 chikusei
load(input_file); 

% 3. 预处理
% 参照你提供的 Chikusei 生成逻辑，先进行中心裁剪（去除无效边界）
% 这样可以保证坐标系与训练/测试集一致
img = chikusei(107:2410, 144:2191, :);
clear chikusei; % 释放大内存

img = double(img);
% 全局最大值归一化（这是防止训练/测试数据范围不匹配的关键）
img = img ./ max(img(:)); 
img = single(img);

% 4. 选择可视化区域 (Patch 坐标选择)
% Chikusei 很大，这里我们选择一个地物丰富的区域
% 你可以根据需要调整 start_y 和 start_x
% 建议选择：y=500, x=500 附近通常有清晰的建筑或田块
start_y = 430; 
start_x = 300;

hr = img(start_y : start_y + patch_size - 1, start_x : start_x + patch_size - 1, :);

% 5. 生成 LR (包含抗混叠滤波的双三次插值)
% 这是生成“奶油感”低分辨图像的关键步骤
lr = imresize(hr, 1/scale, 'bicubic');

% 6. 保存结果
% 使用 -v6 格式以确保 Python 的 scipy.io.loadmat 完美兼容
save(save_name, 'hr', 'lr', '-v6');

fprintf('✅ Chikusei 处理完成！\n');
fprintf('   - 保存路径: %s\n', fullfile(pwd, save_name));
fprintf('   - HR 尺寸: [%d x %d x %d]\n', size(hr,1), size(hr,2), size(hr,3));
fprintf('   - LR 尺寸: [%d x %d x %d]\n', size(lr,1), size(lr,2), size(lr,3));