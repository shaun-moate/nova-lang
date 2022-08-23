#!/usr/bin/env python3
## TODO: implement tox/poetry to manage virtual environment for python
## TODO: consider migration to go-lang support implementation of static typing
## TODO: implement OOP for readability (TestCase, Stats, etc.)

import subprocess
import sys
import os

NOVA_EXT = ".nv"
COMPILE_FAIL = 0
COMPILE_FAILURE_LIST = []
SIMULATE_FAIL = 0
SIMULATE_FAILURE_LIST = []

def uncons(xs):
    return (xs[0], xs[1:])

def usage(program):
    print("-------------------------------------------")
    print("Usage: %s <SUBCOMMAND> [ARGS]" % program)
    print("SUBCOMMANDS:")
    print("    --generate <dir>       Iterate through each test and store outputs")
    print("    --help                 Provide usage details")
    print("    --run      <dir>       Iterate through each test, providing back aggregate success/failures")
    print("-------------------------------------------")
    exit(1)

def generate_all_test_cases(input_directory: str):
   assert os.path.isdir(input_directory), "ERROR: path must be a directory"
   for file in os.listdir(input_directory):
       f = os.path.join(input_directory, file)
       if os.path.isfile(f) and f.endswith(".nv"):
           generate_test_case(f)

def generate_test_case(input_file_path: str):
    output_file_path = str(input_file_path[:-len(NOVA_EXT)])
    print("[INFO] building %s: build/output" % (input_file_path))
    build = subprocess.run(["./nova.py", "-c", input_file_path], stdout=subprocess.DEVNULL)
    print("[INFO] generating test case file: %s -> %s" % (input_file_path, output_file_path))
    result = subprocess.run(["build/output"], capture_output=True, text=True)
    with open(output_file_path, "w") as file:
        file.write(":returncode %s\n" % (result.returncode))
        file.write(":stdout %d\n%s" % (len(result.stdout), result.stdout))

def run_all_test_cases(input_directory: str):
   assert os.path.isdir(input_directory), "ERROR: path must be a directory"
   for file in os.listdir(input_directory):
       f = os.path.join(input_directory, file)
       if os.path.isfile(f) and f.endswith(".nv"):
           run_test_case(f)
   print("[INFO] failed test cases: simulated = %d, compiled = %d" % (SIMULATE_FAIL, COMPILE_FAIL))
   if len(SIMULATE_FAILURE_LIST) > 0:
       print("[INFO] for reference, following simulated test cases failed:\n%s" % (SIMULATE_FAILURE_LIST))
       exit(1)
   if len(COMPILE_FAILURE_LIST) > 0:
       print("[INFO] for reference, following compiled test cases failed:\n%s" % (COMPILE_FAILURE_LIST))
       exit(1)

def run_test_case(input_file_path: str):
   global COMPILE_FAIL
   global COMPILE_FAILURE_LIST
   global SIMULATE_FAIL
   global SIMULATE_FAILURE_LIST
   print("[INFO] running test case: %s == %s" % (input_file_path, str(input_file_path[:-len(NOVA_EXT)])))
   if compile_test_case(input_file_path) == load_test_case(input_file_path):
      print("[PASS] compilation of test case PASSED: %s" % (input_file_path))
   else:
      print("[FAIL] compilation test case FAILED: %s" % (input_file_path))
      COMPILE_FAIL += 1
      COMPILE_FAILURE_LIST.append(input_file_path)
   if simulate_test_case(input_file_path) == load_test_case(input_file_path):
      print("[PASS] simulation of test case PASSED: %s" % (input_file_path))
   else:
      print("[FAIL] simulation test case FAILED: %s" % (input_file_path))
      SIMULATE_FAIL += 1
      SIMULATE_FAILURE_LIST.append(input_file_path)

def compile_test_case(input_file_path: str):
    build = subprocess.run(["./nova.py", "-c", input_file_path], stdout=subprocess.DEVNULL)
    result = subprocess.run(["build/output"], capture_output=True, text=True)
    return str(result.returncode) + result.stdout

def simulate_test_case(input_file_path: str):
    result = subprocess.run(["./nova.py", "-s" , input_file_path], capture_output=True, text=True)
    return str(result.returncode) + result.stdout

def load_test_case(input_file_path: str):
    test_case_file_path = str(input_file_path[:-len(NOVA_EXT)])
    with open(test_case_file_path, "r") as file:
       while True:
          line = file.readline()
          if line.startswith(":returncode"):
             returncode = line[-2]
          elif line.startswith(":stdout"):
             stdout_len = int(line[8:-1])
             stdout = file.read(stdout_len)
          elif not line:
             break
       return returncode + stdout

if __name__ == '__main__':
    argv = sys.argv
    assert len(argv) >= 1
    (program, argv) = uncons(argv)
    if len(argv) < 1:
        print("ERROR: no subcommand has been provided")
        usage(program)
    (subcommand, argv) = uncons(argv)
    if subcommand == "--generate" or subcommand == "-g":
        if len(argv) < 1:
            print("ERROR: no input directory to generate test cases")
            usage(program)
        (input_directory, argv) = uncons(argv)
        generate_all_test_cases(input_directory)
    elif subcommand == "--run" or subcommand == "-r":
        if len(argv) < 1:
            print("ERROR: no input directory to run test cases")
            usage(program)
        (input_directory, argv) = uncons(argv)
        ## run_all_test_cases(input_directory)
        run_all_test_cases(input_directory)
    elif subcommand == "--help":
        usage(program)
    else:
        print("ERROR: unknown nova subcommand '%s'" % (subcommand))
        usage(program)
