import re
import sys
import argparse
from pathlib import Path

# --- Configuration ---
# Define targets: (File Path, Regex to find version)
TARGETS = [
    (
        Path("src/python/utils/_version.py"), 
        r'^__version__\s*=\s*["\'](?P<version>[\d\.]+)(?P<prerelease>.*?)["\']$'
    ),
    (
        Path("pyproject.toml"), 
        r'^version\s*=\s*["\'](?P<version>[\d\.]+)(?P<prerelease>.*?)["\']$'
    )
]

def increment_version(level, custom_prerelease):
    """Increments version in all configured target files."""
    
    for file_path, regex in TARGETS:
        if not file_path.exists():
            print(f"Warning: File not found at {file_path}. Skipping.")
            continue

        print(f"Processing: {file_path}")
        content = file_path.read_text()
        match = re.search(regex, content, re.MULTILINE)

        if not match:
            print(f"Error: Could not find version pattern in {file_path}")
            continue

        old_line = match.group(0)
        version_number_str = match.group('version')
        prerelease_tag = match.group('prerelease')

        # Logic for incrementing (same as your original)
        try:
            parts = list(map(int, version_number_str.split('.')))
        except ValueError:
            print(f"Error: Invalid format in {file_path}: {version_number_str}")
            sys.exit(1)

        new_parts = list(parts)
        level_map = {'major': 0, 'minor': 1, 'patch': 2}
        level_index = level_map[level]
        
        new_parts[level_index] += 1
        for i in range(level_index + 1, 3):
            new_parts[i] = 0

        # Prerelease logic
        if custom_prerelease is not None:
            new_prerelease_tag = f"-{custom_prerelease}" if custom_prerelease else ""
        elif level == 'major':
            new_prerelease_tag = ""
        else:
            new_prerelease_tag = prerelease_tag

        new_version_str = ".".join(map(str, new_parts)) + new_prerelease_tag
        
        # Build the new line while preserving the key (variable name or TOML key)
        # We replace only the version part within the matched line
        key_name = "__version__" if "_version.py" in str(file_path) else "version"
        new_line = f'{key_name} = "{new_version_str}"'
        
        new_content = content.replace(old_line, new_line)
        file_path.write_text(new_content)
        print(f"  Updated {version_number_str}{prerelease_tag} -> **{new_version_str}**")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Increment project version in multiple files.")
    parser.add_argument('--level', choices=['major', 'minor', 'patch'], required=True)
    parser.add_argument('--prerelease', type=str, nargs='?', const='', default=None)
    
    args = parser.parse_args()
    increment_version(args.level, args.prerelease)