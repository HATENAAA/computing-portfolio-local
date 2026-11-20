"""Run the existing project tests against installed local dependencies."""
import argparse,sys,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from manage import command
PROJECTS={'firewatch':'firewatch','hsi':'hsi-sr-lab','signal':'signal-lab','bathymetry':'bathymetry-lab'}
p=argparse.ArgumentParser();p.add_argument('project',choices=['all','vrfitai','manufacturing',*PROJECTS],default='all',nargs='?');a=p.parse_args()
command('java') if a.project in ['all','manufacturing'] else None
for name in (['vrfitai','manufacturing',*PROJECTS] if a.project=='all' else [a.project]):
 if name=='vrfitai':args=[shutil.which('npm') or 'npm','test'];cwd=ROOT/'vrfitai'
 elif name=='manufacturing':args=[command('mvn'),'-Dnet.bytebuddy.experimental=true','test'];cwd=ROOT/'manufacturing-platform/backend'
 else:
  cwd=ROOT/PROJECTS[name];py=cwd/'.venv'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python');args=[str(py),'-m','unittest','discover','-s','tests','-v']
 print('\n验证 '+name,flush=True);subprocess.run(args,cwd=cwd,check=True)
 if name=='manufacturing':subprocess.run([shutil.which('npm') or 'npm','test'],cwd=ROOT/'manufacturing-platform/frontend',check=True)
