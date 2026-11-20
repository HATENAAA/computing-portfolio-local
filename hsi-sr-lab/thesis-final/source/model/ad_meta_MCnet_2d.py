import torch
import torch.nn as nn
from meta_sr import Adapt_3d_2,Meta_upsample,Meta_upsample_3d_3
class BasicConv3d(nn.Module):
    def __init__(self, wn, in_channel, out_channel, kernel_size, stride, padding=(0,0,0)):
        super(BasicConv3d, self).__init__()
        self.conv = wn(nn.Conv3d(in_channel, out_channel,
                              kernel_size=kernel_size, stride=stride,
                              padding=padding))
        self.relu = nn.ReLU()

    def forward(self, x):
  
        x = self.conv(x)
        x = self.relu(x)
        return x

class S3Dblock(nn.Module):
    def __init__(self, wn, n_feats):
        super(S3Dblock, self).__init__()

        self.conv = nn.Sequential(
            BasicConv3d(wn, n_feats, n_feats, kernel_size=(1,3,3), stride=1, padding=(0,1,1)),
            BasicConv3d(wn, n_feats, n_feats, kernel_size=(3,1,1), stride=1, padding=(1,0,0))
        )            
       
    def forward(self, x): 
    	   	
        return self.conv(x)

def _to_4d_tensor(x, depth_stride=None):
    """Converts a 5d tensor to 4d by stackin
    the batch and depth dimensions."""
    x = x.transpose(0, 2)  # swap batch and depth dimensions: NxCxDxHxW => DxCxNxHxW
    if depth_stride:
        x = x[::depth_stride]  # downsample feature maps along depth dimension
    depth = x.size()[0]
    x = x.permute(2, 0, 1, 3, 4)  # DxCxNxHxW => NxDxCxHxW
    x = torch.split(x, 1, dim=0)  # split along batch dimension: NxDxCxHxW => N*[1xDxCxHxW]
    x = torch.cat(x, 1)  # concatenate along depth dimension: N*[1xDxCxHxW] => 1x(N*D)xCxHxW
    x = x.squeeze(0)  # 1x(N*D)xCxHxW => (N*D)xCxHxW
    return x, depth


def _to_5d_tensor(x, depth):
    """Converts a 4d tensor back to 5d by splitting
    the batch dimension to restore the depth dimension."""
    x = torch.split(x, depth)  # (N*D)xCxHxW => N*[DxCxHxW]
    x = torch.stack(x, dim=0)  # re-instate the batch dimension: NxDxCxHxW
    x = x.transpose(1, 2)  # swap back depth and channel dimensions: NxDxCxHxW => NxCxDxHxW
    return x
    
    
class Block(nn.Module):
    def __init__(self, wn, n_feats, n_conv):
        super(Block, self).__init__()

        self.relu = nn.ReLU()
        
        Block1 = []  
        for i in range(n_conv):
            Block1.append(S3Dblock(wn, n_feats)) 
        self.Block1 = nn.Sequential(*Block1)         

        Block2 = []  
        for i in range(n_conv):
            Block2.append(S3Dblock(wn, n_feats)) 
        self.Block2 = nn.Sequential(*Block2) 
        
        Block3 = []  
        for i in range(n_conv):
            Block3.append(S3Dblock(wn, n_feats)) 
        self.Block3 = nn.Sequential(*Block3) 
        
        self.reduceF = BasicConv3d(wn, n_feats*3, n_feats, kernel_size=1, stride=1)                                                            
        self.Conv = S3Dblock(wn, n_feats)
        self.gamma = nn.Parameter(torch.ones(3))   
         
        conv1 = []   
        conv1.append(wn(nn.Conv2d(n_feats, n_feats, kernel_size=(3,3),  stride=1, padding=(1,1)))) 
        conv1.append(self.relu)
        conv1.append(wn(nn.Conv2d(n_feats, n_feats, kernel_size=(3,3),  stride=1, padding=(1,1))))         
        self.conv1 = nn.Sequential(*conv1)           

        conv2 = []   
        conv2.append(wn(nn.Conv2d(n_feats, n_feats, kernel_size=(3,3),  stride=1, padding=(1,1)))) 
        conv2.append(self.relu)
        conv2.append(wn(nn.Conv2d(n_feats, n_feats, kernel_size=(3,3),  stride=1, padding=(1,1))))         
        self.conv2 = nn.Sequential(*conv2)  
        
        conv3 = []   
        conv3.append(wn(nn.Conv2d(n_feats, n_feats, kernel_size=(3,3),  stride=1, padding=(1,1)))) 
        conv3.append(self.relu)
        conv3.append(wn(nn.Conv2d(n_feats, n_feats, kernel_size=(3,3),  stride=1, padding=(1,1))))         
        self.conv3 = nn.Sequential(*conv3)          
        self.SA_adapt = Adapt_3d_2(n_feats)
        
                                                          
    def forward(self, x, n_scale): 
        
        res = x
        x1 = self.Block1(x) + x 
        x2 = self.Block2(x1) + x1         
        x3 = self.Block3(x2) + x2     

        x1, depth = _to_4d_tensor(x1, depth_stride=1)  
        x1 = self.conv1(x1)       
        x1 = _to_5d_tensor(x1, depth)  
                             
        x2, depth = _to_4d_tensor(x2, depth_stride=1)  
        x2 = self.conv2(x2)       
        x2 = _to_5d_tensor(x2, depth)         
   
                     
        x3, depth = _to_4d_tensor(x3, depth_stride=1)  
        x3 = self.conv3(x3)       
        x3 = _to_5d_tensor(x3, depth)  
                
        x = torch.cat([self.gamma[0]*x1, self.gamma[1]*x2, self.gamma[2]*x3], 1)                 
        x = self.reduceF(x) 
        x = self.relu(x)
        x = x + res        
        
        
        x = self.Conv(x)
        x = self.SA_adapt(x, n_scale)      
                                                                                                     
        return x  
                                                                                                                        
                        
class ad_meta_MCnet(nn.Module):
    def __init__(self, n_colors=128,n_feats=64,n_conv=1,upmode = 'Meta_upsample', experts = 4):
        super().__init__()
        
        kernel_size = 3
       
        wn = lambda x: torch.nn.utils.weight_norm(x)
                                            
        self.head = wn(nn.Conv3d(1, n_feats, kernel_size, padding=kernel_size//2))        
               
        self.SSRM1 = Block(wn, n_feats, n_conv)              
        self.SSRM2 = Block(wn, n_feats, n_conv) 
        self.SSRM3 = Block(wn, n_feats, n_conv)           
        self.SSRM4 = Block(wn, n_feats, n_conv)  
                                                
        tail = []          
        tail.append(wn(nn.Conv3d(n_feats, 1, kernel_size, padding=kernel_size//2)))          
        self.tail = nn.Sequential(*tail)
        # self.up = { 'Meta_upsample':Meta_upsample,
        #             'Meta_upsample_3d_3':Meta_upsample_3d_3,\
        #             }[upmode](channels=n_colors, num_experts=experts)
        self.upmode_str = upmode  # 新增：保存 upmode 字符串用于 forward 判断
        if upmode == 'Meta_upsample':
            # 2D 版本在 forward 中会把光谱维 D 叠到 Batch 上，
            # 所以这里的输入通道应该是 n_feats (64) 而不是 n_colors
            self.up = Meta_upsample(channels=n_feats, num_experts=experts)
        else:
            self.up = Meta_upsample_3d_3(channels=n_colors, num_experts=experts)
               
    def forward(self, x, n_scale):
    	
        
        x = x.unsqueeze(1)
        T = self.head(x) 
        
        x = self.SSRM1(T, n_scale)
        x = torch.add(x, T) 
        feo = x 

        x = self.SSRM2(x, n_scale)
        x = torch.add(x, T)   
        feo = torch.cat((feo,x)) 

        x = self.SSRM3(x, n_scale)
        x = torch.add(x, T)  
        feo = torch.cat((feo,x))                              

        x = self.SSRM4(x, n_scale)
        x = torch.add(x, T) 
        feo = torch.cat((feo,x))
        
        # x = self.up(x, n_scale)
        # --- 修改后的部分 ---
        if self.upmode_str == 'Meta_upsample':
            # 1. 5D [B, C, D, H, W] -> 4D [B*D, C, H, W]
            x, depth = _to_4d_tensor(x)

            # 2. 缓解显存爆炸：分块送入 Meta_upsample (时间换空间)
            chunk_size = 16  # 每次只处理 16 个切片。如果依然 OOM，可以改成 8 或 4
            out_chunks = []

            # 将 B*D 大小的 Batch 拆分成多个小 chunk 依次处理
            for i in range(0, x.size(0), chunk_size):
                chunk = x[i: i + chunk_size]
                out_chunk = self.up(chunk, n_scale)
                out_chunks.append(out_chunk)

            # 将处理完的块重新拼接
            x = torch.cat(out_chunks, dim=0)

            # 3. 4D -> 5D 回去，以便让 3D 的 self.tail 能够处理
            x = _to_5d_tensor(x, depth)
        else:
            # 原有的 3D 流程
            x = self.up(x, n_scale)

        x = self.tail(x)
        x = x.squeeze(1)
        # x = self.tail(x)
        # x = x.squeeze(1)
        return x,feo.reshape(feo.shape[0]*feo.shape[1], feo.shape[2],feo.shape[3],feo.shape[4])