import webbrowser
from pathlib import Path
import sys
import os

def view_documentation():
    """Locates and opens the index.html file in the default web browser."""
    
    # Define paths relative to the script's location (tools/)
    PROJECT_ROOT = Path(__file__).parent.parent
    INDEX_HTML_PATH = PROJECT_ROOT / 'docs' / 'api' / '_build' / 'index.html'

    print("--- Attempting to open documentation in browser ---")

    if not INDEX_HTML_PATH.exists():
        print(f"❌ Error: Documentation file not found at: {INDEX_HTML_PATH}")
        print("Please run 'python tools/build_docs.py' first to generate the HTML.")
        sys.exit(1)

    try:
        # Use file:// URI scheme for local files
        url = 'file:///' + os.path.abspath(INDEX_HTML_PATH).replace('\\', '/')
        webbrowser.open_new_tab(url)
        print(f"✅ Opening documentation in default browser: {url}")
        
    except Exception as e:
        print(f"❌ Failed to open browser automatically. Please open the following path manually:")
        print(os.path.abspath(INDEX_HTML_PATH))
        print(f"Error details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    view_documentation()