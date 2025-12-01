import re
import sys
import argparse
from pathlib import Path

# --- Configuration ---
VERSION_FILE_PATH = Path("src/python/utils/_version.py")
VERSION_VARIABLE_NAME = "__version__"
# Regex to find the version string
VERSION_REGEX = r'^{0}\s*=\s*["\'](?P<version>[\d\.]+)(?P<prerelease>.*?)["\']$'.format(VERSION_VARIABLE_NAME)

def increment_version(level, custom_prerelease):
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
    
    # Determine the index to increment: 0=major, 1=minor, 2=patch
    level_map = {'major': 0, 'minor': 1, 'patch': 2}
    if level not in level_map:
        print(f"Error: Invalid increment level '{level}'. Choose 'major', 'minor', or 'patch'.")
        sys.exit(1)
        
    level_index = level_map[level]
    
    # Increment the specified part and reset lower parts
    new_parts[level_index] += 1
    for i in range(level_index + 1, 3):
        new_parts[i] = 0

    # Determine the new pre-release tag
    if custom_prerelease is not None:
        # Use the custom tag provided by the user
        new_prerelease_tag = f"-{custom_prerelease}" if custom_prerelease else ""
    elif level == 'major' and not prerelease_tag:
        # If major is incremented and no current prerelease tag exists, keep it empty.
        new_prerelease_tag = ""
    elif level == 'major' and prerelease_tag:
        # If major is incremented and a prerelease tag exists, drop it by default (release version).
        new_prerelease_tag = ""
    else:
        # For minor/patch increments, keep the existing tag
        new_prerelease_tag = prerelease_tag


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
    parser.add_argument(
        '--prerelease',
        type=str,
        nargs='?', # Allows the flag to be present without a value
        const='',  # If the flag is present but no value is given, treat it as an empty string (remove tag)
        default=None, # If the flag is not present at all, use default logic (keep tag)
        help="Set a new pre-release tag (e.g., 'beta'). Use --prerelease='' to remove the tag."
    )
    args = parser.parse_args()
    increment_version(args.level, args.prerelease)