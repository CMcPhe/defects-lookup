import streamlit as st
import pandas as pd
import datetime
import base64
from github import Github, GithubException

# -------------------
# Configuration
# -------------------
DEFECTS_FILE = "Defect Lookup.xlsx"   # file with defect data
LOG_FILE = "feedback_log.xlsx"        # file where feedback is stored
REPO_NAME = "YOUR_GITHUB_USERNAME/YOUR_REPO_NAME"  # update with your repo
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]          # stored in Streamlit secrets


# -------------------
# Load Defects Data
# -------------------
def load_defects():
    try:
        # Row 2 (B2) = revision date
        revision_date = pd.read_excel(DEFECTS_FILE, header=None).iloc[1, 1]

        # Actual defect data starts row 3 → skip first 2 rows
        df = pd.read_excel(DEFECTS_FILE, skiprows=2)

        # Normalize column names
        df.columns = df.columns.str.strip()

        if "Setup Number" not in df.columns:
            st.error("❌ 'Setup Number' column missing in defect file.")
            return None, None

        return df, revision_date
    except Exception as e:
        st.error(f"Error loading defects file: {e}")
        return None, None


# -------------------
# GitHub Write Feedback
# -------------------
def log_feedback_to_github(setup, operator, feedback, repo_name, log_file, token, retries=1):
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)

        # Current timestamp
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Load existing log if present
        try:
            contents = repo.get_contents(log_file)
            df_existing = pd.read_excel(base64.b64decode(contents.content))
        except GithubException:
            df_existing = pd.DataFrame(columns=["Date", "Setup Number", "Operator", "Feedback"])

        # Append new row
        new_entry = pd.DataFrame(
            [[now, setup, operator, feedback]],
            columns=["Date", "Setup Number", "Operator", "Feedback"]
        )
        df_updated = pd.concat([df_existing, new_entry], ignore_index=True)

        # Convert to bytes
        from io import BytesIO
        buffer = BytesIO()
        df_updated.to_excel(buffer, index=False)
        data = buffer.getvalue()

        # Try update with retries
        for _ in range(retries + 1):
            try:
                contents = repo.get_contents(log_file)
                repo.update_file(
                    path=log_file,
                    message=f"Add feedback for setup {setup}",
                    content=data,
                    sha=contents.sha,
                    branch="main"
                )
                return True, None
            except GithubException:
                try:
                    repo.create_file(
                        path=log_file,
                        message=f"Create feedback log and add feedback for setup {setup}",
                        content=data,
                        branch="main"
                    )
                    return True, None
                except Exception as e2:
                    error_msg = str(e2)
        return False, error_msg
    except Exception as e:
        return False, str(e)


# -------------------
# Streamlit App
# -------------------
def main():
    st.title("Defect Lookup & Feedback")

    # Initialize session state
    for key in ["operator", "feedback", "setup_number", "option", "feedback_submitted"]:
        if key not in st.session_state:
            st.session_state[key] = "" if key != "feedback_submitted" else False

    # Load defects
    defects_df, revision_date = load_defects()

    # Options
    option = st.radio(
        "Choose an option:",
        ["Lookup Setup", "Setup Feedback"],
        key="option"
    )

    # -------------------
    # Lookup Setup
    # -------------------
    if option == "Lookup Setup" and defects_df is not None:
        setup_number = st.text_input("Enter Setup Number:", key="setup_number")

        if setup_number:
            setup_number = setup_number.strip().lower()
            results = defects_df[defects_df["Setup Number"].str.lower() == setup_number]

            if not results.empty:
                st.subheader(f"Defects for Setup {setup_number.upper()}")
                st.table(results[["Defect", "Description", "Prevention"]].head(6))
            else:
                st.warning(f"No defects found for setup '{setup_number}'.")

    # -------------------
    # Setup Feedback
    # -------------------
    elif option == "Setup Feedback":
        setup_number_fb = st.text_input("Enter Setup Number (optional):", key="setup_number_fb")
        operator = st.text_input("Operator Name:", key="operator")
        feedback = st.text_area("Feedback:", key="feedback")

        if st.button("Submit Feedback"):
            if operator.strip() and feedback.strip():
                success, error_msg = log_feedback_to_github(
                    setup_number_fb if setup_number_fb.strip() else "N/A",
                    operator,
                    feedback,
                    REPO_NAME,
                    LOG_FILE,
                    GITHUB_TOKEN,
                    retries=1
                )
                if success:
                    st.session_state["feedback_submitted"] = True
                    # Clear inputs
                    st.session_state["operator"] = ""
                    st.session_state["feedback"] = ""
                    st.session_state["setup_number_fb"] = ""
                    st.rerun()
                else:
                    st.error(f"❌ Failed to submit feedback: {error_msg}")
            else:
                st.error("❌ Please provide operator name and feedback.")

    # -------------------
    # After rerun → show confirmation
    # -------------------
    if st.session_state.get("feedback_submitted", False):
        st.success("✅ Feedback submitted successfully!")
        st.session_state["feedback_submitted"] = False

    # -------------------
    # Show revision date
    # -------------------
    if revision_date is not None:
        st.markdown(f"*Data last updated: {revision_date}*")


if __name__ == "__main__":
    main()
