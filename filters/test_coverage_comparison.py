import os
import subprocess

COVERAGE_THRESHOLD = 2.5  # Minimum % increase required for a test file to stay

def run_coverage(directory):
    """Runs gcov on all C/C++ source files and returns coverage data."""
    coverage_command = ["gcov", "-b", "-c"]
    test_files = [f for f in os.listdir(directory) if f.endswith(".cpp") or f.endswith(".c")]

    total_lines = 0
    covered_lines = 0

    for test_file in test_files:
        test_path = os.path.join(directory, test_file)
        try:
            subprocess.run(["g++", "-fprofile-arcs", "-ftest-coverage", test_path, "-o", "test_exec"],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["./test_exec"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(coverage_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            with open(f"{test_file}.gcov", "r") as gcov_file:
                for line in gcov_file:
                    if "#####:" in line or line.strip().startswith("-:"):
                        total_lines += 1
                    elif line.strip().split(":")[0].isdigit():
                        covered_lines += 1
                        total_lines += 1

        except subprocess.CalledProcessError:
            print(f"Failed to analyze coverage for: {test_file}")

    return covered_lines, total_lines

def measure_coverage(directory, phase):
    """Measures test coverage and saves results."""
    covered, total = run_coverage(directory)
    coverage_percent = (covered / total * 100) if total > 0 else 0
    print(f"{phase} Coverage: {covered}/{total} lines covered ({coverage_percent:.2f}%)")
    return covered, total

def remove_low_coverage_tests(directory, before_covered, before_total):
    """Removes test files that do not increase coverage by at least 2.5%."""
    test_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith("_test.cpp")]
    removed_tests = 0

    for test_file in test_files:
        after_covered, after_total = run_coverage(directory)
        before_coverage = (before_covered / before_total * 100) if before_total > 0 else 0
        after_coverage = (after_covered / after_total * 100) if after_total > 0 else 0
        improvement = after_coverage - before_coverage

        if improvement < COVERAGE_THRESHOLD:
            os.remove(test_file)
            removed_tests += 1
            print(f"Removed {test_file} (Coverage increase: {improvement:.2f}%)")

    return removed_tests

if __name__ == "__main__":
    test_dir = "cloned_repo"  # Adjust directory as needed

    print("\nMeasuring initial coverage...")
    before_covered, before_total = measure_coverage(test_dir, "Before")

    # The program should now generate tests and check compilation before continuing.

    print("\nMeasuring final coverage...")
    after_covered, after_total = measure_coverage(test_dir, "After")

    removed_tests = remove_low_coverage_tests(test_dir, before_covered, before_total)

    coverage_diff = after_covered - before_covered
    print(f"\nTest Coverage Improvement: {coverage_diff} more lines covered.")
    print(f"Total tests removed for low coverage impact: {removed_tests}")
