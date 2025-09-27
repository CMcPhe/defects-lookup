import streamlit as st
import pandas as pd
from datetime import datetime
from github import Github
import io

# ---------------------------
# Config
# ---------------------------
DEFECT_FILE = "Defect Lookup.xlsx"
FEEDBACK_FILE = "feedback_log.xlsx"
GITHUB_REPO = "your_org_or_username/your_repo_name"  # Replace with your repo

# ---------------------------
# Helper Functions
# ---------------------------
def load_defects(filename=DEFECT_FILE):
    """Always reload defects Excel file fresh (no caching). Handles missing columns."""
    try:
        df = pd.read_excel(filename)
        df.columns = [str(col).strip() for col in df.columns]

        # Ensure expected columns exist
        expected_cols = ["Setup Number", "Defect Name", "Frequency", "Preventative Suggestion"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""

        # Legacy case-insensitive cleaning (works like original version)
        df["Setup Number"] = df["Setup Number"].astype(str).str.strip().str.lower()

        # Debug: see available setups
        st.write("Available setup numbers in defects file:", df["Setup Number"].tolist())

        return df
    except Exception as e:
        st.error(f"Error loading defects file: {e}")
        st.stop()

def get_version(filename=DEFECT_FILE):
    """Read update date from Excel cell B1 safely"""
    try:
        df_version = pd.read_excel(filename, sheet_name=0, nrows=1, usecols="B", header=None)
        version = df_version.iloc[0,0]
        return str(version)
    except:
        return "unknown"

def get_defects_for_setup(df, setup_number, top_n=6):
    """Return top N defects for a setup"""
    setup_number_input = setup_number.strip().lower()
    filtered = df[df["Setup Number"] == setup_number_input]

    if filtered.empty:
        return pd.DataFrame(columns=["Defect Name", "Frequency", "Preventative Suggestion"])

    freq_order = {"High": 3, "Medium": 2, "Low": 1}
    filtered["FreqOrder"] = filtered["Frequency"].map(freq_order).fillna(0)
    filtered = filtered.sort_values(by="FreqOrder", ascending=False)

    return filtered.head(top_n)[["Defect Name", "Frequency", "Preventative Suggestion"]]

def push_feedback_to_github(df_feedback):
    """Push feedback DataFrame to GitHub as Excel"""
    token = st.secrets["GITHUB_TOKEN"]
    g = Github(token)
    repo = g.get_repo(GITHUB_REPO)

    with io.BytesIO() as output:
        df_feedback.to_excel(output, index=False)
        data = output.getvalue()

    try:
        contents = repo.get_contents(FEEDBACK_FILE)
        repo.update_file(FEEDBACK_FILE, "Update feedback log", data, contents.sha)
    except:
        repo.create_file(FEEDBACK_FILE, "Create feedback log", data)

def submit_feedback(setup_number, operator, feedback_text):
    """Submit feedback and push to GitHub"""
    entry = {
        "Setup Number": setup_number.strip(),
        "Operator": operator.strip(),
        "Feedback": feedback_text.strip(),
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        repo = g.get_repo(GITHUB_REPO)
        contents = repo.get_contents(FEEDBACK_FILE)
        df_feedback = pd.read_excel(io.BytesIO(contents.decoded_content))
        df_feedback = pd.concat([df_feedback, pd.DataFrame([entry])], ignore_index=True)
    except:
        df_feedback = pd.DataFrame([entry])

    push_feedback_to_github(df_feedback)
    st.success("Feedback submitted successfully!")

# ---------------------------
# Streamlit App
# ---------------------------
def main():
    st.set_page_config(page_title="Production Line App", layout="wide")
    st.title("📋 Production Line App")

    option = st.radio("Select an option:", ["Lookup Setup", "Setup Feedback"])

    # Always reload defects fresh
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

    st.markdown("---")
    st.markdown(f"*Updated: {updated_date}*")

if __name__ == "__main__":
    main()

