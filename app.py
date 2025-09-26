import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ---------------------------
# Constants / Filenames
# ---------------------------
DEFECT_FILE = "Defect Lookup.xlsx"
FEEDBACK_FILE = "feedback_log.csv"

# ---------------------------
# Helper Functions
# ---------------------------
def load_defects(filename=DEFECT_FILE):
    """Load defects Excel file"""
    df = pd.read_excel(filename)
    df.columns = [col.strip() for col in df.columns]  # Clean column names
    return df

def get_version(filename=DEFECT_FILE):
    """Read the update date from Excel cell B1"""
    try:
        df_version = pd.read_excel(filename, sheet_name=0, nrows=1, usecols="B")
        version = df_version.iloc[0,0]
        return str(version)
    except:
        return "unknown"

def get_defects_for_setup(df, setup_number, top_n=6):
    """Filter defects for a given setup and return top N (non-case-sensitive)"""
    setup_number = str(setup_number).lower()  # convert input to lowercase
    filtered = df[df["Setup Number"].astype(str).str.lower() == setup_number]
    
    freq_order = {"High": 3, "Medium": 2, "Low": 1}
    filtered["FreqOrder"] = filtered["Frequency"].map(freq_order).fillna(0)
    filtered = filtered.sort_values(by="FreqOrder", ascending=False).head(top_n)
    
    return filtered[["Defect Name", "Frequency", "Preventative Suggestion"]]

def submit_feedback(setup_number, operator, feedback_text):
    """Append feedback to the CSV log"""
    entry = {
        "Setup Number": setup_number,
        "Operator": operator,
        "Feedback": feedback_text,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if os.path.exists(FEEDBACK_FILE):
        df_feedback = pd.read_csv(FEEDBACK_FILE)
        df_feedback = pd.concat([df_feedback, pd.DataFrame([entry])], ignore_index=True)
    else:
        df_feedback = pd.DataFrame([entry])
    df_feedback.to_csv(FEEDBACK_FILE, index=False)
    st.success("Feedback submitted successfully!")

# ---------------------------
# Streamlit App
# ---------------------------
def main():
    st.set_page_config(page_title="Production Line App", layout="wide")
    st.title("📋 Production Line App")

    # Landing page option
    option = st.radio("Select an option:", ["Lookup Setup", "Setup Feedback"])

    # Load defects data
    df = load_defects()
    updated_date = get_version()
    
    if option == "Lookup Setup":
        st.subheader("Lookup Setup Defects")
        setup_number = st.text_input("Enter your setup number:")
        if setup_number:
            top_defects = get_defects_for_setup(df, setup_number)
            if top_defects.empty:
                st.warning(f"No defects found for setup {setup_number}.")
            else:
                st.subheader(f"Top {len(top_defects)} Most Common Defects for Setup {setup_number}")
                st.dataframe(top_defects)

        # Optional feedback at the bottom
        st.markdown("---")
        st.subheader("Submit Feedback for this Setup")
        operator = st.text_input("Operator Name:", key="bottom_operator")
        feedback_text = st.text_area("Feedback:", key="bottom_text")
        if st.button("Submit Feedback for this setup"):
            if not setup_number or not operator or not feedback_text:
                st.error("Please fill in all fields before submitting.")
            else:
                submit_feedback(setup_number, operator, feedback_text)

    elif option == "Setup Feedback":
        st.subheader("Submit Setup Feedback")
        setup_number = st.text_input("Enter your setup number:", key="fb_setup")
        operator = st.text_input("Enter your name:", key="fb_operator")
        feedback_text = st.text_area("Enter your feedback here:", key="fb_text")
        if st.button("Submit Feedback"):
            if not setup_number or not operator or not feedback_text:
                st.error("Please fill in all fields before submitting.")
            else:
                submit_feedback(setup_number, operator, feedback_text)

    # Show updated date at the bottom of the landing page
    st.markdown("---")
    st.markdown(f"*Updated: {updated_date}*")

if __name__ == "__main__":
    main()


