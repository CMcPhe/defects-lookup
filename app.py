import streamlit as st
import pandas as pd
import os
from datetime import datetime

# -----------------------------
# Load defects file
# -----------------------------
def load_defects(file_path):
    try:
        df = pd.read_excel(file_path)

        # Schema check
        required_cols = ["Setup Number", "Defect Name", "Frequency", "Preventative Suggestion"]
        for col in required_cols:
            if col not in df.columns:
                st.error(f"❌ Missing required column: {col}")
                return None, None

        # Read version/date if present
        version = "Unknown"
        if "Version" in df.columns:
            version = df["Version"].dropna().astype(str).iloc[0]
        elif "B1" in df:  # fallback
            version = df.iloc[0, 1]

        return df, version
    except Exception as e:
        st.error(f"Error loading defects file: {e}")
        return None, None

# -----------------------------
# Lookup function with debug
# -----------------------------
def get_defects_for_setup(df, setup_number, top_n=6):
    setup_number_input = setup_number.strip().lower()

    # Debug: show first 10 raw setup numbers
    st.write("🔍 Debug - First 10 setup numbers in file:", 
             [repr(x) for x in df["Setup Number"].head(10).tolist()])

    # Debug: show your input clearly
    st.write("🔍 Debug - Your input:", repr(setup_number_input))

    # Normalize
    df["SetupNorm"] = df["Setup Number"].astype(str).str.strip().str.lower()

    # Debug: unique normalized values
    st.write("🔍 Debug - Unique normalized setup numbers:", 
             [repr(x) for x in df["SetupNorm"].unique().tolist()])

    # Filter
    filtered = df[df["SetupNorm"] == setup_number_input]

    if filtered.empty:
        st.error(f"❌ Debug - No rows matched '{setup_number_input}'")
    else:
        st.write("✅ Debug - Matching rows found:", filtered)

    if filtered.empty:
        return pd.DataFrame(columns=["Defect Name", "Frequency", "Preventative Suggestion"])

    # Sort by frequency
    freq_order = {"High": 3, "Medium": 2, "Low": 1}
    filtered["FreqOrder"] = filtered["Frequency"].map(freq_order).fillna(0)
    filtered = filtered.sort_values(by="FreqOrder", ascending=False)

    return filtered.head(top_n)[["Defect Name", "Frequency", "Preventative Suggestion"]]

# -----------------------------
# Feedback logging
# -----------------------------
def log_feedback(setup_number, operator_name, feedback_text, log_file="feedback_log.xlsx"):
    entry = {
        "Setup Number": setup_number,
        "Operator": operator_name,
        "Feedback": feedback_text,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if os.path.exists(log_file):
        existing = pd.read_excel(log_file)
        updated = pd.concat([existing, pd.DataFrame([entry])], ignore_index=True)
    else:
        updated = pd.DataFrame([entry])

    updated.to_excel(log_file, index=False)

# -----------------------------
# Streamlit App
# -----------------------------
def main():
    st.title("📊 Production Line Defect Lookup & Feedback")

    file_path = "Defect Lookup.xlsx"
    df, version = load_defects(file_path)

    if df is None:
        st.stop()

    st.sidebar.success(f"✅ Data last updated: {version}")

    # Landing page options
    option = st.radio("Choose an option:", ["Lookup Setup", "Setup Feedback"])

    setup_number = st.text_input("Enter Setup Number:")

    if option == "Lookup Setup" and setup_number:
        results = get_defects_for_setup(df, setup_number)
        if results.empty:
            st.warning("No defects found for this setup.")
        else:
            st.subheader(f"Top Defects for Setup {setup_number}")
            st.table(results)

    elif option == "Setup Feedback" and setup_number:
        operator_name = st.text_input("Enter Operator Name:")
        feedback_text = st.text_area("Enter your feedback here:")
        if st.button("Submit Feedback"):
            if operator_name and feedback_text:
                log_feedback(setup_number, operator_name, feedback_text)
                st.success("✅ Feedback submitted successfully!")
            else:
                st.error("❌ Please provide both operator name and feedback text.")

if __name__ == "__main__":
    main()

