import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# run with `python src/data/load_vacancies.py` from root project folder

import json
from pydantic import TypeAdapter
from src.schemas.vacancy import Vacancy

def load():
    path = "data/synth/ofertes.json"
    data = json.loads(open(path, encoding="utf-8").read())

    vacancies = TypeAdapter(list[Vacancy]).validate_python(data)
    return path, vacancies

if __name__ == "__main__":
    path, vacancies = load()
    print(f"Loaded {len(vacancies)} vacancies\n")

    job_titles = set()
    for vac in vacancies:
        job_titles.add(vac.job_title)

    print(f"Job roles in {path} ({len(job_titles)}):\n")
    for job in job_titles: print("\t",job)
    print("\n")

    print("Sectors + comptes:")
    for job in job_titles:
        sectors={}

        print(f"\nPel rol de {job}:\n")
        for vac in vacancies:
            if vac.job_title == job:
                sectors[vac.sector] = sectors.get(vac.sector, 0) + 1
    
        sorted_sectors = dict(sorted(sectors.items(), key=lambda x: x[1], reverse=True))
        print(sorted_sectors)
        #for k,v in sorted_sectors:
        #    print(f"\t{k}: {v}")
        top_sector = next(iter(sorted_sectors))
        print(f"\nTop sector for {job} is", top_sector, f"with {max(sorted_sectors.values())} offers")


