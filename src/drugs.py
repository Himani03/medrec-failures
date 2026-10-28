"""Small drug lexicon used to (a) find target drugs in real notes and
(b) match model output back to the target drug (brand <-> generic).

This is deliberately small and hand-checked rather than a full RxNorm lookup:
we only ever need to recognise ONE target drug per note.

Each entry: canonical generic name -> list of aliases (brand names, common
spellings). Only oral/common outpatient drugs that are clinically meaningful
to hold or re-dose are included. Lowercase everywhere.
"""
import re

DRUGS = {
    # cardiovascular
    "lisinopril": ["prinivil", "zestril"],
    "enalapril": ["vasotec"],
    "losartan": ["cozaar"],
    "valsartan": ["diovan"],
    "metoprolol": ["lopressor", "toprol", "toprol-xl", "toprol xl"],
    "atenolol": ["tenormin"],
    "carvedilol": ["coreg"],
    "amlodipine": ["norvasc"],
    "diltiazem": ["cardizem"],
    "hydrochlorothiazide": ["hctz", "microzide"],
    "furosemide": ["lasix"],
    "spironolactone": ["aldactone"],
    "digoxin": ["lanoxin"],
    "warfarin": ["coumadin", "jantoven"],
    "clopidogrel": ["plavix"],
    "aspirin": ["asa", "ecotrin"],
    "atorvastatin": ["lipitor"],
    "simvastatin": ["zocor"],
    "rosuvastatin": ["crestor"],
    "pravastatin": ["pravachol"],
    "isosorbide mononitrate": ["imdur"],
    "nitroglycerin": ["nitrostat"],
    "hydralazine": ["apresoline"],
    "clonidine": ["catapres"],
    "amiodarone": ["cordarone", "pacerone"],
    "ramipril": ["altace"],
    "flecainide": ["tambocor"],
    # endocrine
    "metformin": ["glucophage"],
    "glipizide": ["glucotrol"],
    "glyburide": ["diabeta", "micronase"],
    "levothyroxine": ["synthroid", "levoxyl", "unithroid"],
    "prednisone": ["deltasone"],
    "pioglitazone": ["actos"],
    # GI
    "omeprazole": ["prilosec"],
    "pantoprazole": ["protonix"],
    "esomeprazole": ["nexium"],
    "lansoprazole": ["prevacid"],
    "ranitidine": ["zantac"],
    "famotidine": ["pepcid"],
    "docusate": ["colace"],
    "metoclopramide": ["reglan"],
    # neuro / psych
    "gabapentin": ["neurontin"],
    "sertraline": ["zoloft"],
    "fluoxetine": ["prozac"],
    "paroxetine": ["paxil"],
    "citalopram": ["celexa"],
    "escitalopram": ["lexapro"],
    "trazodone": ["desyrel"],
    "lorazepam": ["ativan"],
    "alprazolam": ["xanax"],
    "clonazepam": ["klonopin"],
    "phenytoin": ["dilantin"],
    "levetiracetam": ["keppra"],
    "carbamazepine": ["tegretol"],
    "quetiapine": ["seroquel"],
    "olanzapine": ["zyprexa"],
    "risperidone": ["risperdal"],
    "lithium": ["lithobid"],
    "donepezil": ["aricept"],
    "amitriptyline": ["elavil"],
    "bupropion": ["wellbutrin"],
    "zolpidem": ["ambien"],
    # pain
    "ibuprofen": ["motrin", "advil"],
    "naproxen": ["naprosyn", "aleve"],
    "acetaminophen": ["tylenol"],
    "hydrocodone": ["vicodin", "norco", "lortab"],
    "oxycodone": ["percocet", "oxycontin"],
    "tramadol": ["ultram"],
    "celecoxib": ["celebrex"],
    "cyclobenzaprine": ["flexeril"],
    # pulm / allergy
    "montelukast": ["singulair"],
    "albuterol": ["proventil", "ventolin"],
    "cetirizine": ["zyrtec"],
    "loratadine": ["claritin"],
    # GU / other
    "tamsulosin": ["flomax"],
    "finasteride": ["proscar"],
    "allopurinol": ["zyloprim"],
    "potassium chloride": ["k-dur", "klor-con"],
    "alendronate": ["fosamax"],
}

# alias -> canonical
ALIAS = {}
for gen, aliases in DRUGS.items():
    ALIAS[gen] = gen
    for a in aliases:
        ALIAS[a] = gen


def find_alias(alias: str, text: str):
    """Yield whole-word matches of a drug alias in text (case-insensitive)."""
    pattern = r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])"
    return re.finditer(pattern, text.lower())


def canonical(name: str):
    """Map a free-text drug name such as 'Toprol XL 50 mg' to its generic
    name ('metoprolol'). Returns None if the drug is not in the lexicon."""
    text = name.lower().strip()
    if text in ALIAS:
        return ALIAS[text]

    # Otherwise pick the longest alias that appears as a whole word.
    matches = [alias for alias in ALIAS if any(find_alias(alias, text))]
    if not matches:
        return None
    return ALIAS[max(matches, key=len)]
