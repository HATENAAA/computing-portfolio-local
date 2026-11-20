"""Generate explicitly synthetic reference signals for comparing with future VI exports."""
import json
from pathlib import Path
import numpy as np
from scipy import signal
from signal_check import analyze,spectrum

def generate(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    fs=1024;t=np.arange(4096)/fs
    x=np.sin(2*np.pi*50*t)+.5*np.sin(2*np.pi*200*t)
    reports=[]
    for name,sos in [('butterworth',signal.butter(4,100,fs=fs,output='sos')),('chebyshev',signal.cheby1(4,1,100,fs=fs,output='sos'))]:
        y=signal.sosfilt(sos,x)
        path=out/(name+'.csv');np.savetxt(path,np.column_stack([t,x,y]),delimiter=',',header='time_s,input,filtered',comments='')
        r=analyze(path,[50,200],1024)
        _,response=signal.freqz_sos(sos,worN=np.array([50,200]),fs=fs)
        r['mode']='synthetic-reference';r['filter']=name;r['order']=4;r['cutoff_hz']=100
        r['theoretical_gain_db']=(20*np.log10(np.abs(response))).tolist()
        r['maximum_gain_error_db']=float(max(abs(row['gain_db']-expected) for row,expected in zip(r['tones'],r['theoretical_gain_db'])))
        reports.append(r)
    # A known above-Nyquist sine aliases; this is a demonstration, not a VI measurement.
    f,a,_=spectrum(t,np.sin(2*np.pi*750*t));observed=float(f[np.argmax(a)])
    report=dict(mode='synthetic-reference',scope='SciPy reference calculations only; no physical acquisition and no LabVIEW VI executed',filters=reports,aliasing=dict(input_hz=750,sampling_hz=fs,expected_alias_hz=274,observed_peak_hz=observed))
    (out/'reference_report.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    return report
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(generate(a.out),indent=2))
