import os
import time
import hashlib
import pandas as pd
from pathlib import Path

#Configuration. Change these to your directories which are highly populated by junk files.
TARGET_DIRS = [
    r"C:\Users\chund\Downloads",
    r"C:\Users\chund\Documents",
    r"C:\Users\chund\Desktop",
    r"C:\Users\chund\AppData\Local\Temp",
    r"C:\Users\chund\AppData\Local",
    r"C:\Users\chund\AppData\Roaming",
    r"C:\ProgramData",
    r"C:\Temp"
]

EXCLUDE_PATTERNS = [r"\WindowsApps", r"\Packages"]
JUNK_EXTS = {'.tmp', '.log', '.lnk', '.bak', '.dmp', '.old', '.cache'}
JUNK_KEYWORDS = {'cache', 'temp', 'install', 'log', 'debug', 'crash', 'setup'}

MAX_SIZE_MB = 500
MIN_HASH_MB = 0.01
MAX_HASH_MB = 50
HASH_LIMIT_PER_DIR = 10000


#Helper functions
def should_skip_dir(path):
    path_lower = path.lower()
    return any(p.lower() in path_lower for p in EXCLUDE_PATTERNS)

def compute_file_hash(path):
    try:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

#Scans directories
def scan_directory(dir_path):
    print(f"\n Scanning: {dir_path}")
    start_time = time.time()

    file_data = []
    file_count = 0
    hash_count = 0

    for root, dirs, files in os.walk(dir_path, topdown=True):
        if should_skip_dir(root):
            dirs[:] = []
            continue
        for name in files:
            full_path = os.path.join(root, name)
            file_count += 1
            if file_count % 50 == 0:
                print(f"  → Processed {file_count} files...")

            try:
                p = Path(full_path).resolve()
                stat = p.stat()
                size_mb = stat.st_size / (1024 ** 2)

                # Hashing logic
                do_hash = (MIN_HASH_MB < size_mb < MAX_HASH_MB) and (hash_count < HASH_LIMIT_PER_DIR)
                file_hash = None
                if do_hash and stat.st_size > 0:
                    file_hash = compute_file_hash(p)
                    if file_hash:
                        hash_count += 1

                file_data.append({
                    "path": str(p),
                    "size": stat.st_size,
                    "last_modified": stat.st_mtime,
                    "last_accessed": stat.st_atime,
                    "extension": p.suffix.lower(),
                    "depth": len(p.parts) - 1,
                    "sha256": file_hash
                })
            except (PermissionError, OSError) as e:
                if not isinstance(e, PermissionError) and getattr(e, "winerror", None) != 1920:
                    print(f"[ERROR] {e} → {file_path}")
                continue

    print(f" Finished scanning {dir_path} — {file_count} files in {time.time() - start_time:.2f}s")
    return file_data


#Heuristic labeling
def heuristic_label(row):
    ext = row["extension"]
    path = row["path"].lower()
    if ext in JUNK_EXTS:
        return 1
    if any(keyword in path for keyword in JUNK_KEYWORDS):
        return 1
    return 0


#Main execution
def collect_all_data():
    full_dataset = []
    for path in TARGET_DIRS:
        full_dataset.extend(scan_directory(path))

    df = pd.DataFrame(full_dataset)

    # Heuristic junk labeling
    df["is_junk"] = df.apply(heuristic_label, axis=1)

    # Timestamps
    df["last_modified_str"] = pd.to_datetime(df["last_modified"], unit="s")
    df["last_accessed_str"] = pd.to_datetime(df["last_accessed"], unit="s")

    # FIX: Only compute duplicates for files with valid hashes
    df["is_duplicate"] = False
    df["is_redundant_copy"] = False

    has_hash = df["sha256"].notna()
    df.loc[has_hash, "is_duplicate"] = df[has_hash].duplicated(subset="sha256", keep=False)
    df.loc[has_hash, "is_redundant_copy"] = df[has_hash].duplicated(subset="sha256", keep="first")

    # Save
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_file = f"file_dataset_{timestamp}.csv"
    df.to_csv(out_file, index=False)

    print(f"\n Scan complete. {len(df)} files saved to {out_file}")
    print(f" Junk files: {df['is_junk'].sum()}")
    print(f" Valid duplicates: {df['is_duplicate'].sum()} (based only on hashed files)")
    print(f" Files without hash: {df['sha256'].isna().sum()}")

if __name__ == "__main__":
    collect_all_data()
