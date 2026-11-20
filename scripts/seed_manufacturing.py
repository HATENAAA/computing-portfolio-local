"""Create explicit local manufacturing demo records; no existing data is cleared."""
from pathlib import Path
import runpy
if __name__=='__main__':
 runpy.run_path(str(Path(__file__).resolve().parents[1]/'manufacturing-platform/scripts/seed_demo.py'),run_name='__main__')
