import os
import subprocess
import openai
from filters.compile_and_cleanup import cleanup_failed_tests
from filters.test_coverage_comparison import measure_coverage, remove_low_coverage_tests
# Retrieve OpenAI API key from environment variables
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clone_repo(repo_url, clone_dir):
    """Clones the given GitHub repository into the specified directory."""
    subprocess.run(['git', 'clone', repo_url, clone_dir], check=True)

def find_cpp_c_files(directory):
    """Finds all .cpp and .c files in the cloned repository that contain '_ref' in their filename."""
    cpp_c_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if ('_ref' in file) and (file.endswith('.cpp') or file.endswith('.c')):
                cpp_c_files.append(os.path.join(root, file))
    return cpp_c_files

def generate_test_file(file_path):
    """Creates a basic test file template for a given C/C++ source file."""
    # Ensure '_test' is added only once and correctly formatted
    if file_path.endswith('.cpp'):
        test_file_path = file_path.replace('_ref.cpp', '_ref_test.cpp')
    elif file_path.endswith('.c'):
        test_file_path = file_path.replace('_ref.c', '_ref_test.c')
    else:
        return None

def generate_unit_tests(source_file, test_file):
    """Uses OpenAI's API to generate unit tests that increase coverage."""
    with open(source_file, 'r') as sf:
        source_content = sf.read()
    
    with open(test_file, 'r') as tf:
        test_content = tf.read()

    prompt = f"""
    I am working on generating tests with AI that add to coverage and that compile and run right after generation. 
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

    # Source File:
    ```
    {source_content}
    ```

    # Existing Test File:
    ```
    {test_content}
    ```

    When giving comments to explain test ensure that they are in comments to allow for complie.
    
    Generate additional unit tests that meet the requirements. 
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an AI that generates comprehensive unit tests for C/C++ code using the Linux MPI system."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    generated_tests = response.choices[0].message.content

    with open(test_file, 'a') as tf:
        tf.write("\n// Auto-generated tests\n")
        tf.write(generated_tests)

    print(f"Unit tests generated for {source_file}")


def main(repo_url, clone_dir):
    clone_repo(repo_url, clone_dir)
    cpp_c_files = find_cpp_c_files(clone_dir)
    test_files = []

    # Generate test files
    for file_path in cpp_c_files:
        generate_test_file(file_path, test_files)
    
    # Generate unit tests
    for source_file, test_file in zip(cpp_c_files, test_files):
        generate_unit_tests(source_file, test_file)

    print("\nMeasuring initial coverage...")
    before_covered, before_total = measure_coverage(clone_dir, "Before")

    # Run the compile and cleanup script to remove failed tests
    cleanup_failed_tests(clone_dir)

    print("\nMeasuring final coverage...")
    after_covered, after_total = measure_coverage(clone_dir, "After")

    # Remove low-coverage tests
    removed_tests = remove_low_coverage_tests(clone_dir, before_covered, before_total)

    coverage_diff = after_covered - before_covered
    print(f"\nTest Coverage Improvement: {coverage_diff} more lines covered.")
    print(f"Total tests removed for low coverage impact: {removed_tests}")

if __name__ == '__main__':
    repo_url = 'https://github.com/hpcg-benchmark/hpcg.git'  # Example repo URL
    clone_dir = 'cloned_repo'
    main(repo_url, clone_dir)