# run with `python scripts/run_interpreter.py` from root project folder (≈ 2 min)

import os
import time
import threading
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.agents.interpreter import interpret, save_profile, DEFAULT_OUTPUT_DIR, MAX_WORKERS

TOTAL = 10
INPUT_DIR = "data/raw"
OLLAMA_URL = "http://127.0.0.1:11434"


def ensure_ollama_running(timeout: int = 10) -> None: # `pkill ollama` to kill the process
    """Start ollama serve in the background if it is not already running."""
    try:
        urllib.request.urlopen(OLLAMA_URL, timeout=2)
        print("[Ollama] already running")
        return
    except Exception:
        pass

    print("[Ollama] not running — starting 'ollama serve' in background...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True, # detach from parent and survives Ctrl+C
    )

    # wait until the server is up
    for _ in range(timeout):
        time.sleep(1)
        try:
            urllib.request.urlopen(OLLAMA_URL, timeout=1)
            print("[Ollama] server ready")
            return
        except Exception:
            pass

    raise RuntimeError(f"Ollama did not start within {timeout}s. Check your installation.")


def parse_cv(i: int, print_lock: threading.Lock, total: int):
    pdf = os.path.join(INPUT_DIR, f"{i:02d}_cv.pdf")
    with print_lock:
        print(f"[{i}/{total}] Starting: {pdf}")
    cv_start = time.time()
    profile = interpret(pdf)            # raises on total failure
    cv_elapsed = time.time() - cv_start
    return i, pdf, profile, cv_elapsed


def main():
    ensure_ollama_running()
    print_lock = threading.Lock()
    start = time.time()
    ok, failed = 0, 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(parse_cv, i, print_lock, TOTAL): i
            for i in range(1, TOTAL + 1)
        }

        for future in as_completed(futures):
            try:
                i, pdf, profile, cv_elapsed = future.result()
                ok += 1
                out_path = os.path.join(DEFAULT_OUTPUT_DIR, f"{i:02d}_candidate.json")
                save_profile(profile, out_path)
                with print_lock:
                    print(f"\n  [{i}/{TOTAL}] {pdf}  ({cv_elapsed:.1f}s)  → saved: {out_path}")
                    print(f"    Name:       {profile.name}")
                    print(f"    Location:   {profile.location or 'N/A'}")
                    print(f"    Contact:    {profile.contact or 'N/A'}")
                    print(f"    Skills:     {[s.name for s in profile.skills]}")
                    print(f"    Experience: {profile.years_experience} years")
                    print(f"    Education:  {profile.education_level} in {profile.education_field}")
                    print(f"    Languages:  {[(l.language, l.level) for l in profile.languages]}")
                    # Useful for posterior grey-zone skills detection
                    print(f"    Raw Text Length: {len(profile.raw_text)} chars")

            except Exception as e:
                failed += 1
                i = futures[future]
                with print_lock:
                    print(f"\n  [{i}/{TOTAL}] FAILED — {e}")

    elapsed = time.time() - start
    print(f"\n{'─'*40}")
    print(f"Done: {ok} parsed, {failed} failed — {elapsed:.1f}s total (workers={MAX_WORKERS})")


if __name__ == "__main__":
    main()
