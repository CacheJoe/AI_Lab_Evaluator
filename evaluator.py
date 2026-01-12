import os
import re
import pdfplumber
from PyPDF2 import PdfReader

# ============================================================
#  SECTION → ALIASES (what students actually write)
# ============================================================

SECTION_ALIASES = {
    "Experiment Title": [
        "experiment title", "lab experiment", "practical no", "experiment no",
        "experiment", "lab no"
    ],
    "Aim / Objective": [
        "aim", "objective", "aims"
    ],
    "Theory": [
        "theory", "background"
    ],
    "Algorithm / Methodology": [
        "algorithm", "methodology", "procedure", "steps", "method"
    ],
    "Dataset Description": [
        "dataset", "data set", "data description", "dataset description"
    ],
    "Implementation": [
        "implementation", "code", "program", "python code"
    ],
    "Output / Result": [
        "output", "result", "results", "output result"
    ],
    "Result Analysis": [
        "analysis", "observation", "result analysis", "discussion"
    ],
    "Conclusion": [
        "conclusion", "inference", "summary"
    ]
}

REQUIRED_HEADINGS = list(SECTION_ALIASES.keys())

# ============================================================
#  TEXT EXTRACTION
# ============================================================

def extract_text(pdf_path):
    try:
        full = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    full += t + "\n"

                try:
                    words = page.extract_words()
                    for w in words:
                        full += " " + w["text"]
                except:
                    pass
        return full
    except:
        return ""


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================
#  TOKEN-WINDOW SEMANTIC DETECTOR
# ============================================================

def section_exists(norm_text, aliases):
    words = norm_text.split()

    for alias in aliases:
        alias_tokens = set(alias.split())
        window = len(alias_tokens) + 4

        for i in range(len(words) - window + 1):
            chunk = set(words[i:i+window])
            if alias_tokens.issubset(chunk):
                return True

    return False


# ============================================================
#  IMAGE COUNT
# ============================================================

def count_images(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        count = 0
        for page in reader.pages:
            res = page.get("/Resources", {})
            if "/XObject" in res:
                xobj = res["/XObject"].get_object()
                for o in xobj:
                    try:
                        if xobj[o]["/Subtype"] == "/Image":
                            count += 1
                    except:
                        pass
        return count
    except:
        return 0


# ============================================================
#  THEORY EXTRACTION
# ============================================================

def extract_theory(text):
    patterns = [
        r"theory\s*[:\-]?\s*(.*?)(algorithm|methodology|procedure|steps)",
        r"theory\s*[:\-]?\s*(.*?)(dataset|implementation|code)",
    ]

    for p in patterns:
        m = re.search(p, text, re.S | re.I)
        if m:
            return m.group(1)

    if re.search(r"\btheory\b", text, re.I):
        return "__THEORY_PRESENT__"

    return ""


# ============================================================
#  MAIN EVALUATION
# ============================================================

def evaluate(pdf_path):
    filename = os.path.basename(pdf_path)

    raw_text = extract_text(pdf_path)
    norm_text = normalize(raw_text)

    missing = []
    found = {}

    for section, aliases in SECTION_ALIASES.items():
        exists = section_exists(norm_text, aliases)
        found[section] = exists
        if not exists:
            missing.append(section)

    theory = extract_theory(raw_text)

    if theory == "__THEORY_PRESENT__":
        theory_words = 1
    else:
        theory_words = len(theory.split())

    return {
        "File": filename,
        "Filename_OK": bool(re.match(r".+_Exp\d+_AI_GC\.pdf", filename)),
        "Missing_Sections": ", ".join(missing),
        "Theory_Words": theory_words,
        "Screenshots": count_images(pdf_path) > 0,
        "Implementation_Present": found["Implementation"],
        "Analysis_Present": found["Result Analysis"],
        "Conclusion_Present": found["Conclusion"],
        "Theory_Text": "" if theory == "__THEORY_PRESENT__" else theory
    }
