%% MATLAB 脚本：生成高质量 LR 测试 Patch (精简版)
clc; clear; close all;

% 1. 参数设置
input_file = 'Pavia.mat'; 
save_name = 'test_patch_pavia_matlab_x4_2.mat'; % 直接保存在当前文件夹
scale = 4;
patch_size = 88; 

% 2. 加载数据
if ~exist(input_file, 'file')
    error('错误：在当前文件夹中找不到 %s，请确认文件位置。', input_file);
end

fprintf('正在加载原始数据...\n');
load(input_file); % 加载后变量名为 pavia

% 3. 预处理 (遵循原作逻辑：全局最大值归一化)
img = double(pavia);
img = img ./ max(img(:)); 
img = single(img);

% 4. 执行裁剪 (y=240, x=0 对应 MATLAB 索引 241, 1)
start_y = 250; 
start_x = 1;
hr = img(start_y : start_y + patch_size - 1, start_x : start_x + patch_size - 1, :);

% 5. 生成 LR (核心：MATLAB imresize 自动包含 Anti-aliasing 抗混叠滤波)
% 这就是消除你之前看到的“高亮噪点”、产生“奶油感”的关键
lr = imresize(hr, 1/scale, 'bicubic');

% 6. 保存结果
% 使用 -v6 格式，Python 的 scipy.io.loadmat 兼容性最好且读取速度最快
save(save_name, 'hr', 'lr', '-v6');

fprintf('✅ 处理完成！\n');
fprintf('   - 生成文件: %s\n', save_name);
fprintf('   - HR 尺寸: [%d x %d x %d]\n', size(hr,1), size(hr,2), size(hr,3));
fprintf('   - LR 尺寸: [%d x %d x %d]\n', size(lr,1), size(lr,2), size(lr,3));