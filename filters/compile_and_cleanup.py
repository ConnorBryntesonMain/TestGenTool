import os
import subprocess
import platform

def compile_test_file(test_file):
    """Attempts to compile a C++ test file. Returns True if successful, False otherwise."""
    output_exe = test_file.replace(".cpp", "")
    if platform.system() == "Windows":
        output_exe += ".exe"
        
    # Basic compilation command
    compile_command = [
        "mpic++",
        test_file,
        "-o",
        output_exe,
        "-std=c++11"
    ]
    
    # Add MPI flags only if MPI is likely available (check for mpicc)
    try:
        # Check if MPI is installed by looking for mpicc
        mpi_check = subprocess.run(
            ["which", "mpicc"] if platform.system() != "Windows" else ["where", "mpicc"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if mpi_check.returncode == 0:
            compile_command.extend(["-I/usr/include/mpi", "-lmpi"])
    except:
        # MPI not found, continue without MPI flags
        pass

    # Add coverage flags for gcov compatibility
    compile_command.extend(["-fprofile-arcs", "-ftest-coverage"])

    try:
        result = subprocess.run(
            compile_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(f"Compiled: {test_file} -> {output_exe}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to compile: {test_file}")
        error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
        print(f"Error: {error_message}")
        return False


def cleanup_failed_tests(path):
    """Compiles and removes failed test files. Accepts either a directory or a single file."""

    if os.path.isfile(path):
        # If a single file is provided, check and clean it
        test_files = [path] if path.endswith("_test.cpp") else []
    elif os.path.isdir(path):
        # If a directory is provided, find all test files
        test_files = [
            os.path.join(path, f) for f in os.listdir(path) if f.endswith("_test.cpp")
        ]
    else:
        print(f"Invalid path: {path}")
        return 0  # Return 0 to indicate no tests were processed

    total_tests = len(test_files)
    removed_tests = 0

    for test_file in test_files:
        output_exe = test_file.replace(".cpp", "")  # Executable name
        if platform.system() == "Windows":
            output_exe += ".exe"
            
        if not compile_test_file(test_file):
            if os.path.exists(test_file):
                os.remove(test_file)
                print(f"Removed test file: {test_file}")

            if os.path.exists(output_exe):
                os.remove(output_exe)
                print(f"Removed compiled binary: {output_exe}")

            removed_tests += 1

    print(f"\nTotal test files checked: {total_tests}")
    print(f"Total test files removed: {removed_tests}")
    return removed_tests


if __name__ == "__main__":
    test_path = "cloned_repo"  # Default directory
    
    # Check if directory exists, create if not
    if not os.path.exists(test_path):
        os.makedirs(test_path)
        print(f"Created directory: {test_path}")
        print("No test files found to process.")
    else:
        cleanup_failed_tests(test_path)