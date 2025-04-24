import os
import subprocess
import platform

def compile_test_file(test_file):
    """Compiles the test file with appropriate flags."""
    try:
        source_dir = os.path.dirname(test_file)
        build_dir = os.path.join(os.path.dirname(source_dir), "build")
        
        # Check if there's a CMake or Make build system
        has_cmake = os.path.exists(os.path.join(os.path.dirname(source_dir), "CMakeLists.txt"))
        has_make = os.path.exists(os.path.join(os.path.dirname(source_dir), "Makefile"))
        
        # Extract compiler and flags from build system
        compiler = "mpicxx"  # Default for MPI C++ programs
        flags = ["-g", "-O0", "--coverage", "-fprofile-arcs", "-ftest-coverage"]
        
        if has_cmake and os.path.exists(build_dir):
            # Try to extract compiler from CMake cache
            cmake_cache = os.path.join(build_dir, "CMakeCache.txt")
            if os.path.exists(cmake_cache):
                with open(cmake_cache, 'r') as f:
                    for line in f:
                        if line.startswith("CMAKE_CXX_COMPILER:"):
                            compiler = line.split('=')[1].strip()
                        if line.startswith("CMAKE_CXX_FLAGS:"):
                            extra_flags = line.split('=')[1].strip()
                            flags.extend(extra_flags.split())
        
        elif has_make:
            # Try to extract compiler from Makefile
            with open(os.path.join(os.path.dirname(source_dir), "Makefile"), 'r') as f:
                makefile = f.read()
                if "CXX =" in makefile:
                    for line in makefile.split('\n'):
                        if line.strip().startswith("CXX ="):
                            compiler = line.split('=')[1].strip()
                        if line.strip().startswith("CXXFLAGS ="):
                            extra_flags = line.split('=')[1].strip()
                            flags.extend(extra_flags.split())
        
        # Remove optimization flags that might interfere with coverage
        flags = [flag for flag in flags if not flag.startswith('-O') or flag == '-O0']
        
        # Add include directories
        include_dirs = []
        for root, dirs, files in os.walk(os.path.dirname(source_dir)):
            for d in dirs:
                if d.lower() in ['include', 'inc', 'headers']:
                    include_dirs.append(os.path.join(root, d))
        
        include_flags = [f"-I{d}" for d in include_dirs]
        
        # Compile the test file
        output_file = test_file.replace(".cpp", "") if test_file.endswith(".cpp") else test_file.replace(".c", "")
        
        cmd = [compiler] + flags + include_flags + ["-o", output_file, test_file]
        print(f"Compiling with: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            return False
        
        return True
    except Exception as e:
        print(f"Error compiling test file: {str(e)}")
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