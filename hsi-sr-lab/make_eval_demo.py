"""Create deterministic synthetic arrays to smoke-test the evaluator, not a model benchmark."""
import argparse,json
from pathlib import Path
import numpy as np
def generate(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    rng=np.random.default_rng(20261101);samples=[];predictions=[[],[]]
    for i,split in enumerate(['train','val','test','test']):
        x=rng.uniform(.1,.9,(16,16,6));np.save(out/f'truth-{i}.npy',x)
        samples.append(dict(id=f'patch-{i}',scene='synthetic-scene',split=split,window=[i*32,0,16,16],truth=f'truth-{i}.npy'))
        if split=='test':
            noise=rng.normal(0,1,x.shape)
            for j,sigma in enumerate([.02,.01]):
                name=f'noise-{j}-{i}.npy';np.save(out/name,x+sigma*noise)
                predictions[j].append(dict(sample_id=f'patch-{i}',path=name))
    spec=dict(mode='synthetic',experiment_id='evaluator-smoke-only',data_range=1,samples=samples,runs=[dict(id=f'synthetic-noise-{sigma}',scale=4,predictions=predictions[j]) for j,sigma in enumerate([.02,.01])])
    (out/'manifest.json').write_text(json.dumps(spec,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args();generate(a.out)
