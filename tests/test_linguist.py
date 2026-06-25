import numpy as np
import pytest
from sentence_transformers import SentenceTransformer
from src.config import LINGUIST_MATCH_THRESHOLD as MATCH, LINGUIST_GREY_THRESHOLD as GREY


@pytest.fixture(scope="session")
def model():
    return SentenceTransformer("intfloat/multilingual-e5-base")


def embed(model, text):
    return model.encode(f"query: {text}", normalize_embeddings=True)


def similarity(model, a, b):
    return float(np.dot(embed(model, a), embed(model, b)))


# --- MATCH ---

@pytest.mark.parametrize("a,b", [
    ("Python", "Python"),
    ("SQL", "PostgreSQL"),
    ("Gestió de projectes", "Project Management"),
    ("Machine Learning", "Machine Learning"),
])
def test_match_pairs(model, a, b):
    assert similarity(model, a, b) >= MATCH, f'"{a}" ↔ "{b}" hauria ser MATCH (>= {MATCH})'


# --- GREY ZONE ---
# Inclou equivalents cross-lingual exactes que el model posa just per sota del MATCH threshold
# (el Detective els resol correctament a MATCH en llegir el CV)

@pytest.mark.parametrize("a,b", [
    ("Python", "PyTorch"),
    ("Machine Learning", "Estadística"),
    ("Machine Learning", "Aprenentatge automàtic"),
    ("Anàlisi de dades", "Data Analysis"),
])
def test_grey_zone_pairs(model, a, b):
    score = similarity(model, a, b)
    assert GREY <= score < MATCH, f'"{a}" ↔ "{b}" hauria ser GREY ZONE ({GREY}–{MATCH}), score={score:.4f}'


# --- NO MATCH ---

@pytest.mark.parametrize("a,b", [
    ("Python", "Marketing"),
    ("Machine Learning", "Disseny gràfic"),
    ("SQL", "Vendes"),
    ("Deep Learning", "Comptabilitat"),
])
def test_no_match_pairs(model, a, b):
    assert similarity(model, a, b) < GREY, f'"{a}" ↔ "{b}" hauria ser NO MATCH (< {GREY})'
