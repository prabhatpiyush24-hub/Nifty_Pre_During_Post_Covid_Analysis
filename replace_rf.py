import os
from pathlib import Path

root = Path(r"d:\Analysis Project")
count = 0
for path in root.rglob("*.py"):
    if path.name == "replace_rf.py":
        continue
    try:
        content = path.read_text(encoding="utf-8")
        if "Rf=0%" in content:
            new_content = content.replace("Rf=0%", "Rf=6.5%")
            path.write_text(new_content, encoding="utf-8")
            print(f"Updated {path.name}")
            count += 1
    except Exception as e:
        print(f"Error on {path}: {e}")

print(f"Done. Updated {count} files.")
