import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.native_detector import build
if __name__=='__main__':print(build()[0])
