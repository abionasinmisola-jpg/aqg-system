import os
os.environ["HF_HOME"] = "/app/.cache/huggingface"

from sentence_transformers import SentenceTransformer
SentenceTransformer('all-MiniLM-L6-v2')
print('Model downloaded successfully')