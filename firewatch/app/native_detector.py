"""C++ pixel classification, components and temporal region features; Python I/O adapter."""
from pathlib import Path
import ctypes as C,hashlib,json,os,platform,shutil,subprocess,threading,time
from tempfile import TemporaryDirectory
import cv2,numpy as np
from .detector import Config
ROOT=Path(__file__).resolve().parents[1];_lock=threading.Lock();_lib=None
class Region(C.Structure):
    _fields_=[(k,C.c_int) for k in ('x','y','width','height','pixels')]+[(k,C.c_double) for k in ('motion','texture','warm_fraction')]
def build():
    source = ROOT / 'native/fire_core.cpp'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    system = platform.system()
    extension = {'Darwin': '.dylib', 'Windows': '.dll'}.get(system, '.so')
    folder = ROOT / '.native'
    folder.mkdir(exist_ok=True)
    target = folder / f'fire-{platform.machine()}-{digest[:16]}{extension}'
    if target.is_file():
        return target, digest

    if system == 'Windows':
        compiler = shutil.which('cl.exe')
        if not compiler:
            raise RuntimeError('Use the Windows release ZIP or open the x64 Native Tools Command Prompt for Visual Studio, then retry installation.')
    else:
        compiler = shutil.which('c++') or shutil.which('clang++') or shutil.which('g++')
        if not compiler:
            raise RuntimeError('Install a C++17 compiler, then retry installation.')

    with TemporaryDirectory(prefix='fire-build-', dir=folder) as build_folder:
        temporary = Path(build_folder) / target.name
        if system == 'Windows':
            args = [compiler, '/nologo', '/std:c++17', '/EHsc', '/O2', '/MT', '/LD',
                    str(source), '/link', '/OUT:' + str(temporary)]
        else:
            args = [compiler, '-std=c++17', '-O3', '-shared', '-fPIC', str(source), '-o', str(temporary)]
        result = subprocess.run(args, cwd=build_folder, capture_output=True, text=True, errors='replace', timeout=120)
        if result.returncode:
            raise RuntimeError('C++ detector build failed:\n' + (result.stdout + result.stderr)[-2000:])
        try:
            os.replace(temporary, target)
        except PermissionError:
            if not target.is_file():
                raise
    return target, digest

def library():
    global _lib
    with _lock:
        if _lib is None:
            target,digest=build();lib=C.CDLL(str(target));lib.fw_regions.argtypes=[C.c_void_p,C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_int,C.c_void_p,C.POINTER(Region),C.c_int,C.POINTER(C.c_double)];lib.fw_regions.restype=C.c_int;_lib=(lib,digest)
        return _lib

def analyze(image,cfg=None,previous=None):
    cfg=cfg or Config()
    if image is None or image.dtype!=np.uint8 or image.ndim!=3 or image.shape[2]!=3 or image.shape[0]*image.shape[1]>12000000:raise ValueError('Expected bounded uint8 BGR image')
    started=time.perf_counter();original=image;h,w=image.shape[:2];scale=min(1,960/max(h,w));shape=(max(1,round(w*scale)),max(1,round(h*scale)))
    image=np.ascontiguousarray(cv2.resize(image,shape) if scale<1 else image)
    if previous is not None:
        if previous.shape!=original.shape:raise ValueError('Previous frame shape differs')
        previous=np.ascontiguousarray(cv2.resize(previous,shape) if scale<1 else previous)
    mask=np.zeros(image.shape[:2],np.uint8);regions=(Region*300)();scene=C.c_double();lib,digest=library()
    n=lib.fw_regions(image.ctypes.data,previous.ctypes.data if previous is not None else None,image.shape[1],image.shape[0],cfg.brightness,max(3,round(cfg.min_component*scale*scale)),mask.ctypes.data,regions,300,C.byref(scene))
    if n<0:raise RuntimeError('C++ detector rejected frame: '+str(n))
    boxes=[];minimum=max(cfg.min_component,w*h*cfg.min_area_ratio);eligible=[]
    for r in regions[:n]:
        box=dict(x=int(r.x/scale),y=int(r.y/scale),width=max(1,int(r.width/scale)),height=max(1,int(r.height/scale)),pixels=int(r.pixels/(scale*scale)),motion_ratio=r.motion,local_texture=r.texture,warm_fraction=r.warm_fraction)
        box['spatial_candidate']=box['pixels']>=minimum and r.texture>=.025
        box['detected']=bool(box['spatial_candidate'] and (previous is None or (.02<=r.motion and scene.value<.65)))
        boxes.append(box)
        if box['detected']:eligible.append(box)
    area=float(np.count_nonzero(mask)/mask.size);overlay=original.copy();full_mask=cv2.resize(mask,(w,h),interpolation=cv2.INTER_NEAREST)
    for b in boxes:
        x,y,bw,bh=[b[k] for k in ('x','y','width','height')];cv2.rectangle(overlay,(x,y),(min(w-1,x+bw-1),min(h-1,y+bh-1)),(30,110,250) if b['detected'] else (130,130,130),2)
    temporal=previous is not None
    reason='candidate' if eligible else 'no_color_region' if not boxes else 'area_below_threshold' if not any(b['spatial_candidate'] for b in boxes) else 'scene_motion' if scene.value>=.65 else 'motion_below_threshold'
    return dict(algorithm='cpp-region-motion-v1',native_sha256=digest,adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),width=w,height=h,detected=bool(eligible),boxes=boxes,area_ratio=area,reason=reason,has_previous=temporal,scene_motion_ratio=scene.value,motion_ratio=max((b['motion_ratio'] for b in boxes if b['spatial_candidate']),default=0),methods=[dict(method='LocalTexture',edge_color_ratio=max((b['local_texture'] for b in boxes),default=0),edge_pixels=int(np.count_nonzero(mask)),detected=bool(eligible))],elapsed_ms=round((time.perf_counter()-started)*1000,2),config=dict(brightness=cfg.brightness,min_area_ratio=cfg.min_area_ratio,min_component=cfg.min_component,motion_threshold=.02,scene_motion_limit=.65),note='C++ 颜色候选与局部纹理／运动筛选，非训练模型；静态图像无法验证闪烁。'),dict(original=original,mask=full_mask,overlay=overlay)
