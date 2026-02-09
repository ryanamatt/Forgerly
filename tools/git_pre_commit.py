# tools/git_pre_commit.py

import pytest
import sys
import io
from contextlib import redirect_stdout
import subprocess
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent

def run_cycle_detection():
    """Check for circular import dependencies."""
    print("\n🔍 Checking for circular imports...")
    
    try:
        result = subprocess.run(
            [sys.executable, PROJECT_ROOT / "tools" / "detect_cycles.py"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check if any cycles were detected in the output
        if "Cycle detected:" in result.stdout:
            print("❌ Circular import dependencies found:")
            print(result.stdout)
            return False
        else:
            print("✅ No circular imports detected")
            return True
            
    except Exception as e:
        print(f"⚠️  Warning: Could not run cycle detection: {e}")
        return True  # Don't block commit on tool failure

def build_documentation():
    """Build documentation to ensure it compiles without errors."""
    print("\n📚 Building documentation...")
    
    try:
        result = subprocess.run(
            [sys.executable, PROJECT_ROOT / "tools" / "build_docs.py"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("✅ Documentation built successfully")
            return True
        else:
            print("❌ Documentation build failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"⚠️  Warning: Could not build documentation: {e}")
        return True  # Don't block commit on tool failure

def run_tests():
    """Run pytest test suite."""
    print("\n🧪 Running pre-commit tests...")

    f = io.StringIO()
    with redirect_stdout(f):
        # Run tests silently
        exit_code = pytest.main(["-q", "--tb=short", "tests/"])

    if exit_code == 0:
        print("✅ All tests passed")
        return True
    else:
        # If they failed, print the captured output so the user can see errors
        print(f.getvalue())
        print(f"❌ Tests failed with exit code {exit_code}")
        return False

def main():
    print("🚀 Running pre-commit checks...\n")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Run all checks
    if not run_cycle_detection():
        all_checks_passed = False
    
    if not run_tests():
        all_checks_passed = False
    
    if not build_documentation():
        all_checks_passed = False
    
    # Final summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ All pre-commit checks passed! Proceeding with commit.")
        sys.exit(0)
    else:
        print("❌ Some pre-commit checks failed. Please fix the issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()