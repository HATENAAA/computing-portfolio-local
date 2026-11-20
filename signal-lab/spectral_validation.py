"""Power conservation and jointly fitted, declared stationary tones."""
import numpy as np
from scipy import signal
from signal_check import spectrum

def power_check(time, values):
    _, _, fs = spectrum(time, values)
    x = np.asarray(values, dtype=float)
    window = signal.windows.hann(len(x), sym=False)
    f, psd = signal.periodogram(x, fs=fs, window=window, detrend='constant', scaling='density')
    integrated = float(psd.sum() * (f[1] - f[0]))
    reference = float(np.sum(((x-x.mean()) * window)**2) / np.sum(window**2))
    return dict(integrated_psd=integrated, window_weighted_mean_square=reference,
                absolute_error=abs(integrated-reference),
                relative_error=abs(integrated-reference)/reference if reference else None,
                equivalent_noise_bandwidth_hz=float(fs*np.sum(window**2)/window.sum()**2),
                coherent_gain=float(window.mean()), units='input-unit squared',
                definition='One-sided PSD sum times bin width equals the window-weighted, demeaned mean square.')

def fit_tones(time, input_values, output_values, tones):
    _, _, fs = spectrum(time, input_values)
    spectrum(time, output_values)
    tones = sorted(set(tones))
    if not tones or len(tones)>8 or any(not np.isfinite(f) or not 0<f<fs/2 for f in tones):
        raise ValueError('Declare 1..8 finite tones strictly below Nyquist')
    t = np.asarray(time, dtype=float); t = t-t[0]
    columns = [np.ones(len(t))]
    for f in tones: columns.extend([np.sin(2*np.pi*f*t), np.cos(2*np.pi*f*t)])
    design = np.column_stack(columns)
    condition = float(np.linalg.cond(design))
    if not np.isfinite(condition) or condition>1e8:
        raise ValueError('Declared tones are not numerically identifiable in this time window')
    xy = np.column_stack([input_values,output_values])
    coefficients, _, rank, _ = np.linalg.lstsq(design, xy, rcond=None)
    if rank < design.shape[1]:raise ValueError('Tone design is rank deficient')
    residual = np.sqrt(np.mean((xy-design@coefficients)**2,axis=0))
    amplitudes = np.hypot(coefficients[1::2],coefficients[2::2])
    floor = max(float(amplitudes[:,0].max())*1e-6, 1e-12)
    rows=[]
    for k,f in enumerate(tones):
        a,b=map(float,amplitudes[k]);phase=np.arctan2(coefficients[2+2*k],coefficients[1+2*k])
        phase_difference=float(np.angle(np.exp(1j*(phase[1]-phase[0])))*180/np.pi)
        measurable=a>floor and b>1e-12
        rows.append(dict(frequency_hz=float(f),input_amplitude=a,output_amplitude=b,
                         gain_db=float(20*np.log10(b/a)) if measurable else None,
                         phase_difference_deg=phase_difference if measurable else None))
    return dict(tones=rows, residual_rms_input=float(residual[0]),residual_rms_output=float(residual[1]),
                design_condition=condition,scope='Joint sine/cosine plus DC least-squares fit at declared frequencies; assumes stationary tones, not an automatic frequency estimator.')
