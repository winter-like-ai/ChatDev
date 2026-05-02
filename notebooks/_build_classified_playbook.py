"""
Build script for build_classified_playbook.ipynb.
Usage: python notebooks/_build_classified_playbook.py
"""
import json

CELL = []

def md(source):
    CELL.append({"cell_type": "markdown", "metadata": {}, "source": source.split("\n")})

def code(source):
    CELL.append({"cell_type": "code", "metadata": {}, "source": source.split("\n"),
                 "outputs": [], "execution_count": None})

# ============================================================
# Cell 0: Title
# ============================================================
md("""# Build Classified Playbook Dataset

Converts every `.log` file under `data/classified_chatdev/trajectory/` into
a playbook JSON using `log_to_playbook`, then distributes copies into
bug-category subdirectories mirroring the original `classified_chatdev` layout.

**Output:**
- `data/classified_chatdev_playbook/` — playbook dataset (same structure as classified_chatdev)
- `data/classified_chatdev_api_record/` — intermediate api_records.jsonl (for bug_detector node_index)

**Setup:** Run cells in order. The first cell configures paths.""")

# ============================================================
# Cell 1: Configuration
# ============================================================
code("""# Configuration

SOURCE_DIR  = "data/classified_chatdev"          # original dataset
PLAYBOOK_DIR = "data/classified_chatdev_playbook" # new playbook dataset
API_DIR      = "data/classified_chatdev_api_record" # intermediate api_records

import os, shutil
from pathlib import Path

for d in [PLAYBOOK_DIR, API_DIR]:
    os.makedirs(d, exist_ok=True)

print(f"SOURCE_DIR:   {os.path.abspath(SOURCE_DIR)}")
print(f"PLAYBOOK_DIR: {os.path.abspath(PLAYBOOK_DIR)}")
print(f"API_DIR:      {os.path.abspath(API_DIR)}")""")

# ============================================================
# Cell 2: Imports
# ============================================================
code("""import json, sys, time
from pathlib import Path
from collections import defaultdict

_project_root = Path(os.getcwd()).resolve()
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from chatdev.analyzer.log_to_playbook import log_to_playbook
from chatdev.analyzer.log_to_api import log_to_api_records

print("All imports OK")""")

# ============================================================
# Cell 3: Step 1 — Discover files and category mapping
# ============================================================
md("""## Step 1: Discover Logs & Category Mapping

Scans `classified_chatdev`:
- All `.log` files live under `trajectory/`.
- Numbered subdirectories (`0.0`, `1.1`, ... `3.3`) contain parsed `.json`
  copies categorised by bug type.  We use these to know which playbook
  belongs in which category.""")

# ============================================================
# Cell 4: Discovery
# ============================================================
code("""# ---- Find all .log files ----
trajectory_dir = os.path.join(SOURCE_DIR, "trajectory")
log_files = sorted(Path(trajectory_dir).glob("*.log"))
print(f"Found {len(log_files)} .log files in trajectory/")

# ---- Build category -> [log_name] mapping ----
# Each numbered subdirectory contains .json files whose stem matches a .log name
category_map = defaultdict(list)   # log_stem -> [category, ...]
all_categories = []

for entry in sorted(os.listdir(SOURCE_DIR)):
    cat_dir = os.path.join(SOURCE_DIR, entry)
    if not os.path.isdir(cat_dir) or entry == "trajectory":
        continue
    all_categories.append(entry)
    for fname in os.listdir(cat_dir):
        if fname.endswith(".json"):
            stem = fname[:-5]  # remove .json
            category_map[stem].append(entry)

# Build reverse: category -> [stems]
cat_to_stems = defaultdict(list)
for stem, cats in category_map.items():
    for c in cats:
        cat_to_stems[c].append(stem)

print(f"Categories: {sorted(all_categories)}")
print(f"Unique log stems referenced: {len(category_map)}")
for cat in sorted(all_categories):
    stems = cat_to_stems.get(cat, [])
    print(f"  {cat}: {len(stems)} entries")""")

# ============================================================
# Cell 5: Step 2 — Generate playbooks for all trajectory logs
# ============================================================
md("""## Step 2: Generate Playbooks from Trajectory Logs

For every `.log` in `trajectory/`, run `log_to_playbook` and save:
- `{name}_playbook.json` -> `classified_chatdev_playbook/trajectory/`
- api_records.jsonl -> `classified_chatdev_api_record/trajectory/`""")

# ============================================================
# Cell 6: Process trajectory
# ============================================================
code("""# ---- Create output trajectory directories ----
pb_traj = os.path.join(PLAYBOOK_DIR, "trajectory")
api_traj = os.path.join(API_DIR, "trajectory")
os.makedirs(pb_traj, exist_ok=True)
os.makedirs(api_traj, exist_ok=True)

success = 0
fail = 0
errors = []

for i, log_path in enumerate(log_files):
    name = log_path.stem
    pb_out = os.path.join(pb_traj, f"{name}_playbook.json")
    api_out = os.path.join(api_traj, f"{name}_api_records.jsonl")

    try:
        # Generate playbook (api_records is created alongside the log by default)
        log_to_playbook(str(log_path), output_path=pb_out, keep_api_records=True)

        # Move api_records.jsonl to API_DIR (it was created next to the log)
        default_api = log_path.parent / "api_records.jsonl"
        if default_api.exists():
            shutil.move(str(default_api), api_out)

        success += 1
        if (i + 1) % 20 == 0 or (i + 1) == len(log_files):
            print(f"  [{i+1}/{len(log_files)}] {success} ok, {fail} fail")
    except Exception as e:
        fail += 1
        errors.append((name, str(e)))
        print(f"  [{i+1}/{len(log_files)}] FAIL {name}: {e}")

print(f"\\nTrajectory processing: {success} success, {fail} fail")
if errors:
    print("Errors:")
    for name, err in errors:
        print(f"  - {name}: {err}")""")

# ============================================================
# Cell 7: Step 3 — Distribute playbooks to category subdirectories
# ============================================================
md("""## Step 3: Distribute to Category Subdirectories

For each bug-category directory, copy the relevant playbooks from
`trajectory/` and the matching `api_records.jsonl`.""")

# ============================================================
# Cell 8: Distribute
# ============================================================
code("""# ---- Distribute playbooks and api_records to category dirs ----
for cat in sorted(all_categories):
    stems = cat_to_stems.get(cat, [])
    if not stems:
        print(f"  {cat}: 0 entries (skip)")
        continue

    pb_cat_dir = os.path.join(PLAYBOOK_DIR, cat)
    api_cat_dir = os.path.join(API_DIR, cat)
    os.makedirs(pb_cat_dir, exist_ok=True)
    os.makedirs(api_cat_dir, exist_ok=True)

    copied = 0
    for stem in stems:
        src_pb = os.path.join(pb_traj, f"{stem}_playbook.json")
        src_api = os.path.join(api_traj, f"{stem}_api_records.jsonl")

        if os.path.exists(src_pb):
            shutil.copy2(src_pb, os.path.join(pb_cat_dir, f"{stem}_playbook.json"))
        if os.path.exists(src_api):
            shutil.copy2(src_api, os.path.join(api_cat_dir, f"{stem}_api_records.jsonl"))
        copied += 1

    print(f"  {cat}: {copied} playbooks distributed")

print("\\nDistribution complete")""")

# ============================================================
# Cell 9: Step 4 — Summary
# ============================================================
md("""## Step 4: Summary & Verification

Count files in each output directory to verify the dataset is complete.""")

# ============================================================
# Cell 10: Summary
# ============================================================
code("""# ---- Verify output ----
def count_files(root_dir):
    counts = {}
    for entry in sorted(os.listdir(root_dir)):
        p = os.path.join(root_dir, entry)
        if os.path.isdir(p):
            n = len([f for f in os.listdir(p)
                     if f.endswith(".json") or f.endswith(".jsonl")])
            counts[entry] = n
    return counts

print("=== classified_chatdev_playbook ===")
pb_counts = count_files(PLAYBOOK_DIR)
total_pb = sum(pb_counts.values())
for cat, n in sorted(pb_counts.items()):
    print(f"  {cat}: {n} playbooks")
print(f"  TOTAL: {total_pb}")

print()
print("=== classified_chatdev_api_record ===")
api_counts = count_files(API_DIR)
total_api = sum(api_counts.values())
for cat, n in sorted(api_counts.items()):
    print(f"  {cat}: {n} api_records")
print(f"  TOTAL: {total_api}")

print()
print(f"Playbook dataset: {os.path.abspath(PLAYBOOK_DIR)}")
print(f"API records:      {os.path.abspath(API_DIR)}")
print("\\nDataset build complete!")""")

# ============================================================
# Write notebook
# ============================================================
notebook = {
    "cells": CELL,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.9.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

output_path = "notebooks/build_classified_playbook.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"Generated: {output_path}")
print(f"  {len(CELL)} cells")
