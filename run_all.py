import os
import pandas as pd
import evaluator
import plagiarism
from plagiarism_report import build_reports
from plagiarism import plagiarism_matrix
from screenshot_check import analyze_screenshots
from semantic import evaluate_sections
from plagiarism_graph import build_graph

SUB = "submissions"
REP = "reports"
os.makedirs(REP, exist_ok=True)

# -------------------------------------------------
# Ask teacher for topic
# -------------------------------------------------
topic = input("\nEnter the topic / aim of this experiment:\n> ")

# -------------------------------------------------
# Load PDFs
# -------------------------------------------------
records = []
for f in os.listdir(SUB):
    if f.lower().endswith(".pdf"):
        records.append(evaluator.evaluate(os.path.join(SUB, f)))

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
# Plagiarism flags
# -------------------------------------------------
df["Plagiarism"] = plagiarism.plagiarism_flags(df["Theory_Text"].fillna("").tolist())

# -------------------------------------------------
# Screenshot forensics
# -------------------------------------------------
pdf_paths = [os.path.join(SUB, f) for f in df["File"].tolist()]
screen_report, duplicates = analyze_screenshots(pdf_paths)

df["Screenshot_Status"] = "OK"
df["Screenshot_Plagiarism"] = ""

for i, row in df.iterrows():
    path = os.path.join(SUB, row["File"])
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

# ---------- 1. Execution & Evidence (40) ----------
exec_score = 0
exec_score += df["Filename_OK"].astype(int) * 5
exec_score += df["Screenshots"].astype(int) * 10
exec_score += df["Screenshot_Status"].map({"OK":10,"BLANK":3,"NONE":0}).fillna(0)
exec_score -= (df["Screenshot_Plagiarism"] != "").astype(int) * 5
exec_score += df["Implementation_Present"].astype(int) * 10
df["Total_Marks"] += exec_score.clip(0,40)

# ---------- 2. Structure & Completeness (25) ----------
df["Section_Count"] = df["Missing_Sections"].apply(lambda x: 9 - len(x.split(",")) if x else 9)
structure_score = (df["Section_Count"] / 9) * 15
theory_score = df["Theory_Words"].apply(lambda x: 10 if x>=150 else 6 if x>=80 else 2)
df["Total_Marks"] += structure_score + theory_score

# ---------- 3. Understanding (20) ----------
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

# ---------- 4. Academic Integrity (15) ----------
integrity_score = df["Plagiarism"].map({"LOW":15,"MEDIUM":8,"HIGH":0}).fillna(0)
df["Total_Marks"] += integrity_score

df["Total_Marks"] = df["Total_Marks"].round(1).clip(0,100)

# -------------------------------------------------
# Plagiarism network
# -------------------------------------------------
sim_matrix, index_map = plagiarism_matrix(df["Theory_Text"].fillna("").tolist())

if sim_matrix is not None and len(index_map) > 1:
    names = df.iloc[index_map]["File"].tolist()
    pairwise, graph = build_reports(names, sim_matrix)
    pairwise.to_csv(f"{REP}/pairwise_similarity.csv", index=False)
    graph.to_csv(f"{REP}/who_copied_from_whom.csv", index=False)
    build_graph(f"{REP}/who_copied_from_whom.csv")

# -------------------------------------------------
# Save
# -------------------------------------------------
df.drop(columns=["Theory_Text"], inplace=True)
df.to_csv(f"{REP}/final_marks.csv", index=False)

print("✅ GC-AI Lab Evaluation Completed")
print("📄 reports/final_marks.csv")
