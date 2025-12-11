"""NAS Scan Analysis Script."""
import json
from collections import Counter
from pathlib import Path

# Load scan result
with open("D:/AI/claude01/wsoptv_v2_db/nas_scan_result.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]

# Classify
folders = [i for i in items if i["is_directory"]]
files = [i for i in items if not i["is_directory"]]
hidden_files = [f for f in files if f["name"].startswith(".")]
visible_files = [f for f in files if not f["name"].startswith(".")]

# Calculate sizes
total_size = sum(f["size_bytes"] for f in files)
hidden_size = sum(f["size_bytes"] for f in hidden_files)
visible_size = sum(f["size_bytes"] for f in visible_files)

print("=" * 70)
print("NAS SCAN RESULT")
print("=" * 70)
print(f"Folders: {len(folders)}")
print(f"Files: {len(files)}")
print(f"Total Size: {total_size:,} bytes ({total_size / (1024**4):.2f} TB)")
print()
print("=" * 70)
print("FILE CLASSIFICATION")
print("=" * 70)
print(f"Visible Files (saved to DB): {len(visible_files)} files")
print(f"  Size: {visible_size:,} bytes ({visible_size / (1024**4):.2f} TB)")
print()
print(f"Hidden Files (excluded from DB): {len(hidden_files)} files")
print(f"  Size: {hidden_size:,} bytes ({hidden_size / (1024**2):.2f} MB)")
print()

# Hidden file types
hidden_types = Counter()
for f in hidden_files:
    if f["name"] == ".DS_Store":
        hidden_types[".DS_Store (macOS folder metadata)"] += 1
    elif f["name"].startswith("._"):
        hidden_types["._* (Apple Double resource fork)"] += 1
    else:
        hidden_types[f"Other: {f['name']}"] += 1

print("=" * 70)
print(f"HIDDEN FILE TYPES ({len(hidden_files)} files)")
print("=" * 70)
for t, c in hidden_types.most_common():
    print(f"  {t}: {c}")
print()

print("=" * 70)
print("HIDDEN FILE SAMPLES (first 30)")
print("=" * 70)
for f in hidden_files[:30]:
    print(f"  {f['path']}")
if len(hidden_files) > 30:
    print(f"  ... and {len(hidden_files) - 30} more hidden files")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Expected from Windows Explorer: 1,948 files, 198 folders, 19.5 TB")
print(f"NAS Scan Result:                {len(files)} files, {len(folders)} folders, {total_size / (1024**4):.2f} TB")
print()
print(f"DB Storage (excluding hidden):  {len(visible_files)} files")
print(f"Hidden files excluded:          {len(hidden_files)} files")
print(f"Match: {len(files)} - {len(hidden_files)} = {len(visible_files)} (DB count)")
