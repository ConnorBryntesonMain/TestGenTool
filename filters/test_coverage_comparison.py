import os
import subprocess
import shutil

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
                    if "#####:" in line:  # Uncovered lines
                        total_lines += 1
                    elif line.strip().startswith("-:"):  # Non-executable lines
                        pass  # Don't count these in coverage
                    elif line.strip().split(":")[0].isdigit():  # Covered lines
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
    test_files = [f for f in os.listdir(directory) if f.endswith("_test.cpp")]
    removed_tests = 0
    base_coverage = (before_covered / before_total * 100) if before_total > 0 else 0
    
    # Create a temp directory to test each file's impact
    temp_dir = os.path.join(directory, "temp_coverage_test")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Copy all files to temp directory
    for file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file)):
            shutil.copy(os.path.join(directory, file), os.path.join(temp_dir, file))
    
    for test_file in test_files:
        # Remove the test file from temp directory
        test_path = os.path.join(temp_dir, test_file)
        if os.path.exists(test_path):
            os.rename(test_path, test_path + ".bak")  # Temporarily rename instead of deleting
            
            # Measure coverage without this test
            temp_covered, temp_total = run_coverage(temp_dir)
            temp_coverage = (temp_covered / temp_total * 100) if temp_total > 0 else 0
            
            # Calculate how much this test contributes
            contribution = base_coverage - temp_coverage
            
            # Restore the file for next iteration
            os.rename(test_path + ".bak", test_path)
            
            # If contribution is below threshold, remove from actual directory
            if contribution < COVERAGE_THRESHOLD:
                actual_test_path = os.path.join(directory, test_file)
                os.remove(actual_test_path)
                removed_tests += 1
                print(f"Removed {test_file} (Coverage contribution: {contribution:.2f}%)")
    
    # Clean up
    shutil.rmtree(temp_dir)
    return removed_tests

if __name__ == "__main__":
    test_dir = "cloned_repo"  # Adjust directory as needed
    
    # Check if directory exists
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"Created directory: {test_dir}")
    
    print("\nMeasuring initial coverage...")
    before_covered, before_total = measure_coverage(test_dir, "Before")

    # Placeholder for test generation
    print("\nNote: Test generation code should be added here.")
    # You could import and call a test generation function, e.g.:
    # from test_generator import generate_tests
    # generate_tests(test_dir)
    
    # Compile tests
    print("\nCompiling tests...")
    from compile_and_cleanup import cleanup_failed_tests
    cleanup_failed_tests(test_dir)

    print("\nMeasuring final coverage...")
    after_covered, after_total = measure_coverage(test_dir, "After")

    removed_tests = remove_low_coverage_tests(test_dir, before_covered, before_total)

    coverage_diff = (after_covered / after_total * 100 if after_total > 0 else 0) - (before_covered / before_total * 100 if before_total > 0 else 0)
    print(f"\nTest Coverage Improvement: {coverage_diff:.2f}% increase")
    print(f"Total tests removed for low coverage impact: {removed_tests}")
