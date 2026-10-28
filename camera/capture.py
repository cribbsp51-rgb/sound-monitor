import subprocess
import shutil
import os
from datetime import datetime

IMAGE_DIR = "data/images"

def ensure_dir():
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

def capture_image(prefix="event"):
    ensure_dir()
    ts = datetime.utcnow().isoformat().replace(":", "-")
    filename = f"{prefix}_{ts}.jpg"
    path = os.path.join(IMAGE_DIR, filename)

    # Auto-detect correct camera command
    for cmd in ("rpicam-still", "libcamera-still"):
        if shutil.which(cmd):
            camera_cmd = cmd
            break
    else:
        raise RuntimeError("No camera capture command found.")

    subprocess.run([
        camera_cmd,
        "-n",
        "-o", path,
        "--width", "1920",
        "--height", "1080",
        "--autofocus-mode", "continuous"
    ], check=False)

    return path
