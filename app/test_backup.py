import os
import shutil
from datetime import datetime

ASSETS_DIR = "/Users/javier/Documents/DEVELOPER/nuevo-creador-videos-research-2026/app/assets"

def backup_and_clear_assets(class_id: int):
    base_path = os.path.join(ASSETS_DIR, str(class_id))
    if not os.path.exists(base_path):
        print("Base path does not exist")
        return
    
    has_files = False
    for folder in ["images", "videos"]:
        folder_path = os.path.join(base_path, folder)
        if os.path.exists(folder_path) and os.listdir(folder_path):
            has_files = True
            break
            
    if not has_files:
        print("No files to backup")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(base_path, "backups")
    backup_dir = os.path.join(backup_root, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"Backing up to {backup_dir}")
    
    for folder in ["images", "videos"]:
        src = os.path.join(base_path, folder)
        if os.path.exists(src) and os.listdir(src):
            dst = os.path.join(backup_dir, folder)
            print(f"Moving {src} to {dst}")
            shutil.move(src, dst)
            os.makedirs(src, exist_ok=True)

# Test
test_id = 999
test_path = os.path.join(ASSETS_DIR, str(test_id))
os.makedirs(os.path.join(test_path, "images"), exist_ok=True)
with open(os.path.join(test_path, "images", "test.txt"), "w") as f:
    f.write("test")

backup_and_clear_assets(test_id)
print("Done")
