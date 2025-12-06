import subprocess
import os
import sys
import shutil
from pathlib import Path
from typing import List

# --- Configuration: Define paths relative to the project root ---
# Assumes the script is run from the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / 'documentation'
SRC_DIR = PROJECT_ROOT / 'src' / 'python'

def delete_build_dir():
    """Removes the entire _build directory."""
    build_path = DOCS_DIR / '_build'
    print(f"  Attempting to remove directory: {build_path}")
    if build_path.exists():
        try:
            # Recursively remove the directory and its contents
            shutil.rmtree(build_path)
            print(f"  Successfully removed: {build_path.name}")
        except OSError as e:
            # Handle permissions or other OS issues
            print(f"  ❌ Error removing build directory {build_path}: {e}")
            sys.exit(1)
    else:
        print(f"  Directory not found, skipping removal.")


def run_sphinx_command(command_name: str, args: List[str], cwd: Path) -> None:
    """Runs a Sphinx command (e.g., 'sphinx-apidoc', 'sphinx-build')."""

    # The command is the executable name (e.g., 'sphinx-build') followed by arguments
    command = [command_name] + args
    
    print(f"\n--- Running command in {cwd.name}/: {' '.join(command)} ---")
    
    try:
        # check=True raises an error if the command fails
        # The script relies on the active virtual environment to find 'sphinx-build'
        subprocess.run(command, cwd=cwd, check=True, capture_output=False)
    except FileNotFoundError:
        print(f"❌ Error: '{command_name}' not found. Ensure your virtual environment is active.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {command_name} execution.")
        print(f"Command failed: {e}")
        sys.exit(1)

def clean_build_internals():
    """Removes non-essential intermediate files from the _build directory."""
    print("\n--- Cleaning up non-essential files inside _build/ ---")
    
    # Paths to the non-essential directories
    doctrees_path = DOCS_DIR / '_build' / '.doctrees'
    sources_path = DOCS_DIR / '_build' / '_sources'
    buildinfo_path = DOCS_DIR / '_build' / '.buildinfo'

    for path in [doctrees_path, sources_path]:
        if path.exists():
            shutil.rmtree(path)
            print(f"  Removed intermediate directory: {path.name}")
        
    if buildinfo_path.exists():
        os.remove(buildinfo_path)
        print(f"  Removed intermediate file: {buildinfo_path.name}")
        
    print("Intermediate files cleanup complete.")

def clean_stubs():
    """Removes the temporary, generated API stub files (.rst) from the docs directory."""
    print("\n--- Cleaning up generated .rst stub files ---")
    
    # Target files to remove: python.*.rst and modules.rst
    files_to_remove = list(DOCS_DIR.glob('python.*.rst'))
    files_to_remove.append(DOCS_DIR / 'modules.rst')
        
    for path in files_to_remove:
        if path.exists():
            os.remove(path)
            print(f"  Removed: {path.name}")
        
    print("Cleanup complete.")

def build_documentation():
    # Step 1: CLEAN up previous build output using Python's shutil
    print("Step 1: Cleaning previous build output (documentation/_build)...")
    delete_build_dir()

    # Step 2: REGENERATE API stubs
    print("\nStep 2: Generating API stubs for src/python...")
    # Command: sphinx-apidoc -o . ../src/python --separate --force
    run_sphinx_command('sphinx-apidoc', ['-o', '.', '../src/python', '--separate', '--force'], cwd=DOCS_DIR)

    # Step 3: BUILD the final HTML
    print("\nStep 3: Building final HTML documentation...")
    # Command: sphinx-build -b html . _build
    run_sphinx_command('sphinx-build', ['-b', 'html', '.', '_build'], cwd=DOCS_DIR)

    clean_build_internals()
    
    # Step 4: CLEAN up generated stub files
    clean_stubs()

if __name__ == "__main__":
    try:
        build_documentation()
        print("\n=======================================================")
        print("✅ Documentation build and cleanup successful!")
        print(f"HTML output is ready in: {DOCS_DIR / '_build' / 'html'}")
        print("=======================================================")
    except Exception as e:
        print(f"\n❌ Documentation build failed due to a critical error: {e}")
        sys.exit(1)