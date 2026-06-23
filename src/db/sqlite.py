""" Base de dades SQLite on es guarden 
els resultats de les execucions del pipeline SmartCV."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = "data/smartcv.db"


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:

    """Creació de taules si no existeixen. 
    S'executa cada cop que arranca la aplicació.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name    TEXT    NOT NULL,
                candidate_contact TEXT,
                pdf_path          TEXT,
                model             TEXT,
                best_fit_role     TEXT,
                best_fit_score    INTEGER,
                coaching          TEXT,
                top_gaps_json     TEXT,
                strengths_json    TEXT,
                ranking_json      TEXT,
                created_at        TEXT    NOT NULL
            )
        """)
        conn.commit()


def save_run(
    candidate_name:    str,
    candidate_contact: str | None,
    pdf_path:          str,
    model:             str,
    podium_result:     dict,
    visionary_result:  dict,
    db_path:           str = DEFAULT_DB_PATH,
) -> int:
    
    """ Afegir una execució de pipeline. 
    Retorna el nou id de la execució."""

    init_db(db_path)

    ranking  = podium_result.get("ranking", [])
    best     = ranking[0] if ranking else {}

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO runs (
                candidate_name, candidate_contact, pdf_path, model,
                best_fit_role, best_fit_score,
                coaching, top_gaps_json, strengths_json, ranking_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_name,
                candidate_contact,
                pdf_path,
                model,
                visionary_result.get("best_fit_role", best.get("role")),
                visionary_result.get("best_fit_score", best.get("score_match", 0)),
                visionary_result.get("coaching"),
                json.dumps(visionary_result.get("top_gaps", []),    ensure_ascii=False),
                json.dumps(visionary_result.get("strengths", []),   ensure_ascii=False),
                json.dumps(ranking,                                  ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid
