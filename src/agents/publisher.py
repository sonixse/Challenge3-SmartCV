"""Publisher agent. Persists pipeline results to SQLite and returns a summary dict.

This is the final node in the graph. It writes one row to the `runs` table
and returns a lightweight summary so callers can confirm what was saved.
"""

from src.db.sqlite import save_run, DEFAULT_DB_PATH


def publish(
    candidate_name:    str,
    candidate_contact: str | None,
    pdf_path:          str,
    model:             str,
    podium_result:     dict,
    visionary_result:  dict,
    db_path:           str = DEFAULT_DB_PATH,
) -> dict:
    """Persist the pipeline run and return a summary.

    Returns:
        {
          "run_id":        int,       # Auto-incremented DB row id
          "candidate":     str,
          "best_fit_role": str,
          "best_fit_score": int,
          "offers_ranked": int,       # Total offers in the podium ranking
          "top_gaps":      list[str],
          "db_path":       str,
        }
    """
    run_id = save_run(
        candidate_name=candidate_name,
        candidate_contact=candidate_contact,
        pdf_path=pdf_path,
        model=model,
        podium_result=podium_result,
        visionary_result=visionary_result,
        db_path=db_path,
    )

    ranking   = podium_result.get("ranking", [])
    top_gaps  = [g["skill"] for g in visionary_result.get("top_gaps", [])]

    return {
        "run_id":         run_id,
        "candidate":      candidate_name,
        "best_fit_role":  visionary_result.get("best_fit_role", "Unknown"),
        "best_fit_score": visionary_result.get("best_fit_score", 0),
        "offers_ranked":  len(ranking),
        "top_gaps":       top_gaps,
        "db_path":        db_path,
    }
