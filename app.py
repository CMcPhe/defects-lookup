import streamlit as st
import pandas as pd
from datetime import datetime
from github import Github
import io
import time
from zoneinfo import ZoneInfo


# -----------------------------
# Load defects file
# -----------------------------
def load_defects(file_path):
    try:
        df = pd.read_excel(file_path, header=1)
        required_cols = ["Setup Number", "Defect Name", "Frequency", "Preventative Suggestion"]
        for col in required_cols:
            if col not in df.columns:
                st.error(f"❌ Missing required column: {col}")
                return None, None
        raw_version = pd.read_excel(file_path, header=None).iloc[0, 1]
        version = str(raw_version) if pd.notna(raw_version) else "Unknown"
        return df, version
    except Exception as e:
        st.error(f"Error loading defects file: {e}")
        return None, None

# -----------------------------
# Defect lookup
# -----------------------------
def get_defects_for_setup(df, setup_number, top_n=6):
    setup_number_input = setup_number.strip().lower()
    df["SetupNorm"] = df["Setup Number"].astype(str).str.strip().str.lower()
    filtered = df[df["SetupNorm"] == setup_number_input]
    if filtered.empty:
        return pd.DataFrame(columns=["Defect Name", "Frequency", "Preventative Suggestion"])
    freq_order = {"High": 3, "Medium": 2, "Low": 1}
    filtered["FreqOrder"] = filtered["Frequency"].map(freq_order).fillna(0)
    filtered = filtered.sort_values(by="FreqOrder", ascending=False)
    return filtered.head(top_n)[["Defect Name", "Frequency", "Preventative Suggestion"]]

# -----------------------------
# Feedback logging to GitHub
# -----------------------------
def log_feedback_to_github(setup_number, operator_name, feedback_text, repo_name, log_file, token, retries=1):
    entry = {
        "Setup Number": setup_number,
        "Operator": operator_name,
        "Feedback": feedback_text,
        "Date": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M:%S")
    }
    g = Github(token)
    repo = g.get_repo(repo_name)

    last_exception = None
    for attempt in range(retries + 1):
        try:
            contents = repo.get_contents(log_file)
            existing = pd.read_excel(io.BytesIO(contents.decoded_content))
            updated = pd.concat([existing, pd.DataFrame([entry])], ignore_index=True)
            with io.BytesIO() as output:
                updated.to_excel(output, index=False)
                repo.update_file(log_file,
                                 f"Update feedback log ({datetime.now().isoformat()})",
                                 output.getvalue(),
                                 contents.sha)
            return True, ""
        except Exception as e:
            last_exception = e
            time.sleep(1)
            continue

    try:
        df_feedback = pd.DataFrame([entry])
        with io.BytesIO() as output:
            df_feedback.to_excel(output, index=False)
            repo.create_file(log_file, f"Create feedback log ({datetime.now().isoformat()})", output.getvalue())
        return True, ""
    except Exception as e2:
        last_exception = e2

    return False, f"GitHub write error: {last_exception}"

# -----------------------------
# Streamlit App
# -----------------------------
def main():
    st.title("📊 Buffering Line Setup & Feedback")

    # -----------------------------
    # Load defect data
    # -----------------------------
    df, version = load_defects("Defect Lookup.xlsx")
    if df is None:
        st.stop()

    st.sidebar.success(f"✅ Data last updated: {version}")

    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")
    REPO_NAME = st.secrets.get("REPO_NAME")
    LOG_FILE = st.secrets.get("LOG_FILE", "feedback_log.xlsx")

    # -----------------------------
    # Landing choice
    # -----------------------------
    option = st.radio(
        "Choose an option:",
        ["Lookup Setup", "Setup Feedback"]
    )

    # -----------------------------
    # Lookup section
    # -----------------------------
    if option == "Lookup Setup":
        setup_number = st.text_input("Enter Setup Number:")
        if setup_number:
            results = get_defects_for_setup(df, setup_number)
            if results.empty:
                st.warning("No defects found for this setup.")
            else:
                st.subheader(f"Top Defects for Setup {setup_number}")
                st.table(results)

    # -----------------------------
    # Feedback section using st.form
    # -----------------------------
    elif option == "Setup Feedback":
        with st.form("feedback_form", clear_on_submit=True):
            setup_number_fb = st.text_input("Enter Setup Number:")
            operator = st.text_input("Enter Operator Name:")
            feedback = st.text_area("Enter your feedback here:")

            submitted = st.form_submit_button("Submit Feedback")

            if submitted:
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
                        st.success("✅ Feedback submitted successfully!")
                    else:
                        st.error(f"❌ Failed to submit feedback: {error_msg}")
                else:
                    st.error("❌ Please provide operator name and feedback.")


if __name__ == "__main__":
    main()


















