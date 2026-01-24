import pandas as pd

def build_reports(names, similarity_matrix, threshold=0.45):
    n = len(names)

    # ------------------------------------
    # 1. Pairwise similarity (UNIQUE pairs)
    # ------------------------------------
    rows = []
    for i in range(n):
        for j in range(i + 1, n):   # ✅ unique pairs only
            rows.append({
                "Student_A": names[i],
                "Student_B": names[j],
                "Similarity": round(float(similarity_matrix[i][j]) * 100, 1)
            })

    pairwise = pd.DataFrame(rows)

    # ------------------------------------
    # 2. Suspicious pairs (UNIQUE)
    # ------------------------------------
    suspects = []
    for i in range(n):
        for j in range(i + 1, n):   # ✅ unique pairs only
            sim = float(similarity_matrix[i][j])

            if sim >= threshold:
                suspects.append({
                    "Student_1": names[i],
                    "Student_2": names[j],
                    "Similarity": round(sim * 100, 1),
                    "Risk_Level": (
                        "Near Duplicate" if sim >= 0.90 else
                        "High Risk" if sim >= 0.75 else
                        "Suspicious"
                    )
                })

    who = pd.DataFrame(suspects)

    return pairwise, who
