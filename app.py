import streamlit as st
import pandas as pd

st.title("📋 Production Line Defect Lookup")

# Upload Excel file
uploaded_file = st.file_uploader("Upload defects Excel file", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [col.strip() for col in df.columns]  # clean column names

    # Input setup number
    setup_number = st.text_input("Enter your setup number:")

    if setup_number:
        filtered = df[df["Setup Number"].astype(str) == setup_number]

        if filtered.empty:
            st.warning(f"No defects found for setup {setup_number}.")
        else:
            st.subheader(f"Most Common Defects for Setup {setup_number}")
            st.dataframe(filtered[["Defect Name", "Frequency", "Preventative Suggestion"]])
