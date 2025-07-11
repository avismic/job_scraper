# utils/validators.py

from difflib import get_close_matches

# Allowed value sets for strict fields
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
    """
    Fuzzy-match a single value to the allowed choices.
    """
    v = val.strip()
    if v in choices:
        return v
    matches = get_close_matches(v, choices, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    return default or choices[0]

def normalize_list(val: str, choices: list[str], max_items: int = None) -> str:
    """
    Normalize a comma-separated list of values:
    - Strip whitespace
    - Fuzzy-match each to allowed choices
    - Deduplicate, preserving order
    - Truncate to max_items if provided
    Returns a comma-separated string of the normalized items.
    """
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
    """
    Apply normalization rules to a parsed record.
    Fields not present are left as-is (or set to '').
    """
    # officeType
    rec['officeType'] = normalize_choice(
        rec.get('officeType', ''),
        ALLOWED['officeType'],
        default=''
    )

    # experienceLevel
    rec['experienceLevel'] = normalize_choice(
        rec.get('experienceLevel', ''),
        ALLOWED['experienceLevel'],
        default=''
    )

    # employmentType
    rec['employmentType'] = normalize_choice(
        rec.get('employmentType', ''),
        ALLOWED['employmentType'],
        default=''
    )

    # industries (no minimum, no padding)
    rec['industries'] = normalize_list(
        rec.get('industries', ''),
        ALLOWED['industries'],
        max_items=None
    )

    # visa (default to 'No' if missing or unrecognized)
    rec['visa'] = normalize_choice(
        rec.get('visa', ''),
        ALLOWED['visa'],
        default='No'
    )

    # currency → keep only first character (symbol)
    cur = rec.get('currency', '').strip()
    rec['currency'] = cur[0] if cur else ''

    # salary fields left as-is (assume numeric/empty)

    # benefits → leave as-is (comma-separated list)
    rec['benefits'] = rec.get('benefits', '').strip()

    # skills (no minimum, no padding)
    skills = [s.strip() for s in rec.get('skills', '').split(',') if s.strip()]
    seen = []
    for s in skills:
        if s not in seen:
            seen.append(s)
    rec['skills'] = ','.join(seen)

    return rec
