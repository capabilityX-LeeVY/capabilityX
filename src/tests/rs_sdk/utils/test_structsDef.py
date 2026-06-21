import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from core.structsDef import TestCase, TestSuite,TestCaseBatch

# file = "navigations/basic/sign_in"
# case = TestCase()
# case.from_yaml_file_Relative_path(file)
# print(case.__dict__)

# path = "/Volumes/Data/Code/WebexRegressSheild/src/test_space/test_cases"
# for root, dirs, files in os.walk(path):
#     for file in files:
#         if file.endswith(".yaml"):
#             file_path = os.path.join(root, file)
#             case = TestCase()
#             case.from_yaml_file(file_path)
           

# path = "/Volumes/Data/Code/WebexRegressSheild/src/test_space/test_suites"
# for root, dirs, files in os.walk(path):
#     for file in files:
#         if file.endswith(".yaml"):
#             file_path = os.path.join(root, file)
#             suite = TestSuite()
#             suite.from_yaml_file(file_path)
#             print(suite.__dict__)
#             for case in suite.test_cases:
#                 print(case.__dict__)

path = "/Volumes/Data/Code/WebexRegressSheild/src/test_space/test_batch/"
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith(".yaml"):
            file_path = os.path.join(root, file)
            case = TestCaseBatch()
            case.from_yaml_file(file_path)
            print(case.__dict__)