// FireWatch region detector, C++17. C ABI keeps Python responsible for I/O only.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>
struct Region {int x,y,width,height,pixels;double motion,texture,warm_fraction;};
extern "C"
#if defined(_WIN32)
__declspec(dllexport)
#endif
int fw_regions(const uint8_t* bgr,const uint8_t* previous,int w,int h,int brightness,int min_pixels,uint8_t* output,Region* boxes,int capacity,double* scene_motion){
 try{
  if(!bgr||!output||!boxes||!scene_motion||w<1||h<1||int64_t(w)*h>12000000||capacity<1)return -1;
  const int n=w*h;std::vector<uint8_t> seed(n),mask(n),gray(n),old(n);double sum=0,old_sum=0;
  for(int i=0;i<n;++i){int b=bgr[3*i],g=bgr[3*i+1],r=bgr[3*i+2];gray[i]=(77*r+150*g+29*b)>>8;sum+=gray[i];if(previous){old[i]=(77*previous[3*i+2]+150*previous[3*i+1]+29*previous[3*i])>>8;old_sum+=old[i];}
   // Maximum-channel luminance retains red flames rejected by gray > 150.
   seed[i]=(r>=brightness&&r>=g+8&&g>=b+10&&r-b>=35);mask[i]=seed[i];}
  // Connect warm flame rims to adjacent yellow/white cores, without admitting an entire white page.
  for(int pass=0;pass<2;++pass){auto next=mask;for(int y=1;y<h-1;++y)for(int x=1;x<w-1;++x){int i=y*w+x;if(mask[i])continue;int b=bgr[3*i],g=bgr[3*i+1],r=bgr[3*i+2];if(r>=190&&g>=170&&b>=100&&(mask[i-1]||mask[i+1]||mask[i-w]||mask[i+w]))next[i]=1;}mask.swap(next);}
  double offset=previous?(sum-old_sum)/n:0.;int changed=0;
  std::vector<uint8_t> motion(n);if(previous)for(int i=0;i<n;++i){motion[i]=std::abs(double(gray[i])-old[i]-offset)>=18;changed+=motion[i];}
  *scene_motion=previous?double(changed)/n:0.;std::fill(output,output+n,0);
  std::vector<int> todo,component;int count=0;
  for(int start=0;start<n;++start){if(!mask[start])continue;mask[start]=0;todo.clear();component.clear();todo.push_back(start);int x0=w,y0=h,x1=0,y1=0,warm=0;
   while(!todo.empty()){int i=todo.back();todo.pop_back();component.push_back(i);int x=i%w,y=i/w;x0=std::min(x0,x);x1=std::max(x1,x);y0=std::min(y0,y);y1=std::max(y1,y);warm+=seed[i];for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx){int xx=x+dx,yy=y+dy;if(xx<0||xx>=w||yy<0||yy>=h)continue;int j=yy*w+xx;if(mask[j]){mask[j]=0;todo.push_back(j);}}}
   if(int(component.size())<min_pixels||warm<min_pixels/3)continue;
   int moving=0,inside=0,edges=0;
   // Measure motion inside the component, excluding a two-pixel boundary where rigid orange objects move.
   for(int i:component){output[i]=255;int x=i%w,y=i/w;if(x>1&&x<w-2&&y>1&&y<h-2&&seed[i]&&seed[i-2]&&seed[i+2]&&seed[i-2*w]&&seed[i+2*w]){++inside;moving+=motion[i];}if(x>0&&x<w-1&&y>0&&y<h-1&&(std::abs(int(gray[i+1])-gray[i-1])+std::abs(int(gray[i+w])-gray[i-w])>35))++edges;}
   if(count<capacity)boxes[count++]={x0,y0,x1-x0+1,y1-y0+1,int(component.size()),inside?double(moving)/inside:0.,double(edges)/component.size(),double(warm)/component.size()};
  }
  return count;
 }catch(...){return -2;}
}
