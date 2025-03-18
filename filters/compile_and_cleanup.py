import os
import subprocess

def compile_test_file(test_file):
    """Attempts to compile a C++ test file. Returns True if successful, False otherwise."""
    output_exe = test_file.replace(".cpp", "")
    compile_command = ["g++", test_file, "-o", output_exe, "-std=c++11", "-I/usr/include/mpi", "-lmpi"]

    try:
        subprocess.run(compile_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def cleanup_failed_tests(directory):
    """Finds and compiles all test files, deleting those that fail."""
    test_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith("_test.cpp")]

    total_tests = len(test_files)
    removed_tests = 0

    for test_file in test_files:
        if not compile_test_file(test_file):
            os.remove(test_file)
            removed_tests += 1
            print(f"Removed: {test_file}")

    print(f"\nTotal test files checked: {total_tests}")
    print(f"Total test files removed: {removed_tests}")

if __name__ == "__main__":
    test_dir = "cloned_repo"  # Adjust directory as needed
    cleanup_failed_tests(test_dir)