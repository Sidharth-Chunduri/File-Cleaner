import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
import joblib

# Configuration
INPUT_CSV = "file_dataset_20250520_202205.csv"
DROP_COLS = ["path", "last_modified_str", "last_accessed_str", "sha256"]
TARGET_COL = "is_junk"

# Load data
print("Loading dataset...")
df = pd.read_csv(INPUT_CSV, dtype={"sha256": str})

# Clean data
print("Cleaning and engineering features...")
df["extension"] = df["extension"].fillna("<none>").astype("category")
df["has_extension"] = df["extension"] != "<none>"
df["size_mb"] = df["size"] / (1024 ** 2)
df["log_size_mb"] = np.log1p(df["size_mb"])
df["days_since_modified"] = (
    pd.Timestamp.now() - pd.to_datetime(df["last_modified"], unit="s")
).dt.days
df["ext_len"] = df["extension"].str.len().fillna(0).astype(int)
df["is_duplicate"] = df["is_duplicate"].astype(int)
df["is_redundant_copy"] = df["is_redundant_copy"].astype(int)

# Prepare data
X = df.drop(columns=DROP_COLS + [TARGET_COL])
y = df[TARGET_COL]

# Define preprocessing
categorical_features = ["extension"]
numeric_features = [col for col in X.columns if col not in categorical_features]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ],
    remainder="passthrough"  # leave numeric columns as-is
)

# Build full pipeline
clf_pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(class_weight="balanced", random_state=42))
])

# Split data train/test
print("Splitting dataset...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, stratify=y, test_size=0.2, random_state=42
)

# Train model
print("Training model...")
clf_pipeline.fit(X_train, y_train)

# Evaluate
print("Evaluation:")
y_pred = clf_pipeline.predict(X_test)
print(classification_report(y_test, y_pred))

# Save model and preprocessor separately
print("Saving model and preprocessor...")
joblib.dump(clf_pipeline.named_steps["classifier"], "junk_file_model.pkl")
joblib.dump(clf_pipeline.named_steps["preprocessor"], "preprocessor.pkl")

print("Done!")
