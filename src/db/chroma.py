import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from sentence_transformers import SentenceTransformer

BGE_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# BGE loaded once and shared by ef (indexing) and linguist (querying)
model = SentenceTransformer(BGE_MODEL_NAME)


class _BGEEmbeddingFunction(EmbeddingFunction):
    def name(self) -> str:
        return "sentence_transformer"  # matches persisted collection config

    def __call__(self, input: Documents) -> Embeddings:
        return model.encode(list(input), normalize_embeddings=True).tolist()


client = chromadb.PersistentClient(path="data/chroma")
ef = _BGEEmbeddingFunction()
