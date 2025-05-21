import os
import joblib
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from datetime import datetime
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

# Load model and preprocessing pipeline
model = joblib.load("junk_file_model.pkl")
preprocessor = joblib.load("preprocessor.pkl")

#Feature extraction
def extract_features_from_path(p):
    try:
        stat = p.stat()
        size = stat.st_size
        size_mb = size / (1024 ** 2)
        days_since_modified = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
        ext = p.suffix.lower() if p.suffix else "<none>"
        depth = len(p.parts)
        ext_len = len(ext)
        has_extension = ext != "<none>"

        return {
            "file_name": p.name,
            "size": size,
            "size_mb": size_mb,
            "log_size_mb": np.log1p(size_mb),
            "days_since_modified": days_since_modified,
            "last_modified": stat.st_mtime,
            "last_accessed": stat.st_atime,
            "depth": depth,
            "ext_len": ext_len,
            "extension": ext,
            "has_extension": has_extension,
            "is_duplicate": 0,  # not tracked live
            "is_redundant_copy": 0,  # not tracked live
            "path": str(p)
        }
    except Exception:
        return None

# Format age in a readable way
def format_age(days):
    if days < 30:
        return f"{days} days"
    elif days < 365:
        return f"{days // 30} months"
    else:
        return f"{days // 365} years"

#Main app
st.title("ML-Powered File Cleaner")

folder = st.text_input("Enter folder to scan:", value=str(Path.home() / "Downloads"))

# Session state for scanned data
if "junk_df" not in st.session_state:
    st.session_state.junk_df = None

if st.button("Scan and Predict Junk Files"):
    p = Path(folder)
    file_data = []

    with st.spinner("Scanning files..."):
        for root, _, files in os.walk(p):
            for f in files:
                path = Path(root) / f
                feats = extract_features_from_path(path)
                if feats:
                    file_data.append(feats)

    df = pd.DataFrame(file_data)
    if df.empty:
        st.warning("No readable files found.")
    else:
        df["extension"] = df["extension"].astype("category")
        X_live = df.drop(columns=["path", "file_name"])

        # Apply preprocessing pipeline
        X_transformed = preprocessor.transform(X_live)

        # Predict junk files
        df["is_junk"] = model.predict(X_transformed)
        junk_df = df[df["is_junk"] == 1].sort_values("size_mb", ascending=False)
        junk_df["file_age"] = junk_df["days_since_modified"].apply(format_age)
        junk_df["Select"] = False

        st.session_state.junk_df = junk_df
        st.success(f"Found {len(junk_df)} potential junk files.")

# Display table if available
if st.session_state.junk_df is not None:
    st.write("### Select files to delete:")
    display_df = st.session_state.junk_df.copy()
    display_df = display_df[["Select", "file_name", "extension", "file_age", "size_mb", "path"]]
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="junk_table"
    )

    to_delete = edited_df[edited_df["Select"] == True]["path"].tolist()

    if st.button("Delete Selected Junk Files") and to_delete:
        deleted = 0
        for path in to_delete:
            try:
                os.remove(path)
                deleted += 1
            except Exception:
                continue
        st.success(f"Deleted {deleted} selected files.")

    if st.button("Delete ALL Detected Junk Files"):
        if st.warning("This will permanently delete all detected junk files. Proceed with caution!"):
            confirm = st.checkbox("I understand the risk and want to delete all junk files.")
            if confirm:
                deleted_all = 0
                for path in st.session_state.junk_df["path"]:
                    try:
                        os.remove(path)
                        deleted_all += 1
                    except Exception:
                        continue
                st.success(f"Deleted {deleted_all} files in total.")