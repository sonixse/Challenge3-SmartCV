import json
from pathlib import Path
from src.schemas.candidate import CandidateProfile
from src.data.load_vacancies import load
from src.agents.linguist import analyse

data = json.loads(Path('data/processed/01_candidate.json').read_text())
profile = CandidateProfile.model_validate(data)
_, vacs = load()

scores = []
for vac in vacs[:15]:
    result = analyse(profile, vac)
    for s in result['skills']:
        if s['vacancy_skill'] not in [x[2] for x in scores]:
            scores.append((s['similarity'], s['classification'], s['vacancy_skill'], s.get('best_match','')))

matches = [s for s in scores if s[1]=='MATCH']
greys   = [s for s in scores if s[1]=='GREY ZONE']
nones   = [s for s in scores if s[1]=='NO MATCH']

print(f'MATCH: {len(matches)} | GREY ZONE: {len(greys)} | NO MATCH: {len(nones)}')

if greys:
    print('Grey zones remaining:')
    for sim, cls, vsk, bm in sorted(greys, reverse=True):
        print(f'  {sim:.4f}  {vsk:30} ~ {bm}')