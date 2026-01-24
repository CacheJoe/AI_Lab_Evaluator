def compute_marks(row):
    """
    Returns a dictionary with:
    - Raw_Marks (0–100)
    - Regulated_Marks (0–100)
    - Final_Marks_5 (1–5)
    - AI_Likelihood (0–1)
    """

    # -------------------------------------------------
    # 1. RAW MARK COMPUTATION (your original logic)
    # -------------------------------------------------
    raw = 0

    raw += 5 if row.get("Filename_OK") else 0
    raw += 25 if row.get("Missing_Sections") == "" else 0

    theory_words = row.get("Theory_Words", 0)
    if 200 <= theory_words <= 300:
        raw += 10
    elif theory_words > 300:
        raw += 5

    raw += 10 if row.get("Screenshots") else 0
    raw += 15 if row.get("Implementation_Present") else 0

    if row.get("Plagiarism") == "LOW":
        raw += 15
    elif row.get("Plagiarism") == "MEDIUM":
        raw += 7

    if row.get("Analysis_Present") and row.get("Conclusion_Present"):
        raw += 10

    raw = min(raw, 100)

    # -------------------------------------------------
    # 2. AI LIKELIHOOD (heuristic, non-punitive)
    # -------------------------------------------------
    ai_likelihood = 0.0

    # Polished text but low plagiarism → possible AI
    if row.get("Plagiarism") == "LOW" and theory_words >= 150:
        ai_likelihood += 0.4

    # Very clean structure with medium length → AI-ish
    if row.get("Missing_Sections") == "" and 120 <= theory_words <= 300:
        ai_likelihood += 0.3

    # Screenshots missing but theory strong → suspicion
    if not row.get("Screenshots") and theory_words > 200:
        ai_likelihood += 0.3

    ai_likelihood = min(round(ai_likelihood, 2), 1.0)

    # -------------------------------------------------
    # 3. REGULATED MARKS (examiner-like moderation)
    # -------------------------------------------------
    regulated = raw

    if ai_likelihood > 0.7:
        regulated = min(regulated, 65)
    elif ai_likelihood > 0.4:
        regulated = min(regulated, 80)

    # -------------------------------------------------
    # 4. CONVERT TO /5 (banded, dispute-proof)
    # -------------------------------------------------
    if regulated >= 85:
        final_5 = 5
    elif regulated >= 70:
        final_5 = 4
    elif regulated >= 55:
        final_5 = 3
    elif regulated >= 40:
        final_5 = 2
    else:
        final_5 = 1

    return {
        "Raw_Marks": round(raw, 1),
        "Regulated_Marks": round(regulated, 1),
        "Final_Marks_5": final_5,
        "AI_Likelihood": ai_likelihood,
        # backward compatibility
        "Total_Marks": round(regulated, 1)
    }
