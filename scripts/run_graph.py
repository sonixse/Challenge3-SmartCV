from src.orchestrator.graph import compiled
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
cv = BASE_DIR + "/data/raw/01_cv.pdf"

state = {
    "pdf_path": str(cv),
    "model": "llama3"
}

result = compiled.invoke(state)


"""
### Save the result of the graph execution to a CSV file


with open("output.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Candidate", "Vacancy", "Score"])
    for candidate, vacancies in result.items():
        for vacancy, score in vacancies.items():
            writer.writerow([candidate, vacancy, score])
"""