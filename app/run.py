import os
import sys

# Run from anywhere: python run.py  OR  python app/run.py
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    print("\n🎬  Video Creator — http://127.0.0.1:8080\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
