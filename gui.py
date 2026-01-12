import streamlit as st
import pandas as pd

st.title("GC AI Lab Auto Assessment")

df = pd.read_csv("reports/final_marks.csv")
st.dataframe(df)

st.download_button("Download Marks CSV", df.to_csv(index=False), "GC_AI_Marks.csv")
