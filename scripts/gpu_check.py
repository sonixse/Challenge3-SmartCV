import torch
from sentence_transformers import SentenceTransformer

model_name = "intfloat/multilingual-e5-base"
model = SentenceTransformer(model_name)

print(f"CUDA disponible: {torch.cuda.is_available()}")
print(f"Device: {model.device}")
