# utils/validators.py

from difflib import get_close_matches

ALLOWED = {
    'officeType': [
        'Remote',
        'Hybrid',
        'In-Office',
        'Remote-Anywhere'
    ],
    'experienceLevel': [
        'Intern',
        'Entry-Level',
        'Associate/Mid-Level',
        'Senior-Level',
        'Managerial',
        'Executive'
    ],
    'employmentType': [
        'Full-Time',
        'Part-Time',
        'Contract',
        'Freelance',
        'Temporary'
    ],
    'industries': [
        'Tech',
        'Healthcare',
        'Marketing',
        'Consulting',
        'Finance',
        'Manufacturing'
    ],
    'visa': [
        'Yes',
        'No'
    ]
}

def normalize_choice(val: str, choices: list[str], default: str = None) -> str:
    v = val.strip()
    if v in choices:
        return v
    matches = get_close_matches(v, choices, n=1, cutoff=0.6)
    return matches[0] if matches else (default or choices[0])

def normalize_list(val: str, choices: list[str], max_items: int = None) -> str:
    items = [v.strip() for v in val.split(',') if v.strip()]
    normalized = []
    for item in items:
        nc = normalize_choice(item, choices)
        if nc not in normalized:
            normalized.append(nc)
        if max_items and len(normalized) >= max_items:
            break
    return ','.join(normalized)

def validate_record(rec: dict) -> dict:
    rec['officeType'] = normalize_choice(
        rec.get('officeType', ''), ALLOWED['officeType'], default=''
    )
    rec['experienceLevel'] = normalize_choice(
        rec.get('experienceLevel', ''), ALLOWED['experienceLevel'], default=''
    )
    rec['employmentType'] = normalize_choice(
        rec.get('employmentType', ''), ALLOWED['employmentType'], default=''
    )
    rec['industries'] = normalize_list(
        rec.get('industries', ''), ALLOWED['industries']
    )
    rec['visa'] = normalize_choice(
        rec.get('visa', ''), ALLOWED['visa'], default='No'
    )
    cur = rec.get('currency', '').strip()
    rec['currency'] = cur[0] if cur else ''
    rec['benefits'] = rec.get('benefits', '').strip()
    skills = [s.strip() for s in rec.get('skills', '').split(',') if s.strip()]
    seen = []
    for s in skills:
        if s not in seen:
            seen.append(s)
    rec['skills'] = ','.join(seen)
    return rec
