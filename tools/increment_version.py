import re
import sys
import argparse
from pathlib import Path

# --- Configuration ---
VERSION_FILE_PATH = Path("src/python/utils/_version.py")
VERSION_VARIABLE_NAME = "__version__"
# Regex to find the version string
VERSION_REGEX = r'^{0}\s*=\s*["\'](?P<version>[\d\.]+)(?P<prerelease>.*?)["\']$'.format(VERSION_VARIABLE_NAME)

def increment_version(level):
    """Reads, increments the specified version level, and writes the new version."""

    print(f"Reading version from: {VERSION_FILE_PATH}")

    # 1. Read the file content
    try:
        content = VERSION_FILE_PATH.read_text()
    except FileNotFoundError:
        print(f"Error: Version file not found at {VERSION_FILE_PATH}")
        sys.exit(1)

    # 2. Extract the version
    match = re.search(VERSION_REGEX, content, re.MULTILINE)

    if not match:
        print(f"Error: Could not find the {VERSION_VARIABLE_NAME} variable in the file.")
        sys.exit(1)

    old_line = match.group(0)
    version_number_str = match.group('version') # e.g., "0.2.1"
    prerelease_tag = match.group('prerelease') # e.g., "-alpha"

    # Split and convert to integers
    try:
        parts = list(map(int, version_number_str.split('.')))
    except ValueError:
        print(f"Error: Invalid version format detected: {version_number_str}")
        sys.exit(1)
        
    if len(parts) < 3:
        print("Error: Version string must be in major.minor.patch format (e.g., 0.2.1).")
        sys.exit(1)

    # 3. Calculate the new version based on the level
    new_parts = list(parts)
    
    if level == 'major':
        # Increment major, reset minor and patch
        new_parts[0] += 1
        new_parts[1] = 0
        new_parts[2] = 0
        # When moving to a new major version, often the prerelease tag is dropped
        # unless explicitly required (e.g., 1.0.0-beta)
        new_prerelease_tag = "" 
    elif level == 'minor':
        # Increment minor, reset patch
        new_parts[1] += 1
        new_parts[2] = 0
        new_prerelease_tag = prerelease_tag # Keep prerelease tag for minor increments
    elif level == 'patch':
        # Increment patch only
        new_parts[2] += 1
        new_prerelease_tag = prerelease_tag # Keep prerelease tag for patch increments
    else:
        print(f"Error: Invalid increment level '{level}'. Add --level 'major', 'minor', or 'patch'.")
        sys.exit(1)

    new_version_number_str = ".".join(map(str, new_parts))
    new_version = new_version_number_str + new_prerelease_tag
    
    # Create the new line for the file
    new_line = f'{VERSION_VARIABLE_NAME} = "{new_version}"'
    new_content = content.replace(old_line, new_line)

    # 4. Write the new content back
    try:
        VERSION_FILE_PATH.write_text(new_content)
        print("--- Version Update Summary ---")
        print(f"Level Incremented: **{level.upper()}**")
        print(f"  Old Version: {version_number_str}{prerelease_tag}")
        print(f"  New Version: **{new_version}**")
        print(f"File Updated: {VERSION_FILE_PATH}")
    except Exception as e:
        print(f"Error writing to file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Increment project version in _version.py.")
    parser.add_argument(
        '--level',
        choices=['major', 'minor', 'patch'],
        help="The level of the version to increment (major, minor, or patch)."
    )
    args = parser.parse_args()
    increment_version(args.level)