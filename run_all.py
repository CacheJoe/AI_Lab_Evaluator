import os
import pandas as pd
import evaluator
import plagiarism
from plagiarism_report import build_reports
from plagiarism import plagiarism_matrix
from screenshot_check import analyze_screenshots
from semantic import evaluate_sections
from plagiarism_graph import build_graph_html
from marks import compute_marks   # ✅ NEW: single source of truth

# -------------------------------------------------
# MAIN CLOUD SAFE FUNCTION
# -------------------------------------------------

def run_evaluation(submission_folder, topic):

    records = []
    for f in os.listdir(submission_folder):
        if f.lower().endswith(".pdf"):
            records.append(evaluator.evaluate(os.path.join(submission_folder, f)))

    df = pd.DataFrame(records)

    # -------------------------------------------------
    # Guarantee columns
    # -------------------------------------------------
    for col in [
        "Theory_Text","Missing_Sections","Filename_OK","Screenshots",
        "Implementation_Present","Analysis_Present","Conclusion_Present","Theory_Words"
    ]:
        if col not in df:
            df[col] = ""

    # -------------------------------------------------
    # 🔧 FIX: Theory word count from RAW text
    # -------------------------------------------------
    df["Theory_Words"] = df["Theory_Text"].fillna("").apply(
        lambda x: len([w for w in x.split() if w.isalpha()])
    )

    # -------------------------------------------------
    # Plagiarism flags (text-level)
    # -------------------------------------------------
    df["Plagiarism"] = plagiarism.plagiarism_flags(
        df["Theory_Text"].fillna("").tolist()
    )

    # -------------------------------------------------
    # Screenshot forensics
    # -------------------------------------------------
    pdf_paths = [os.path.join(submission_folder, f) for f in df["File"].tolist()]
    screen_report, duplicates = analyze_screenshots(pdf_paths)

    df["Screenshot_Status"] = "OK"
    df["Screenshot_Plagiarism"] = ""

    for i, row in df.iterrows():
        path = os.path.join(submission_folder, row["File"])
        status = screen_report.get(path, {}).get("status", "NONE")
        df.at[i, "Screenshot_Status"] = status

        if path in duplicates:
            df.at[i, "Screenshot_Plagiarism"] = ", ".join(
                [os.path.basename(x) for x in duplicates[path]]
            )

    # -------------------------------------------------
    # Semantic understanding
    # -------------------------------------------------
    for sec in [
        "Theory_Relevance",
        "Algorithm_Relevance",
        "Analysis_Relevance",
        "Conclusion_Relevance"
    ]:
        df[sec] = 0.0

    for i, row in df.iterrows():
        scores = evaluate_sections(
            topic,
            row.get("Theory_Text",""),
            row.get("Theory_Text",""),
            row.get("Theory_Text",""),
            row.get("Theory_Text","")
        )
        for k, v in scores.items():
            df.at[i, k] = round(v, 3)

    # -------------------------------------------------
    # 🔒 INTEGRITY NORMALIZATION (NO DOUBLE PENALTY)
    # -------------------------------------------------
    df.loc[df["Screenshot_Plagiarism"].str.strip() != "", "Plagiarism"] = "HIGH"

    df["Integrity_Remark"] = ""
    df.loc[df["Plagiarism"] == "MEDIUM", "Integrity_Remark"] = \
        "Suspicious similarity detected"
    df.loc[df["Plagiarism"] == "HIGH", "Integrity_Remark"] = \
        "High similarity – likely copied"

    # -------------------------------------------------
    # 🎯 MARK COMPUTATION (DELEGATED TO marks.py)
    # -------------------------------------------------
    mark_rows = df.apply(compute_marks, axis=1, result_type="expand")
    df = pd.concat([df, mark_rows], axis=1)

    # -------------------------------------------------
    # BOILERPLATE-STRIPPED PLAGIARISM MATRIX
    # -------------------------------------------------
    cleaned_texts = []
    for t in df["Theory_Text"].fillna(""):
        t = t.lower()
        for junk in [
            "ramdeobaba", "rcoem", "experiment", "aim", "objective",
            "department", "computer science", "data science",
            "university", "semester", "roll no", "name:", "date:"
        ]:
            t = t.replace(junk, "")
        t = "".join([c for c in t if not c.isdigit()])
        t = " ".join(t.split())
        cleaned_texts.append(t)

    sim_matrix, index_map = plagiarism_matrix(cleaned_texts)

    pairwise_df = None
    who_df = None
    graph_html = None

    if sim_matrix is not None and len(index_map) > 1:
        names = df.iloc[index_map]["File"].tolist()
        pairwise_df, who_df = build_reports(names, sim_matrix)
        graph_html = build_graph_html(who_df)

    # -------------------------------------------------
    # FINAL OUTPUT (UI SAFE)
    # -------------------------------------------------
    df_final = df.drop(columns=["Theory_Text"])

    return df_final, pairwise_df, who_df, graph_html
