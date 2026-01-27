import subprocess
import os
import sys
import argparse
import re

def compile_resources():
    """
    Compiles the .qrc file into a Python resource file and patches
    it for PySide6 compatibility.
    """
    # Define paths relative to the project root
    # Project structure: tools/compile_resources.py -> ../
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    qrc_file = os.path.join(root_dir, "resources", "resources.qrc")
    output_dir = os.path.join(root_dir, "src", "python")
    output_file = os.path.join(output_dir, "resources_rc.py")

    # Ensure source QRC exists
    if not os.path.exists(qrc_file):
        print(f"Error: Resource file not found at {qrc_file}")
        return

    # Ensure output directory exists (important for fresh clones)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    print(f"--- Compiling {qrc_file} ---")

    # 1. Run the pyside6-rcc command
    try:
        subprocess.run(
            ["pyside6-rcc", qrc_file, "-o", output_file],
            check=True,
        )
        print(f"Successfully compiled to: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during compilation: {e}")
        return
    except FileNotFoundError:
        print("Error: 'pyside6-rcc' not found. Please install PySide6 (pip install PySide6).")
        return

def clean_resources():
    """Removes generated resource files matching .gitignore patterns."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    generated_files = [
        os.path.join(root_dir, "src", "python", "resources_rc.py"),
        os.path.join(root_dir, "src", "python", "resources_rc.pyclear")
    ]
    
    for file_path in generated_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Qt resource compilation.")
    parser.add_argument("--clean", action="store_true", help="Remove generated resource files.")
    
    args = parser.parse_args()
    
    if args.clean:
        clean_resources()
    else:
        compile_resources()
