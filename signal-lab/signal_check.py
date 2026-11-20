"""Quantitative FFT checks for time-series CSV exported from a simulated instrument."""
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np

def spectrum(time, values):
    t,x=np.asarray(time,dtype=float),np.asarray(values,dtype=float)
    if t.ndim!=1 or x.shape!=t.shape or len(t)<32 or not np.isfinite(t).all() or not np.isfinite(x).all():
        raise ValueError('At least 32 finite one-dimensional time/value samples required')
    dt=np.diff(t)
    if not (dt>0).all() or not np.allclose(dt,np.median(dt),rtol=1e-4,atol=1e-12):
        raise ValueError('Timestamps must be strictly increasing and uniformly spaced in seconds')
    fs=1/np.median(dt);window=np.hanning(len(x))
    amplitude=np.abs(np.fft.rfft((x-x.mean())*window))/window.sum()
    if len(x)%2==0:amplitude[1:-1]*=2
    else:amplitude[1:]*=2
    frequency=np.fft.rfftfreq(len(x),1/fs)
    return frequency,amplitude,float(fs)

def analyze(path,tones,discard=0):
    path=Path(path)
    with path.open(encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    if not rows or 'time_s' not in rows[0] or not {'input','filtered'} <= rows[0].keys():
        raise ValueError('CSV columns must include time_s,input,filtered')
    if type(discard) is not int or discard<0:raise ValueError('discard must be a nonnegative integer')
    t=np.array([float(r['time_s']) for r in rows])[discard:]
    x=np.array([float(r['input']) for r in rows])[discard:]
    y=np.array([float(r['filtered']) for r in rows])[discard:]
    f,a,fs=spectrum(t,x);_,b,_=spectrum(t,y)
    result=[]
    for tone in tones:
        if not np.isfinite(tone) or not 0<tone<fs/2:raise ValueError('Requested tones must be below Nyquist')
        k=int(np.argmin(abs(f-tone)))
        gain=float(20*np.log10(b[k]/a[k])) if a[k]>1e-12 and b[k]>1e-12 else None
        result.append(dict(requested_hz=float(tone),bin_hz=float(f[k]),input_amplitude=float(a[k]),filtered_amplitude=float(b[k]),gain_db=gain))
    return dict(scope='CSV numerical analysis; does not execute or certify a LabVIEW VI',input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),samples=len(t),sampling_hz=fs,nyquist_hz=fs/2,bin_width_hz=float(fs/len(t)),window='Hann, DC removed, coherent gain corrected',discarded_samples=discard,tones=result)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('csv',type=Path);p.add_argument('--tones',type=float,nargs='+',required=True);p.add_argument('--discard',type=int,default=0);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    report=analyze(a.csv,a.tones,a.discard);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2,allow_nan=False));print(a.out)
if __name__=='__main__':main()
