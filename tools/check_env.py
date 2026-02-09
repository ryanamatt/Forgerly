# tools/check_env.py

import sys
import subprocess
import shutil

def check_command(cmd, version_arg="--version"):
    path = shutil.which(cmd)
    if not path:
        return False, "Not Found"
    try:
        result = subprocess.run([cmd, version_arg], capture_output=True, text=True)
        version = result.stdout.split('\n')[0] or result.stderr.split('\n')[0]
        return True, version.strip()
    except Exception:
        return True, "Found (Version check failed)"

def run_diagnostics():
    print("--- Forgerly Development Environment Diagnostic ---")
    
    # Check Python
    print(f"Platform: {sys.platform} (Arch: {sys.maxsize.bit_length() + 1}-bit)")
    
    # Check Compiler
    cpp_ok, cpp_ver = check_command("g++")
    print(f"C++ Compiler (g++): {cpp_ver if cpp_ok else '❌ MISSING'}")
    
    # Check Build Tools
    make_ok, make_ver = check_command("make")
    print(f"Make: {make_ver if make_ok else '❌ MISSING'}")
    
    # Check Dependencies
    try:
        import PySide6
        print(f"PySide6: {PySide6.__version__}")
    except ImportError:
        print("PySide6: ❌ MISSING")

    try:
        import cffi
        print(f"CFFI: {cffi.__version__}")
    except ImportError:
        print("CFFI: ❌ MISSING (Required for C++ Bridge)")

    print("\nDiagnostic complete.")

if __name__ == "__main__":
    run_diagnostics()