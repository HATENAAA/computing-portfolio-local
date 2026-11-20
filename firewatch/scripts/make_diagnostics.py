"""Synthetic rule diagnostics, never a real-fire benchmark."""
import argparse
import csv
from pathlib import Path
import cv2
import numpy as np

def generate(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    rows=[]
    for j, split in enumerate(('validation','test')):
        for i,kind in enumerate(('flame_proxy','dim_proxy','black','white','orange_object','tiny_noise','blue','warm_lamp')):
            image=np.zeros((96,128,3),np.uint8)
            # Distinct backgrounds avoid exact duplicate diagnostics across splits.
            image[0,0]=[j+1,i+1,0]
            if kind in ('flame_proxy','dim_proxy'):
                color=(0,190 if kind=='flame_proxy' else 125,255)
                points=np.array([[25+j,78],[42,20+j],[54,48],[70,28],[90,78]])
                cv2.fillPoly(image,[points],color)
            elif kind=='white': image[20:80,20:100]=255
            elif kind=='orange_object': image[20:80,20:100]=(0,190,255)
            elif kind=='tiny_noise': image[40:42,40:42]=(0,190,255)
            elif kind=='blue': image[20:80,20:100]=(255,80,0)
            elif kind=='warm_lamp': cv2.circle(image,(65,48),23,(20,180,250),-1)
            name=f'{split}_{kind}.png';cv2.imwrite(str(folder/name),image)
            rows.append(dict(id=name[:-4],path=name,label=int(kind.endswith('proxy')),split=split,group=f'{split}_{kind}'))
    with (folder/'manifest.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','path','label','split','group']);w.writeheader();w.writerows(rows)
    return folder/'manifest.csv'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('runs/diagnostics'))
    print(generate(p.parse_args().out))
