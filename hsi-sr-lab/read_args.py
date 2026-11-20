"""Read original NumPy args objects with a narrow NumPy-only pickle allowlist."""
import pickle,json,numpy as np
from pathlib import Path
class ArgsReader(pickle.Unpickler):
 def find_class(self,module,name):
  allowed={('numpy','ndarray'):np.ndarray,('numpy','dtype'):np.dtype,('numpy.core.multiarray','_reconstruct'):np._core.multiarray._reconstruct,('numpy._core.multiarray','_reconstruct'):np._core.multiarray._reconstruct}
  if (module,name) not in allowed:raise ValueError('Unapproved pickle global in args: '+module+'.'+name)
  return allowed[(module,name)]
def read(path):
 with Path(path).open('rb') as f:
  version=np.lib.format.read_magic(f)
  if version==(1,0):shape,order,dtype=np.lib.format.read_array_header_1_0(f)
  elif version==(2,0):shape,order,dtype=np.lib.format.read_array_header_2_0(f)
  else:raise ValueError('Unsupported NumPy args version')
  if shape!=() or not dtype.hasobject:raise ValueError('Expected scalar object args array')
  value=ArgsReader(f).load().item()
 if not isinstance(value,dict) or any(not isinstance(k,str) for k in value):raise ValueError('Expected argument dict')
 json.dumps(value,allow_nan=False);return value
