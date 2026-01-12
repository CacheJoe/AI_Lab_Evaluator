import pandas as pd

def build_reports(names, similarity_matrix, threshold=0.45):
    n = len(names)

    # -------- Pairwise similarity --------
    rows = []
    for i in range(n):
        for j in range(n):
            if i != j:
                rows.append({
                    "Student_A": names[i],
                    "Student_B": names[j],
                    "Similarity": round(float(similarity_matrix[i][j]) * 100, 1)
                })

    pairwise = pd.DataFrame(rows)

    # -------- All suspicious pairs --------
    suspects = []
    for i in range(n):
        for j in range(n):
            if i != j and similarity_matrix[i][j] >= threshold:
                suspects.append({
                    "Suspected_Copier": names[i],
                    "Likely_Source": names[j],
                    "Similarity": round(float(similarity_matrix[i][j]) * 100, 1)
                })

    who = pd.DataFrame(suspects)

    return pairwise, who
