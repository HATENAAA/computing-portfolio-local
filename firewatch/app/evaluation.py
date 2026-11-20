"""Held-out, single-target box evaluation. AP50 uses the all-point precision envelope.
No model training, VOC difficult labels, COCO area ranges or IoU averaging are implied.
"""
from pathlib import PurePosixPath,Path
import io,json,zipfile,hashlib,math,time
import numpy as np

def iou(a,b):
    x=max(a['x'],b['x']); y=max(a['y'],b['y'])
    w=max(0,min(a['x']+a['width'],b['x']+b['width'])-x)
    h=max(0,min(a['y']+a['height'],b['y']+b['height'])-y)
    overlap=w*h;return overlap/(a['width']*a['height']+b['width']*b['height']-overlap) if overlap else 0.

def metrics(samples,threshold=0.0,match_iou=.5):
    truths={s['id']:s['truth'] for s in samples}; used={s['id']:set() for s in samples}
    count=sum(len(t) for t in truths.values()); ranked=[]
    for s in samples:
        for index,p in enumerate(s['predictions']):
            if p['confidence']>=threshold:ranked.append((p['confidence'],s['id'],index,p))
    ranked.sort(key=lambda r:(-r[0],r[1],r[2])) # deterministic tie order
    tp=fp=0;precision=[];recall=[];errors=[]
    for score,sid,index,p in ranked:
        scores=[iou(p,t) for t in truths[sid]]
        # Standard confidence-greedy matching to the highest-IoU annotation.
        best=max(range(len(scores)),key=lambda n:scores[n]) if scores else None
        if best is not None and scores[best]>=match_iou and best not in used[sid]:
            used[sid].add(best);tp+=1
        else:
            fp+=1
            kind='duplicate' if best is not None and scores[best]>=match_iou else ('localization' if scores and max(scores)>=.1 else 'background')
            errors.append(dict(image=sid,type=kind,confidence=score,box=p,best_iou=round(max(scores,default=0),5)))
        precision.append(tp/(tp+fp));recall.append(tp/count if count else 0)
    for sid,boxes in truths.items():
        for n,b in enumerate(boxes):
            if n not in used[sid]:errors.append(dict(image=sid,type='missed',box=b))
    # All-point interpolated AP, not 11-point VOC07 AP or COCO mAP.
    mrec=[0.]+recall+[1.];mpre=[0.]+precision+[0.]
    for n in range(len(mpre)-2,-1,-1):mpre[n]=max(mpre[n],mpre[n+1])
    ap=sum((mrec[n]-mrec[n-1])*mpre[n] for n in range(1,len(mrec)) if mrec[n]!=mrec[n-1]) if count else None
    p=tp/(tp+fp) if tp+fp else 0.; rr=tp/count if count else 0.
    return dict(tp=tp,fp=fp,fn=count-tp,precision=p,recall=rr,f1=2*p*rr/(p+rr) if p+rr else 0.,ap50=ap,ground_truths=count,predictions=len(ranked),curve=[dict(precision=p,recall=r) for p,r in zip(precision,recall)],errors=errors)

def read_dataset(raw,decode):
    if len(raw)>20*1024*1024:raise ValueError('ZIP 不能超过 20 MB')
    try:archive=zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as e:raise ValueError('无效 ZIP') from e
    with archive:
        entries=archive.infolist();names=[e.filename for e in entries]
        if len(entries)>65 or len(names)!=len(set(names)):raise ValueError('ZIP 文件过多或名称重复')
        if any(e.flag_bits&1 or e.file_size>10*1024*1024 or e.is_dir() or PurePosixPath(e.filename).is_absolute() or '..' in PurePosixPath(e.filename).parts or '\\' in e.filename for e in entries):raise ValueError('ZIP 包含不支持的文件或路径')
        if sum(e.file_size for e in entries)>64*1024*1024:raise ValueError('ZIP 解压总量不能超过 64 MB')
        if 'manifest.json' not in names or archive.getinfo('manifest.json').file_size>1024*1024:raise ValueError('缺少根目录 manifest.json，或清单过大')
        try:m=json.loads(archive.read('manifest.json'),parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Non-finite JSON')))
        except (ValueError,UnicodeError) as e:raise ValueError('清单 JSON 无效') from e
        if not isinstance(m,dict) or set(m)!={'version','target_class','images'} or (type(m['version']) is not int or m['version']!=1) or type(m['target_class']) is not int or not 0<=m['target_class']<100:raise ValueError('清单须为 version=1，含 target_class 和 images')
        images=m['images'];seen=set();groups={};hashes={};samples=[];referenced={'manifest.json'}
        if not isinstance(images,list) or not 2<=len(images)<=60:raise ValueError('需要 2 至 60 张图像，覆盖验证集与测试集')
        for s in images:
            if not isinstance(s,dict) or set(s)!={'id','file','group','split','boxes'}:raise ValueError('图像条目字段无效')
            if any(not isinstance(s[k],str) or not 1<=len(s[k])<=150 for k in ('id','file','group')) or s['id'] in seen:raise ValueError('图像 ID、文件名或来源分组无效')
            seen.add(s['id']);split=s['split']
            if split not in ('validation','test'):raise ValueError('split 只支持 validation / test')
            if s['group'] in groups and groups[s['group']]!=split:raise ValueError('同一来源分组不能跨验证集和测试集')
            groups[s['group']]=split
            if s['file']=='manifest.json' or s['file'] not in names or s['file'] in referenced:raise ValueError('图片文件缺失或重复引用')
            referenced.add(s['file']);payload=archive.read(s['file']);image=decode(payload);h,w=image.shape[:2]
            pixel=hashlib.sha256(str(image.shape).encode()+image.tobytes()).hexdigest()
            if pixel in hashes and hashes[pixel]!=split:raise ValueError('验证集与测试集包含相同解码图像，存在数据泄漏')
            hashes[pixel]=split
            boxes=s['boxes'];truth=[]
            if not isinstance(boxes,list) or len(boxes)>50:raise ValueError('每图最多 50 个标注框')
            for b in boxes:
                if not isinstance(b,list) or len(b)!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in b):raise ValueError('标注框格式为 [x,y,width,height]，单位为像素')
                x,y,bw,bh=b
                if min(x,y)<0 or min(bw,bh)<=0 or x+bw>w or y+bh>h:raise ValueError('标注框超出图像边界')
                truth.append(dict(x=x,y=y,width=bw,height=bh,class_id=m['target_class']))
            samples.append(dict(id=s['id'],file=s['file'],group=s['group'],split=split,truth=truth,raw=payload,source_sha256=hashlib.sha256(payload).hexdigest(),pixel_sha256=pixel,width=w,height=h))
        if referenced!=set(names):raise ValueError('ZIP 只应包含清单与引用的图像')
        for split in ('validation','test'):
            subset=[s for s in samples if s['split']==split]
            if not subset or not any(s['truth'] for s in subset):raise ValueError('验证集与测试集均需至少一张含目标标注的图像')
        return m,samples

def evaluate_archive(raw,model,decode):
    started=time.perf_counter();manifest,samples=read_dataset(raw,decode);target=manifest['target_class']
    if target not in model.contract['target_classes']:raise ValueError('清单目标类别不在模型 target_classes 中')
    times=[];provenance=None
    for s in samples:
        result,_=model.analyze(decode(s.pop('raw')),confidence=.01,iou=.45);provenance=result;times.append(result['elapsed_ms'])
        s['predictions']=[b for b in result['boxes'] if b['class_id']==target]
    validation=[s for s in samples if s['split']=='validation'];test=[s for s in samples if s['split']=='test']
    grid=[round(n/10,1) for n in range(1,10)];sweep=[]
    for t in grid:
        value=metrics(validation,t);sweep.append(dict(threshold=t,**{k:value[k] for k in ('tp','fp','fn','precision','recall','f1')}))
    best=max(sweep,key=lambda x:(x['f1'],x['threshold'])) # ties favor fewer false positives
    report=dict(version=1,protocol='single-target-ap50-all-points-v1',target_class=target,target_label=model.contract['class_names'][target],
      dataset_sha256=hashlib.sha256(raw).hexdigest(),evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      model={k:provenance[k] for k in ('model_sha256','adapter_sha256','runtime','input_size','output_layout')},
      parameters=dict(match_iou=.5,inference_floor=.01,nms_iou=.45,max_detections_per_image=300,threshold_grid=grid),
      selected_threshold=best['threshold'],validation_sweep=sweep,
      validation=dict(ap50=metrics(validation)['ap50'],operating=metrics(validation,best['threshold'])),
      test=dict(ap50=metrics(test)['ap50'],curve=metrics(test)['curve'],operating=metrics(test,best['threshold'])),
      samples=samples,timing=dict(inference_median_ms=float(np.median(times)),total_seconds=round(time.perf_counter()-started,3)),
      scope='单目标类别、IoU=0.5、全点插值 AP；推理分数下限 0.01。阈值只由验证集选取并冻结到测试集；不等同于 COCO mAP，不代表已验证的真实火灾识别准确率。')
    report['test']['iou_sensitivity']={str(i):dict(iou=i,**{('ap_at_iou' if k=='ap50' else k):v for k,v in metrics(test,best['threshold'],i).items()}) for i in [.25,.5,.75]}
    return report
