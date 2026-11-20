"""Standalone, CPU-only metrics for HWC spectral cubes. No torch needed."""
import numpy as np
from skimage.metrics import structural_similarity

def assess(truth,pred,data_range=1.0,scale=4):
    x,y=np.asarray(truth,dtype=np.float64),np.asarray(pred,dtype=np.float64)
    if x.shape!=y.shape or x.ndim!=3 or min(x.shape)<1:raise ValueError('Expected equal nonempty HWC cubes')
    if not np.isfinite(x).all() or not np.isfinite(y).all():raise ValueError('Inputs contain NaN/Inf')
    if not np.isfinite(data_range) or data_range<=0 or not np.isfinite(scale) or scale<=0:raise ValueError('Positive data_range and scale required')
    mse=np.mean((x-y)**2,axis=(0,1));rmse=float(np.sqrt(mse.mean()))
    # Exact equality gives mathematical +inf PSNR; keep this explicit in serialised reports.
    with np.errstate(divide='ignore'):psnr=10*np.log10(data_range**2/mse)
    norm=np.linalg.norm(x,axis=2)*np.linalg.norm(y,axis=2);valid=norm>0
    angles=np.full(norm.shape,np.nan)
    angles[valid]=np.degrees(np.arccos(np.clip(np.sum(x*y,axis=2)[valid]/norm[valid],-1,1)))
    sam=float(angles[valid].mean()) if valid.any() else None
    mean=x.mean(axis=(0,1));nonzero=np.abs(mean)>1e-12
    # Undefined bands are reported, not silently dropped to make the score appear better.
    ergas=float(100/scale*np.sqrt(np.mean(mse/mean**2))) if nonzero.all() else None
    a=x.reshape(-1,x.shape[2]);b=y.reshape(-1,y.shape[2]);a=a-a.mean(axis=0);b=b-b.mean(axis=0)
    den=np.linalg.norm(a,axis=0)*np.linalg.norm(b,axis=0);corr_valid=den>1e-12
    cc=float((np.sum(a*b,axis=0)[corr_valid]/den[corr_valid]).mean()) if corr_valid.all() else None
    win=min(7,x.shape[0],x.shape[1]);win=win if win%2 else win-1
    ssim=float(np.mean([structural_similarity(x[:,:,i],y[:,:,i],data_range=data_range,win_size=win) for i in range(x.shape[2])])) if win>=3 else None
    return dict(RMSE=rmse,MPSNR=float(psnr.mean()) if np.isfinite(psnr).all() else None,
                psnr_has_infinite_band=bool(np.isinf(psnr).any()),MSSIM=ssim,SAM_deg=sam,ERGAS=ergas,CrossCorrelation=cc,
                sam_valid_pixels=int(valid.sum()),sam_total_pixels=int(valid.size),
                ergas_zero_mean_bands=int((~nonzero).sum()),constant_correlation_bands=int((~corr_valid).sum()),
                per_band_rmse=np.sqrt(mse).tolist()),angles
