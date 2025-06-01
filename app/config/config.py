# File Uploads Directory
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

def mkdirs():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
