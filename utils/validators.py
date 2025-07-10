from difflib import get_close_matches

ALLOWED = {
    'officeType':    ['Remote','Hybrid','In-Office','Remote-Anywhere'],
    'experienceLevel': ['Intern','Entry-Level','Associate/Mid-Level','Senior-Level','Managerial','Executive'],
    'employmentType': ['Full-Time','Part-Time','Contract','Freelance','Temporary'],
    'industries':    ['Tech','Healthcare','Marketing','Consulting','Finance','Manufacturing'],
    'visa':          ['Yes','No']
}

def normalize_choice(val, choices, default=None):
    if val in choices:
        return val
    m = get_close_matches(val, choices, n=1, cutoff=0.6)
    return m[0] if m else (default or choices[0])

def normalize_list(val, choices, count):
    items = [v.strip() for v in val.split(',') if v.strip()]
    norm = []
    for item in items:
        nc = normalize_choice(item, choices)
        if nc not in norm:
            norm.append(nc)
        if len(norm) == count:
            break
    while len(norm) < count:
        norm.append(choices[0])
    return ','.join(norm)

def validate_record(rec):
    rec['officeType']     = normalize_choice(rec.get('officeType',''), ALLOWED['officeType'])
    rec['experienceLevel']= normalize_choice(rec.get('experienceLevel',''), ALLOWED['experienceLevel'])
    rec['employmentType'] = normalize_choice(rec.get('employmentType',''), ALLOWED['employmentType'])
    rec['industries']     = normalize_list(rec.get('industries',''), ALLOWED['industries'], 3)
    rec['visa']           = normalize_choice(rec.get('visa',''), ALLOWED['visa'], default='No')
    # currency → first symbol
    cur = rec.get('currency','').strip()
    rec['currency']       = cur[0] if cur else ''
    # skills → ensure exactly 5 comma-separated
    skills = [s.strip() for s in rec.get('skills','').split(',') if s.strip()]
    while len(skills) < 5:
        skills.append('Skill') 
    rec['skills']         = ','.join(skills[:5])
    return rec
