# run with `python src/data/load_vacancies.py` from root project folder

import json
from src.schemas.vacancy import Vacancy

path = "data/synth/ofertes.json"

def load():
    data = json.load(open(path))
    vacancies = [Vacancy(**v) for v in data]
    return None, vacancies

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
