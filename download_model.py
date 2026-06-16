import os
import requests

MODEL_DIR = "local_model/all-MiniLM-L6-v2"
MODEL_FILE = os.path.join(MODEL_DIR, "model.safetensors")
MODEL_URL = https://github.com/abionasinmisola-jpg/aqg-system/releases/download/v1.0/model.safetensors

os.makedirs(MODEL_DIR, exist_ok=True)

if not os.path.exists(MODEL_FILE) or os.path.getsize(MODEL_FILE) < 1000:
    print("Downloading model.safetensors...")
    r = requests.get(MODEL_URL, stream=True)
    r.raise_for_status()
    with open(MODEL_FILE, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Model downloaded successfully")
else:
    print("Model already present")