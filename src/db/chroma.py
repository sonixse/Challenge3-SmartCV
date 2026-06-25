import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from sentence_transformers import SentenceTransformer

E5_MODEL_NAME = "intfloat/multilingual-e5-base"

# E5 loaded once and shared by ef (indexing) and linguist (querying)
model = SentenceTransformer(E5_MODEL_NAME)


class _E5EmbeddingFunction(EmbeddingFunction):
    def name(self) -> str:
        return "sentence_transformer"

    def __call__(self, input: Documents) -> Embeddings:
        passages = [f"passage: {doc}" for doc in input]
        return model.encode(passages, normalize_embeddings=True).tolist()


client = chromadb.PersistentClient(path="data/chroma")
ef = _E5EmbeddingFunction()
