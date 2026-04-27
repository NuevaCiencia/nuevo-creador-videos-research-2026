import os
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

import uvicorn

if __name__ == "__main__":
    print("\n🎬  Video Creator — http://127.0.0.1:8080\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
