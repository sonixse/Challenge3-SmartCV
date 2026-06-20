import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# run with `python scripts/index_vacancies.py` from root project folder

from src.data.load_vacancies import load
import chromadb
from chromadb.utils import embedding_functions

# load vacancies
_, vacancies = load()

# set up chroma and BGE embeddings (text embedding pretrained model)

client = chromadb.PersistentClient(path="data/chroma")
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5" # for prod use "BAAI/bge-base-en-v1.5"
)

collection = client.get_or_create_collection(
    name="vacancies", 
    embedding_function=ef
)

if collection.count() == len(vacancies):
    print(f"Collection already has {collection.count()} vacancies, skip indexing.")
    exit(0)

# index each vacancy: build a text to embed, plus metadata

for i, vac in enumerate(vacancies):

    # Natural language text to embed
    skill_text = ", ".join(f"{s.name} ({s.purpose})" for s in vac.skills)
    tool_text = ", ".join(f"{t.name} ({t.purpose})" for t in vac.tools)

    text = (
        f"{vac.job_title} in the {vac.sector} sector. "
        f"Requires {vac.years_experience} years of experience. "
        f"Minimum degree: {vac.highest_degree}. "
        f"Skills: {skill_text}. "
        f"Tools: {tool_text}. "
    )

    
    collection.add(
        ids=[str(i)],
        documents=[text],
        metadatas=[{
            # chroma only supports str, int and float metadata
            "job_title": vac.job_title,
            "sector":    vac.sector,
            "years_experience": vac.years_experience,
            "has_internship": int(vac.has_internship),
            "highest_degree": vac.highest_degree,
        }]
    )

print(f"Indexed {len(vacancies)} vacancies")


""" 
RELEVANT INFO 

Indexes all vacancies into ChromaDB so Alan Turing can query them at match time
(it queries this collection with a candidate's CV text)

Each vacancy is converted into a text string, BGE turns it into a meaning-vector,
and ChromaDB stores both. Ready for nearest-neighbour closest match search.
"""
