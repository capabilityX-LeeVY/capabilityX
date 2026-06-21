from config.paths import TEST_SPACE_PATH
from core.structsDef import TestCase, TestSuite,TestCaseBatch
from core.mac.RSApplicationGT import CRSTestCase,CRSGTTestSuite,CRSGTTestCaseBatch
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR
from common.utils.featureToggle import FeatureToggle
from tools.webexApp import appHandler

class GTManager(object):
    def __init__(self):
        pass

    @staticmethod
    def run_one_test_case(case: TestCase, language: str = "en_US", progress_callback=None):
        return CRSTestCase(case, language).Run(progress_callback=progress_callback)

    @staticmethod
    def run_one_test_suite(suite: TestSuite, language: str = "en_US", progress_callback=None):
        return CRSGTTestSuite(suite, language).Run(progress_callback=progress_callback)
    @staticmethod
    def run_one_test_case_batch(batch: TestCaseBatch, language: str = "en_US", progress_callback=None):
        return CRSGTTestCaseBatch(batch, language).Run(progress_callback=progress_callback)

    @staticmethod
    def run_by_file(file_path: str, language: str = "en_US",progress_callback=None):
        if TestCase.is_a_test_case_file(file_path):
            case = TestCase()
            case.from_yaml_file_Relative_path(file_path)
            return GTManager.run_one_test_case(case, language,progress_callback)
        elif TestSuite.is_a_test_suite_file(file_path):
            suite = TestSuite()
            suite.from_yaml_file_Relative_path(file_path)
            return GTManager.run_one_test_suite(suite, language,progress_callback)
        elif TestCaseBatch.is_a_test_case_batch_file(file_path):
            batch = TestCaseBatch()
            batch.from_yaml_file_Relative_path(file_path)
            return GTManager.run_one_test_case_batch(batch, language,progress_callback)
        else:
            raise ValueError(f'''{file_path} is not a valid test case, test suite or test case batch file.''')

    @staticmethod
    def run_all_test_cases(language: str = "en_US", progress_callback=None):
        from config.paths import TEST_CASES_PATH
        import os
        results = {
            "total": [],
            "passed": [],
            "failed": []
        }
        spicific_test_cases = [
            # promote_blue_channel cases
            "promote_blue_channel/sign_in.yaml",
            "promote_blue_channel/start_meeting.yaml",
            "promote_blue_channel/check_video.yaml",
            "promote_blue_channel/check_audio.yaml",
            "promote_blue_channel/check_share.yaml",

            # video test cases
            "meetings/video/self_view_shown.yaml",
            "meetings/video/vbg executive office.yaml",
            "meetings/video/vbg_dark.yaml",
            "meetings/video/vbg_daylight.yaml",
            "meetings/video/vbg_dynamic.yaml",
            "meetings/video/vbg_fountain.yaml",
            "meetings/video/vbg_home_office.yaml",
            "meetings/video/vbg_lava.yaml",
            "meetings/video/vbg_lookout.yaml",
            #"meetings/video/vbg_none.yaml",
            "meetings/video/vbg_static.yaml",
            "meetings/video/vbg_upload.yaml",

        ]
        for case_file in spicific_test_cases:
            try:
                case = TestCase()
                case.from_yaml_file_Relative_path(case_file)
                GTManager.run_one_test_case(case, language, progress_callback)
                results["passed"].append(case_file)
                LOGGER_INFO(f"Test case {case_file} passed.")
            except Exception as e:
                LOGGER_ERROR(f"Error: running test case {case_file}: {e}")
                failedInfo = {
                    "name": case.name,
                    "error": str(e),
                    "owner": case.owner
                }
                results["failed"].append(failedInfo )
            results["total"].append(case_file)
        passedCases = results["passed"]
        for case in passedCases:
            LOGGER_INFO(f"Passed case: {case}")
        
        failedCases = results["failed"]
        for case in failedCases:
            LOGGER_ERROR(f"Failed case: {case}")
                         
        return results

    @staticmethod
    def run_all_test_suites(language: str = "en_US", progress_callback=None):
        from config.paths import TEST_SUITE_PATH
        import os
        results = {
            "total": [],
            "passed": [],
            "failed": []
        }
        for root, dirs, files in os.walk(TEST_SUITE_PATH):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, TEST_SUITE_PATH)
                    try:
                        suite = TestSuite()
                        suite.from_yaml_file_Relative_path(relative_path)
                        GTManager.run_one_test_suite(suite, language, progress_callback)
                        results["passed"].append(relative_path)
                        LOGGER_INFO(f"Test suite {relative_path} passed.")
                    except Exception as e:
                        LOGGER_ERROR(f"Error: running test suite {relative_path}: {e}")
                        failedInfo = {
                            "name": suite.name,
                            "error": str(e),
                            "owner": suite.owner
                        }
                        results["failed"].append(failedInfo)
                    results["total"].append(relative_path)
        return results
    
    @staticmethod
    def run_all_test_case_batches(language: str = "en_US", progress_callback=None):
        from config.paths import TEST_CASES_PATH
        import os
        results = {
            "total": [],
            "passed": [],
            "failed": []
        }
        batchFolder = os.path.join(TEST_SPACE_PATH, "test_batch")
        for root, dirs, files in os.walk(batchFolder):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, batchFolder)
                    try:
                        batch = TestCaseBatch()
                        batch.from_yaml_file_Relative_path(relative_path)
                        GTManager.run_one_test_case_batch(batch, language, progress_callback)
                        results["passed"].append(relative_path)
                        LOGGER_INFO(f"Test case batch {relative_path} passed.")
                    except Exception as e:
                        LOGGER_ERROR(f"Error: running test case batch {relative_path}: {e}")
                        failedInfo = {
                            "name": batch.name,
                            "error": str(e),
                            "owner": batch.owner
                        }
                        results["failed"].append(failedInfo)    
                    results["total"].append(relative_path)
        return results

    @staticmethod
    def verify_all_cases():
        from config.paths import TEST_CASES_PATH, TEST_SUITE_PATH
        import os
        for root, dirs, files in os.walk(TEST_CASES_PATH):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    file_path = os.path.join(root, file)
                    if file_path.find("batch") != -1:
                        continue
                    case = TestCase()
                    case.from_yaml_file(file_path)
                    case.verify

        batchFolder = os.path.join(TEST_CASES_PATH, "batch")
        for root, dirs, files in os.walk(batchFolder):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    file_path = os.path.join(root, file)
                    case = TestCaseBatch()
                    case.from_yaml_file(file_path)

        for root, dirs, files in os.walk(TEST_SUITE_PATH):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    file_path = os.path.join(root, file)
                    suite = TestSuite()
                    suite.from_yaml_file(file_path)


