import streamlit as st
import pandas as pd
from datetime import datetime
import os
from github import Github

# -----------------------------
# GitHub Commit Helper
# -----------------------------
def commit_to_github(feedback_text):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        log_file = st.secrets["LOG_FILE"]

        g = Github(token)
        repo = g.get_repo(repo_name)

        # Try to fetch existing log
        try:
            contents = repo.get_contents(log_file)
            existing = contents.decoded_content.decode("utf-8")
        except Exception:
            existing = "timestamp,feedback\n"  # start fresh if missing
            contents = None

        # Append new feedback
        new_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{feedback_text.strip()}\n"
        updated = existing + new_entry

        # Commit to GitHub
        if contents:
            repo.update_file(contents.path, "Update feedback log", updated, contents.sha)
        else:
            repo.create_file(log_file, "Create feedback log", updated)

        return True, None
    except Exception as e:
        return False, str(e)


# -----------------------------
# Local File Log Helper
# -----------------------------
def log_feedback_local(feedback_text):
    log_df = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "feedback": feedback_text.strip()
    }])
    file_exists = os.path.isfile("feedback_log.csv")
    log_df.to_csv("feedback_log.csv", mode="a", header=not file_exists, index=False)


# -----------------------------
# Main App
# -----------------------------
def main():
    st.title("Defects Lookup & Feedback")

    # -----------------------------
    # Radio Options (Stable)
    # -----------------------------
    options = ["Main Menu", "Lookup Setup", "Setup Feedback"]

    if "option" in st.session_state and st.session_state["option"] not in options:
        st.session_state["option"] = "Main Menu"

    option = st.radio("Choose an option:", options, key="option")

    # -----------------------------
    # Main Menu
    # -----------------------------
    if option == "Main Menu":
        st.write("👋 Welcome! Please choose **Lookup Setup** or **Setup Feedback** above.")

    # -----------------------------
    # Lookup Setup Page
    # -----------------------------
    elif option == "Lookup Setup":
        setup_id = st.text_input("Enter Setup ID to lookup")
        if st.button("Search"):
            if setup_id.strip():
                # Replace with your real lookup logic
                st.success(f"Results for setup {setup_id}")
            else:
                st.warning("Please enter a valid Setup ID.")

        if st.button("Return to Menu"):
            st.session_state.option = "Main Menu"
            st.rerun()

    # -----------------------------
    # Feedback Page
    # -----------------------------
    elif option == "Setup Feedback":
        feedback = st.text_area("Enter your feedback:", key="feedback_text")

        if st.button("Submit Feedback"):
            if feedback.strip():
                # Local backup log
                log_feedback_local(feedback)

                # Push to GitHub
                success, err = commit_to_github(feedback)

                # Clear textarea
                st.session_state.feedback_text = ""

                if success:
                    st.success("✅ Feedback submitted successfully and logged to GitHub!")
                else:
                    st.error(f"⚠️ Feedback saved locally, but GitHub update failed: {err}")

                # Return to menu
                st.session_state.option = "Main Menu"
                st.rerun()
            else:
                st.warning("Please enter some feedback before submitting.")

        if st.button("Return to Menu"):
            st.session_state.option = "Main Menu"
            st.rerun()


if __name__ == "__main__":
    main()
