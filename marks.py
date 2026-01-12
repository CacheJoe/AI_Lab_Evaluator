def compute_marks(row):
    marks = 0

    marks += 5 if row["Filename_OK"] else 0
    marks += 25 if row["Missing_Sections"] == "" else 0

    if 200 <= row["Theory_Words"] <= 300:
        marks += 10
    elif row["Theory_Words"] > 300:
        marks += 5

    marks += 10 if row["Screenshots"] else 0
    marks += 15 if row["Implementation_Present"] else 0

    if row["Plagiarism"] == "LOW":
        marks += 15
    elif row["Plagiarism"] == "MEDIUM":
        marks += 7

    if row["Analysis_Present"] and row["Conclusion_Present"]:
        marks += 10

    return marks
