import os
import re
from datetime import datetime

# Configuration: Which files to update
DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs')
TARGET_FILES = [
    "SCHEMA.md",
    "CPP_BRIDGE.md",
    "TODO.md",
    "fruchterman-reingold.md",
    "NarrativeForgeProjectFolder.md"
]

def update_timestamp(file_path):
    current_date = datetime.now().strftime("%Y-%m-%d")
    timestamp_line = f"\n\n*Last Updated: {current_date}*"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to find an existing timestamp (even with different dates)
    pattern = r'\n*\*Last Updated: \d{4}-\d{2}-\d{2}\*'
    
    if re.search(pattern, content):
        # Update existing
        new_content = re.sub(pattern, timestamp_line, content)
        print(f"✅ Updated: {os.path.basename(file_path)}")
    else:
        # Append new
        new_content = content.strip() + timestamp_line
        print(f"➕ Added: {os.path.basename(file_path)}")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == "__main__":
    print("🕒 Updating Documentation Timestamps...")
    for filename in TARGET_FILES:
        full_path = os.path.join(DOCS_DIR, filename)
        if os.path.exists(full_path):
            update_timestamp(full_path)
        else:
            print(f"⚠️  Skipped: {filename} (File not found)")