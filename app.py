import streamlit as st
import pandas as pd

st.set_page_config(page_title="Production Line Defect Lookup", layout="wide")
st.title("📋 Production Line Defect Lookup")

# ---------------------------
# Load Excel directly from repo
# ---------------------------
EXCEL_FILE = "Defect Lookup.xlsx"  # Must be in same folder as app.py
df = pd.read_excel(EXCEL_FILE)
df.columns = [col.strip() for col in df.columns]  # Clean column names

# ---------------------------
# Input setup number
# ---------------------------
setup_number = st.text_input("Enter your setup number:")

if setup_number:
    filtered = df[df["Setup Number"].astype(str) == setup_number]

    if filtered.empty:
        st.warning(f"No defects found for setup {setup_number}.")
    else:
        st.subheader(f"Top 6 Most Common Defects for Setup {setup_number}")

        # Sort by Frequency (assuming you have 'High', 'Medium', 'Low') or numeric column
        # If Frequency is numeric:
        # filtered = filtered.sort_values(by="Frequency", ascending=False)
        # If Frequency is categorical, you can map to numbers first:
        freq_order = {"High": 3, "Medium": 2, "Low": 1}
        filtered["FreqOrder"] = filtered["Frequency"].map(freq_order)
        filtered = filtered.sort_values(by="FreqOrder", ascending=False).head(6)

        st.dataframe(filtered[["Defect Name", "Frequency", "Preventative Suggestion"]])


