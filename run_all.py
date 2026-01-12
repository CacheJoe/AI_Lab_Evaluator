import os
import pandas as pd
import evaluator
import plagiarism
from plagiarism_report import build_reports
from plagiarism import plagiarism_matrix
from screenshot_check import analyze_screenshots
from semantic import evaluate_sections
from plagiarism_graph import build_graph_html

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
    # Plagiarism flags (text)
    # -------------------------------------------------
    df["Plagiarism"] = plagiarism.plagiarism_flags(df["Theory_Text"].fillna("").tolist())

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
    df["Theory_Relevance"] = 0.0
    df["Algorithm_Relevance"] = 0.0
    df["Analysis_Relevance"] = 0.0
    df["Conclusion_Relevance"] = 0.0

    for i, row in df.iterrows():
        scores = evaluate_sections(
            topic,
            row.get("Theory_Text",""),
            row.get("Theory_Text",""),
            row.get("Theory_Text",""),
            row.get("Theory_Text","")
        )

        for k,v in scores.items():
            df.at[i,k] = round(v,3)

    # -------------------------------------------------
    # FAIR MARKING (40-25-20-15)
    # -------------------------------------------------
    df["Total_Marks"] = 0

    exec_score = 0
    exec_score += df["Filename_OK"].astype(int) * 5
    exec_score += df["Screenshots"].astype(int) * 10
    exec_score += df["Screenshot_Status"].map({"OK":10,"BLANK":3,"NONE":0}).fillna(0)
    exec_score -= (df["Screenshot_Plagiarism"] != "").astype(int) * 5
    exec_score += df["Implementation_Present"].astype(int) * 10
    df["Total_Marks"] += exec_score.clip(0,40)

    df["Section_Count"] = df["Missing_Sections"].apply(lambda x: 9 - len(x.split(",")) if x else 9)
    structure_score = (df["Section_Count"] / 9) * 15
    theory_score = df["Theory_Words"].apply(lambda x: 10 if x>=150 else 6 if x>=80 else 2)
    df["Total_Marks"] += structure_score + theory_score

    semantic_avg = (
        df["Theory_Relevance"] +
        df["Algorithm_Relevance"] +
        df["Analysis_Relevance"] +
        df["Conclusion_Relevance"]
    ) / 4

    understanding_score = semantic_avg.apply(
        lambda x: 20 if x>0.65 else 15 if x>0.50 else 10 if x>0.35 else 5
    )
    df["Total_Marks"] += understanding_score

    # -------------------------------------------------
    # INTEGRITY — MUTUAL PENALTY MODEL
    # -------------------------------------------------
    df.loc[df["Screenshot_Plagiarism"].str.strip() != "", "Plagiarism"] = "HIGH"

    df["Integrity_Points"] = 15
    df["Integrity_Remark"] = ""

    df.loc[df["Plagiarism"] == "MEDIUM", "Integrity_Points"] = 8
    df.loc[df["Plagiarism"] == "HIGH", "Integrity_Points"] = 0

    df.loc[df["Plagiarism"] == "MEDIUM", "Integrity_Remark"] = "Suspicious similarity detected"
    df.loc[df["Plagiarism"] == "HIGH", "Integrity_Remark"] = "High similarity – likely copied"

    df["Total_Marks"] += df["Integrity_Points"]
    df["Total_Marks"] = df["Total_Marks"].round(1).clip(0,100)

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

    df_final = df.drop(columns=["Theory_Text"])

    return df_final, pairwise_df, who_df, graph_html
