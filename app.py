import streamlit as st
import os
import pandas as pd
import shutil
import subprocess

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
st.sidebar.image("logo.png", use_column_width=True)
st.sidebar.markdown("## GC – AI Evaluator")
page = st.sidebar.radio("Modules", ["Dashboard", "Evaluate", "Reports"])

st.sidebar.markdown("### Class / Section")
class_selected = st.sidebar.selectbox(
    "",
    ["All", "CSE-A", "CSE-B", "CSE-C", "AI-ML", "DS"]
)

# ---------------- Header ----------------
st.markdown('<div class="erp-header">AI Lab Evaluation System</div>', unsafe_allow_html=True)

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
            st.session_state["run"] = True

    # ---------- Run backend ----------
    if st.session_state.get("run"):
        if not uploaded or not topic.strip():
            st.error("Please upload PDFs and enter topic.")
        else:
            if os.path.exists("submissions"):
                shutil.rmtree("submissions")
            os.makedirs("submissions", exist_ok=True)

            for f in uploaded:
                with open(os.path.join("submissions", f.name), "wb") as out:
                    out.write(f.read())

            with st.spinner("Running evaluation engine..."):
                subprocess.run(["python", "run_all.py"], input=topic, text=True)

    # ---------- Results ----------
    with right:
        if os.path.exists("reports/final_marks.csv"):
            df = pd.read_csv("reports/final_marks.csv")

            if class_selected != "All":
                df = df[df["File"].str.contains(class_selected, case=False)]

            st.markdown('<div class="erp-panel">', unsafe_allow_html=True)
            st.markdown('<div class="erp-title">Final Marks</div>', unsafe_allow_html=True)
            st.dataframe(df, width=1200)
            st.download_button("Download Final Marks", df.to_csv(index=False), "final_marks.csv")
            st.markdown('</div>', unsafe_allow_html=True)

            # ---------- Student Drilldown ----------
            st.markdown('<div class="erp-panel">', unsafe_allow_html=True)
            st.markdown('<div class="erp-title">Student Drilldown</div>', unsafe_allow_html=True)
            student = st.selectbox("Select Student", df["File"].tolist())

            if student:
                row = df[df["File"] == student].iloc[0]

                st.write("**Total Marks:**", row["Total_Marks"])
                st.write("**Plagiarism Level:**", row["Plagiarism"])
                st.write("**Screenshot Status:**", row["Screenshot_Status"])

                st.write("**Theory Relevance:**", f"{row['Theory_Relevance']*100:.0f}%")
                st.write("**Algorithm Relevance:**", f"{row['Algorithm_Relevance']*100:.0f}%")
                st.write("**Analysis Relevance:**", f"{row['Analysis_Relevance']*100:.0f}%")
                st.write("**Conclusion Relevance:**", f"{row['Conclusion_Relevance']*100:.0f}%")

                if pd.notna(row["Screenshot_Plagiarism"]) and str(row["Screenshot_Plagiarism"]).strip() != "":
                    st.warning("Screenshot copied from: " + str(row["Screenshot_Plagiarism"]))

            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Reports Page ----------------
if page == "Reports":

    if os.path.exists("reports/plagiarism_network.html"):
        st.markdown('<div class="erp-panel">', unsafe_allow_html=True)
        st.markdown('<div class="erp-title">Plagiarism Network</div>', unsafe_allow_html=True)
        st.components.v1.html(open("reports/plagiarism_network.html").read(), height=700)
        st.markdown('</div>', unsafe_allow_html=True)

    if os.path.exists("reports/who_copied_from_whom.csv"):
        who = pd.read_csv("reports/who_copied_from_whom.csv")
        st.markdown('<div class="erp-panel">', unsafe_allow_html=True)
        st.markdown('<div class="erp-title">Copy Relationships</div>', unsafe_allow_html=True)
        st.dataframe(who, width=1200)
        st.download_button("Download Copy Network", who.to_csv(index=False), "who_copied_from_whom.csv")
        st.markdown('</div>', unsafe_allow_html=True)

    if os.path.exists("reports/pairwise_similarity.csv"):
        pair = pd.read_csv("reports/pairwise_similarity.csv")
        st.markdown('<div class="erp-panel">', unsafe_allow_html=True)
        st.markdown('<div class="erp-title">Pairwise Similarity</div>', unsafe_allow_html=True)
        st.dataframe(pair, width=1200)
        st.download_button("Download Pairwise", pair.to_csv(index=False), "pairwise_similarity.csv")
        st.markdown('</div>', unsafe_allow_html=True)
    if os.path.exists("reports/plagiarism_network.html"):
       st.markdown("### 🕸️ Plagiarism Network")
       st.components.v1.html(open("reports/plagiarism_network.html").read(), height=700)
