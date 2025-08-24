#!/usr/bin/env python3
"""
Test runner script for the RAG system tests.
Usage: python test_runner.py [options]
"""

import sys
import subprocess
from pathlib import Path


def run_tests(coverage=True, verbose=True, pattern=None):
    """Run the test suite with optional coverage and filtering"""
    
    # Change to the project root directory
    project_root = Path(__file__).parent.parent.parent
    
    cmd = ["uv", "run", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=backend",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    # Add test path
    cmd.append("backend/tests/")
    
    if pattern:
        cmd.extend(["-k", pattern])
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RAG system tests")
    parser.add_argument("--no-coverage", action="store_true", 
                       help="Skip coverage reporting")
    parser.add_argument("--quiet", action="store_true", 
                       help="Run tests in quiet mode")
    parser.add_argument("-k", "--pattern", 
                       help="Run only tests matching the pattern")
    parser.add_argument("--api-only", action="store_true", 
                       help="Run only API endpoint tests")
    
    args = parser.parse_args()
    
    pattern = args.pattern
    if args.api_only:
        pattern = "test_api_endpoints"
    
    success = run_tests(
        coverage=not args.no_coverage,
        verbose=not args.quiet,
        pattern=pattern
    )
    
    sys.exit(0 if success else 1)