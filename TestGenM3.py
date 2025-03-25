import os
import subprocess
import openai
from filters.compile_and_cleanup import cleanup_failed_tests, compile_test_file
from filters.test_coverage_comparison import measure_coverage, remove_low_coverage_tests

# Retrieve OpenAI API key from environment variables
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clone_repo(repo_url, clone_dir):
    """Clones the given GitHub repository into the specified directory."""
    if not os.path.exists(clone_dir):
        subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    else:
        print(f"Repository already cloned at {clone_dir}.")


def find_cpp_c_files(directory):
    """Finds all .cpp and .c files in the cloned repository that contain '_ref' in their filename."""
    cpp_c_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if "_ref" in file and (file.endswith(".cpp") or file.endswith(".c")):
                cpp_c_files.append(os.path.join(root, file))
    return cpp_c_files


def generate_test_file(file_path):
    """Creates a test file with a placeholder if it does not exist."""
    if file_path.endswith(".cpp"):
        test_file_path = file_path.replace("_ref.cpp", "_ref_test.cpp")
    elif file_path.endswith(".c"):
        test_file_path = file_path.replace("_ref.c", "_ref_test.c")
    else:
        return None

    if not os.path.exists(test_file_path):
        with open(test_file_path, "w") as tf:
            tf.write("// Auto-generated test file\n")
        print(f"Created test file: {test_file_path}")
    else:
        print(f"Test file already exists: {test_file_path}")

    return test_file_path


def generate_unit_tests(source_file, test_file):
    """Uses OpenAI's API to generate unit tests that increase coverage."""
    with open(source_file, "r") as sf:
        source_content = sf.read()

    with open(test_file, "r") as tf:
        test_content = tf.read()

    prompt = f"""
    I am working on generating tests with AI that add to coverage and that compile and run right after generation. 

    Generate only C++ unit tests that improve coverage for the function in the provided file. 
    **Do NOT include explanations, comments, or descriptions**—only output valid compilable C++ test code.

    For this, the generation must follow these steps:

    Step 1: Confirm the method signature from provided files.
    Step 2: Generate code explicitly based on confirmed signatures.
    Step 3: Flag missing or ambiguous information.
    Step 4: Suggest tests or static assertions to validate behavior.
    Step 5: Output well-documented, assumption-free code.
    Step 6: Ensure the code generated will increase coverage.

    # Environment Constraints:
    - Use Linux MPI system for compatibility.
    - The code must be compatible with the Linux MPI system setup, initializing and finalizing MPI correctly.
    - Only use existing files that I provide.
    
    Ensure that everything being generated is able to compile.

    # Source File:
    
    {source_content}
    

    # Existing Test File:
    
    {test_content}
        
    Generate additional unit tests that meet the requirements. 
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an AI that generates comprehensive unit tests for C/C++ code using the Linux MPI system.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    generated_tests = response.choices[0].message.content

    with open(test_file, "a") as tf:
        tf.write("\n// Auto-generated tests\n")
        tf.write(generated_tests)

    print(f"Unit tests generated for {source_file}")


def main(repo_url, clone_dir, single_file=None):
    clone_repo(repo_url, clone_dir)
    cpp_c_files = find_cpp_c_files(clone_dir)

    if single_file:
        cpp_c_files = [single_file] if single_file in cpp_c_files else []

    if not cpp_c_files:
        print(" No matching source files found.")
        return

    # Step 1: Verify that existing test files compile before anything else
    for source_file in cpp_c_files:
        test_file = source_file.replace(".cpp", "_test.cpp")
        if os.path.exists(test_file):
            print(f"🔍 Checking if existing test compiles: {test_file}")
            if not compile_test_file(test_file):
                print(
                    f" Existing test file '{test_file}' does not compile. Fix before proceeding."
                )
                return  # Stop execution if a test doesn't compile

    # Step 2: Measure initial coverage (only if existing tests compile)
    print("\n📏 Measuring initial coverage...")
    before_covered, before_total = measure_coverage(clone_dir, "Before")

    # Step 3: Generate new unit tests
    test_files = [generate_test_file(file) for file in cpp_c_files]
    test_files = [file for file in test_files if file]  # Remove None values

    if not test_files:
        print(" No test files were successfully created.")
        return

    for source_file, test_file in zip(cpp_c_files, test_files):
        generate_unit_tests(source_file, test_file)

    # Step 4: Compile new tests and remove failures
    print("\n🛠 Compiling new test files and removing any that fail...")
    if single_file:
        cleanup_failed_tests(single_file)
    else:
        cleanup_failed_tests(clone_dir)

    # Step 5: Measure final coverage
    print("\n📏 Measuring final coverage...")
    after_covered, after_total = measure_coverage(clone_dir, "After")

    # Step 6: Remove low-impact tests
    removed_tests = remove_low_coverage_tests(clone_dir, before_covered, before_total)

    coverage_diff = after_covered - before_covered
    print(f"\n Test Coverage Improvement: {coverage_diff} more lines covered.")
    print(f" Total tests removed for low coverage impact: {removed_tests}")


if __name__ == "__main__":
    repo_url = "https://github.com/hpcg-benchmark/hpcg.git"
    clone_dir = "cloned_repo"

    # Specify a single file or set to None for all files
    single_file = "cloned_repo/src/ComputeSPMV_ref.cpp"

    main(repo_url, clone_dir, single_file)
