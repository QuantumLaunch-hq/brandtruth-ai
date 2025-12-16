#!/usr/bin/env python3
"""Test runner script for BrandTruth AI."""

import argparse
import subprocess
import sys


def run_tests(test_type: str = "all", verbose: bool = True, coverage: bool = False):
    """Run tests with specified options."""
    cmd = ["pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # Add test type filter
    if test_type == "unit":
        cmd.append("tests/unit")
    elif test_type == "integration":
        cmd.append("tests/integration")
    elif test_type == "e2e":
        cmd.extend(["-m", "e2e", "tests/e2e"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    # "all" runs everything
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="BrandTruth AI Test Runner")
    parser.add_argument(
        "type",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "e2e", "fast"],
        help="Type of tests to run",
    )
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Run with coverage report",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode (less verbose)",
    )
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  BRANDTRUTH AI TEST RUNNER                  ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    exit_code = run_tests(
        test_type=args.type,
        verbose=not args.quiet,
        coverage=args.coverage,
    )
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
