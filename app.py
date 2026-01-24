import streamlit as st
import os
import pandas as pd
from run_all import run_evaluation

st.set_page_config(page_title="GC – AI Lab Evaluator", layout="wide")

# ---------------- ERP Styling ----------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Segoe UI", system-ui;
}
[data-testid="stSidebar"] {
    background-color: #0b4aa2;
}
[data-testid="stSidebar"] * {
    color: white;
}
.erp-header {
    background-color: #0b4aa2;
    padding: 16px 24px;
    color: white;
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 12px;
}
.erp-panel {
    background: white;
    border: 1px solid #e1e1e1;
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 16px;
}
.erp-title {
    font-weight: 600;
    color: #323130;
    margin-bottom: 8px;
}
.stButton>button {
    background-color: #0b5ed7 !important;
    color: white !important;
    border-radius: 4px !important;
    height: 36px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar ----------------
st.sidebar.markdown("## GC – AI Evaluator")
page = st.sidebar.radio("Modules", ["Dashboard", "Evaluate", "Reports"])
st.sidebar.selectbox("Class / Section", ["All", "CSE-A", "CSE-B", "CSE-C", "AI-ML", "DS"])

st.markdown('<div class="erp-header">AI Lab Evaluation System</div>', unsafe_allow_html=True)

# ---------------- Session Storage ----------------
if "results" not in st.session_state:
    st.session_state["results"] = None

# ---------------- Helpers ----------------
def integrity_badge(row):
    if row["Plagiarism"] == "HIGH":
        return "🔴 High Risk"
    elif row["Plagiarism"] == "MEDIUM":
        return "🟠 Suspicious"
    else:
        return "🟢 Clean"

# 🔧 NEW: AI likelihood badge (faculty-safe language)
def ai_badge(val):
    if val >= 0.6:
        return "🔴 High AI-likelihood"
    elif val >= 0.3:
        return "🟠 Possible AI-likelihood"
    else:
        return "🟢 Low AI-likelihood"

# ---------------- Evaluate Page ----------------
if page == "Evaluate":

    left, right = st.columns([2,3])

    with left:
        st.markdown('<div class="erp-panel">', unsafe_allow_html=True)
        st.markdown('<div class="erp-title">Experiment Setup</div>', unsafe_allow_html=True)
        topic = st.text_area("Experiment Topic / Aim", height=80)
        uploaded = st.file_uploader("Student PDF Submissions", type=["pdf"], accept_multiple_files=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Evaluate Submissions"):
            if not uploaded or not topic.strip():
                st.error("Please upload PDFs and enter topic.")
            else:
                os.makedirs("submissions", exist_ok=True)
                for f in os.listdir("submissions"):
                    os.remove(os.path.join("submissions", f))

                for f in uploaded:
                    with open(os.path.join("submissions", f.name), "wb") as out:
                        out.write(f.read())

                with st.spinner("Running evaluation engine..."):
                    st.session_state["results"] = run_evaluation("submissions", topic)

    with right:
        if st.session_state["results"]:
            df, pairwise, who, graph_html = st.session_state["results"]

            # -------- Integrity + AI Badges --------
            df["Integrity_Status"] = df.apply(integrity_badge, axis=1)
            df["AI_Status"] = df["AI_Likelihood"].apply(ai_badge)   # 🔧 NEW

            # -------- Similarity Mapping --------
            df["Matched_With"] = ""
            if who is not None and not who.empty:
                for _, r in who.iterrows():
                    a, b = r["Student_1"], r["Student_2"]
                    label = f"{r['Risk_Level']} ({r['Similarity']}%)"
                    df.loc[df["File"] == a, "Matched_With"] = label
                    df.loc[df["File"] == b, "Matched_With"] = label

            # -------- Final Marks Table --------
            st.markdown('<div class="erp-panel">', unsafe_allow_html=True)
            st.markdown('<div class="erp-title">Final Marks</div>', unsafe_allow_html=True)

            display_cols = [
                "File",
                "Final_Marks_5",
                "Regulated_Marks",
                "AI_Status",          # 🔧 NEW
                "Integrity_Status",
                "Matched_With"
            ]
            st.dataframe(df[display_cols], use_container_width=True)
            st.download_button("Download Final Marks", df.to_csv(index=False), "final_marks.csv")
            st.markdown('</div>', unsafe_allow_html=True)

            # -------- Student Drilldown --------
            st.markdown('<div class="erp-panel">', unsafe_allow_html=True)
            st.markdown('<div class="erp-title">Student Drilldown</div>', unsafe_allow_html=True)

            student = st.selectbox("Select Student", df["File"].tolist())

            if student:
                row = df[df["File"] == student].iloc[0]

                st.write("**Final Marks (out of 5):**", row["Final_Marks_5"])
                st.write("**AI Writing Pattern:**", ai_badge(row["AI_Likelihood"]))
                st.caption(f"Internal confidence: {row['AI_Likelihood']*100:.0f}%")

                st.write("**Integrity Status:**", row["Integrity_Status"])
                st.write("**Integrity Remark:**", row["Integrity_Remark"])
                st.write("**Matched With:**", row["Matched_With"])
                st.write("**Screenshot Status:**", row["Screenshot_Status"])

            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Reports Page ----------------
if page == "Reports" and st.session_state["results"]:
    _, pairwise, who, graph_html = st.session_state["results"]

    if graph_html:
        st.markdown('<div class="erp-panel">', unsafe_allow_html=True)
        st.markdown('<div class="erp-title">Plagiarism Network</div>', unsafe_allow_html=True)
        st.components.v1.html(graph_html, height=700)
        st.markdown('</div>', unsafe_allow_html=True)
