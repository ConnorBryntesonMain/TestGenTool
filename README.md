# Test Generation and Coverage System

## Overview

This project is focused on automating the process of generating unit tests for C/C++ codebases. It aims to increase test coverage and ensure that generated tests compile and run successfully. The system uses the OpenAI API to generate unit tests and checks the code coverage both before and after the tests are added. It also removes any tests that do not contribute meaningfully to the overall coverage.

The initial implementation focuses on the [High Performance Conjugate Gradient (HPCG)](https://github.com/hpcg-benchmark/hpcg) benchmark program. HPCG is a stable, well-established legacy program that is widely used for performance benchmarking in high-performance computing (HPC) environments. The focus on HPCG allows for testing and improving the tool in a well-tested, real-world codebase before expanding to other projects in the future.

## Purpose

The goal of this system is to automate the generation and validation of unit tests in order to:

- **Increase test coverage**: By generating unit tests based on existing code, this system ensures that more of the code is tested and verified.
- **Ensure correctness**: The system ensures that the generated tests compile and run successfully, improving the overall quality of the codebase.
- **Remove low-coverage tests**: The system automatically identifies and removes tests that do not meaningfully improve test coverage by over 2.5%.

Initially, this system is focused on testing the HPCG benchmark program, but the design allows for easy expansion to other C/C++ codebases in the future.

## Features

- **Test Generation**: Automatically generates unit tests for C/C++ files using the OpenAI API.
- **Test Compilation**: Tests are compiled and checked for correctness.
- **Coverage Measurement**: The system measures code coverage before and after the tests are added.
- **Test Cleanup**: Low-coverage tests (below a 2.5\% increase in coverage) are removed automatically.
- **Integration with HPCG**: Specifically designed for the HPCG benchmark program, ensuring compatibility with a real-world, stable codebase.

## Why HPCG?

HPCG is chosen as the initial codebase for several reasons:

- **Legacy Stability**: HPCG is a widely recognized and stable benchmark program, making it an ideal candidate for testing this system.
- **Real-World Use**: By focusing on HPCG, the system is working with a codebase that is already used for benchmarking high-performance computing systems. This provides practical value from the get-go.
- **Scalability**: The system is designed to be scalable and can be adapted to work with other C/C++ codebases in the future. Expanding beyond HPCG will be straightforward once the system is proven in this context.

## Future Expansion

While the current focus is on HPCG, this system is designed with future growth in mind. In the future, it can be adapted to generate and validate unit tests for a variety of C/C++ codebases, especially in high-performance computing and other scientific computing domains.

## Requirements

To run the system, you will need:

- Python 3.7 or higher
- The following Python dependencies:
  - `openai>=1.0.0`
- A C/C++ compiler (such as GCC) for compiling test files
- `gcov` for measuring code coverage
- Git for cloning the repositories

You can install the required Python dependencies with:

```bash
pip install -r requirements.txt
