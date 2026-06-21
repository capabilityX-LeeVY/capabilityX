from config.paths import TEST_CASES_PATH, TEST_SPACE_PATH, TEST_SUITE_PATH, TEST_BATCHES_PATH
import os
import yaml
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR

class StepAction(object):
    def __init__(self):
        self.type = None
        self.value = None
        self.wait_time = None
        self.parameters = None
        self.agent_node = None
        self.save_to = None
        self.target = None

    def from_dict(self, action_dict):
        self.verify(action_dict)

        self.type = action_dict.get('type')
        self.value = action_dict.get('value')
        self.wait_time = action_dict.get('wait_time', None)
        self.parameters = action_dict.get('parameters', None)
        self.agent_node = action_dict.get('agent_node', None)
        self.save_to = action_dict.get('save_to', None)
        self.target = action_dict.get('target', None)

    def verify(self,action_dict):
        keys = action_dict.keys()
        result = True
        message = ""
        except_keys = ['type','value','wait_time','parameters','agent_node','save_to','target']
        for key in keys:
            if key not in except_keys:
                message += f"Invalid key in action_dict: {key}\n"
                result = False

        if result == False:
            LOGGER_ERROR(message)
            raise Exception(message)

class Step(object):
    def __init__(self):
        self.name = None
        self.action = None
        self.expect_state = None
        self.optional = False
        self.ui_response = None
        self.ui_response_threshold_ms = None
        self.platforms = None 
        self.performance_cpu_threshold = None
        self.performance_mem_threshold_mb = None
        self.performance_gpu_threshold = None
        self.ai_check = None
        self.wait_time = None

    def from_dict(self, step_dict):
        self.verify(step_dict)

        self.name = step_dict.get('name')
        action_dict = step_dict.get('action', {})
        self.action = StepAction()
        self.action.from_dict(action_dict)
        self.expect_state = step_dict.get('expect_state', None)
        self.optional = step_dict.get('optional', False)
        self.ui_response = step_dict.get('ui_response', None)
        self.ui_response_threshold_ms = step_dict.get('ui_response_threshold_ms', None)
        self.platforms = step_dict.get('platforms', None)
        self.performance_cpu_threshold = step_dict.get('performance_cpu_threshold', None)
        self.performance_mem_threshold_mb = step_dict.get('performance_mem_threshold_mb', None)
        self.performance_gpu_threshold = step_dict.get('performance_gpu_threshold', None)
        self.ai_check = step_dict.get('ai_check', None)
        self.wait_time = step_dict.get('wait_time', None)
        self.stop_on_ai_check_failure = step_dict.get('stop_on_ai_check_failure', False)
    
    def is_platform_supported(self, platform):
        platform = platform.lower()
        if self.platforms is None:
            return True
        if platform in [p.lower() for p in self.platforms]:
            return True
        return False
    
    def verify(self, step_dict):
        keys = step_dict.keys()
        result = True
        message = ""
        expect_keys = ['name','action','expect_state','optional','ui_response',
                       'ui_response_threshold_ms','platforms',
                       'performance_cpu_threshold','performance_mem_threshold_mb',
                       'performance_gpu_threshold',"ai_check","wait_time","navigated","stop_on_ai_check_failure","ai_observe","skip_report","skip_screenshot"]
        for key in keys:
            if key not in expect_keys:
                message += f"Invalid key in step_dict: {key}\n"
                result = False

        if result == False:
            LOGGER_ERROR(message)
            raise Exception(message)

class TestCase(object):
    def __init__(self):
        self.name = None
        self.description = None
        self.team = None
        self.owner = None
        self.expect_result = None
        self.pre_conditions = []
        self.steps: list[Step] = []
        self.post_conditions = []
        self.execution_duration = None 
        self.execution_count = None
        self.project = None

        self.check_points: list[dict] = []
        self.account = None 
        self.need_initialization = None
        self.supported_platforms = None
        self.platforms = None
        self.message_bot = None
        self.custom_dataset = None
        self.case_full_path = None
        self.retry_enabled = True
        self.record_traversal = False
        self.continue_on_error = False
    
    def is_specific_case(self):
        specialCase = ["install Webex app","re-install Webex app","uninstall Webex app"]
        if self.name in specialCase:
            return True
        
        return False
        
    def from_dict(self, test_case_dict):
        self.name = test_case_dict.get('name')
        self.team = test_case_dict.get('team', None)
        self.owner = test_case_dict.get('owner', None)
        self.description = test_case_dict.get('description')
        self.account = test_case_dict.get('account', None)
        self.project = test_case_dict.get('project', None)
        self.platforms = test_case_dict.get('platforms', None)
        if self.platforms is not None:
            self.supported_platforms = self.platforms.get('supported', None)
        self.expect_result = test_case_dict.get('expect_result')
        self.pre_conditions = None
        pre_conditions = test_case_dict.get('pre_conditions', None)

        if pre_conditions is not None:
            self.pre_conditions = []
            for condition in pre_conditions:
                case = TestCase()
                case.from_yaml_file_Relative_path(condition)
                self.pre_conditions.append(case)

        steps_list = test_case_dict.get('steps', [])
        self.steps = []
        for step_dict in steps_list:
            step = Step()
            step.from_dict(step_dict)
            self.steps.append(step)

        self.post_conditions = None
        post_conditions = test_case_dict.get('post_conditions', None)

        if post_conditions is not None:
            self.post_conditions = []
            for condition in post_conditions:
                case = TestCase()
                case.from_yaml_file_Relative_path(condition)
                self.post_conditions.append(case)
        
        self.execution_duration = test_case_dict.get('execution_duration', None)
        self.execution_count = test_case_dict.get('execution_count', None)
        self.check_points = test_case_dict.get('check_points', [])
        self.need_initialization = test_case_dict.get('need_initialization', None)
        self.message_bot = test_case_dict.get('message_bot', None)
        self.message_room = test_case_dict.get('message_room', None)
        self.custom_dataset = test_case_dict.get('custom_dataset', None)
        self.retry_enabled = test_case_dict.get('retry_enabled', True)
        self.record_traversal = test_case_dict.get('record_traversal', False)
        self.continue_on_error = test_case_dict.get('continue_on_error', False)
        self.verify(test_case_dict)

    def is_platform_supported(self, platform):
        platform = platform.lower()
        if self.supported_platforms is None:
            return True
        if platform in [p.lower() for p in self.supported_platforms]:
            return True
        return False
    
    def from_yaml_file(self, file_path):
        LOGGER_INFO(f"Loading test case from file: {file_path}")
        if os.path.exists(file_path) == False:
            message = f"YAML file not found: {file_path}"
            LOGGER_ERROR(message)
            raise FileNotFoundError(message)

        with open(file_path, 'r', encoding='utf-8') as file:
            test_case_dict = yaml.safe_load(file)
            case_dict = test_case_dict.get('test_case', {})
            self.from_dict(case_dict)
            self.case_full_path = file_path
    
    def from_yaml_file_Relative_path(self, file_path):
        full_path = file_path
        if full_path.endswith('.yaml') == False:
            full_path = file_path + '.yaml'

        if os.path.exists(full_path) == False:
            full_path = TEST_CASES_PATH / full_path

        self.from_yaml_file(full_path)

    def verify(self, test_case_dict):
        keys = test_case_dict.keys()
        result = True
        message = ""
        excect_keys = ['name','description','expect_result','pre_conditions',
                       'steps','post_conditions',
                       'execution_duration','execution_count',
                       'check_points',"team","owner","account","need_initialization",
                        'project',"platforms", "message_bot", "message_room",
                        'custom_dataset', 'retry_enabled', 'record_traversal',
                        'continue_on_error'
                       ]
        for key in keys:
            if key not in excect_keys:
                message += f"Invalid key in test_case_dict: {key}\n"
                result = False
                
        if result == False:
            LOGGER_ERROR(message)
            raise Exception(message)
    
        if self.check_points is not None and len(self.check_points) > 0:
            except_keys = ["keyboard operation", "screen reader", "visual audit", "language", "shortcut"]
            message = ""
            for check_point in self.check_points:
                if check_point not in except_keys:
                    message += f"Invalid check_point in test_case_dict: {check_point}\n"

            if message != "":
                message = f"{message}\n please using keywords:[keyboard operation, screen reader, visual audit, language, shortcut]"
                #LOGGER_ERROR(message)
                #raise Exception(message)
        
    @staticmethod
    def is_a_test_case_file(file_path):
        full_path = file_path
        if full_path.endswith('.yaml') == False:
            full_path = file_path + '.yaml'

        if os.path.exists(full_path) == False:
            full_path = TEST_CASES_PATH / full_path

        if os.path.exists(full_path) == False:
            return False

        with open(full_path, 'r', encoding='utf-8') as file:
            test_case_dict = yaml.safe_load(file)
            case_dict = test_case_dict.get('test_case', None)
            if case_dict is None:
                return False
            
        return True

class TestCaseBatch(object):
    def __init__(self):
        self.name = None
        self.team = None
        self.owner = None
        self.platform = None
        self.language = []
        self.description = None
        self.test_cases: list[TestCase] = []
        self.batch_full_path = None
        
    def from_dict(self, batch_dict):
        self.name = batch_dict.get('name')
        self.team = batch_dict.get('team')
        self.owner = batch_dict.get('owner')
        self.platform = batch_dict.get('platform')
        self.language = batch_dict.get('language', [])
        self.description = batch_dict.get('description', None)

        test_cases_list = batch_dict.get('test_cases', [])
        self.test_cases = []
        for test_case_dict in test_cases_list:
            test_case = TestCase()
            test_case.from_yaml_file_Relative_path(test_case_dict)
            self.test_cases.append(test_case)

        self.verify(batch_dict)

    def verify(self, batch_dict):
        keys = batch_dict.keys()
        result = True
        message = ""
        except_keys = ['name','team','owner','platform','language','test_cases','description']
        for key in keys:
            if key not in except_keys:
                message += f"Invalid key in batch_dict: {key}\n"
                result = False

        if result == False:
            LOGGER_ERROR(message)
            raise Exception(message)

    
    def from_yaml_file(self, file_path):
        LOGGER_INFO(f"Loading test case batch from file: {file_path}")
        if os.path.exists(file_path) == False:
            message = f"YAML file not found: {file_path}"
            LOGGER_ERROR(message)
            raise FileNotFoundError(message)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            batch_dict = yaml.safe_load(file)
            batch_dict = batch_dict.get('test_case_batch', {})
            self.from_dict(batch_dict)
            self.batch_full_path = file_path

    def from_yaml_file_Relative_path(self, file_path):
        full_path = file_path
        if full_path.endswith('.yaml') == False:
            full_path = file_path + '.yaml'
        if os.path.exists(full_path) == False:
            full_path = TEST_SPACE_PATH / "test_batch" / full_path

        self.from_yaml_file(full_path)

    @staticmethod
    def is_a_test_case_batch_file(file_path):
        full_path = file_path
        if full_path.endswith('.yaml') == False:
            full_path = file_path + '.yaml'

        if os.path.exists(full_path) == False:
            full_path = TEST_BATCHES_PATH / full_path

        if os.path.exists(full_path) == False:
            return False

        with open(full_path, 'r', encoding='utf-8') as file:
            batch_dict = yaml.safe_load(file)
            case_dict = batch_dict.get('test_case_batch', None)
            if case_dict is None:
                return False
            
        return True


class TestSuite(object):
    def __init__(self):
        self.name = None
        self.team = None
        self.owner = None
        self.platform = None
        self.language = []
        self.description = None
        self.test_cases: list[TestCase] = []
        self.check_points: list = []
        self.project = None
        self.suite_full_path = None
        self.account = None
        
    def from_dict(self, suite_dict):
        self.name = suite_dict.get('name')
        self.team = suite_dict.get('team')
        self.owner = suite_dict.get('owner')
        self.platform = suite_dict.get('platform')
        self.description = suite_dict.get('description', None)
        self.project = suite_dict.get('project', None)
        self.language = suite_dict.get('language', [])  
        self.account = suite_dict.get('account', None)

        cases_list = suite_dict.get('test_cases', [])
        self.test_cases = []
        for case_dict in cases_list:
            case = TestCase()
            case.from_yaml_file_Relative_path(case_dict)
            self.test_cases.append(case)
        
        self.check_points = suite_dict.get('check_points', None)

        self.verify(suite_dict)

    def from_yaml_file(self, file_path):
        LOGGER_INFO(f"Loading test suites from file: {file_path}")
        if os.path.exists(file_path) == False:
            message = f"YAML file not found: {file_path}"
            LOGGER_ERROR(message)
            raise FileNotFoundError(message)

        with open(file_path, 'r', encoding='utf-8') as file:
            suite_dict = yaml.safe_load(file)
            suite_dict = suite_dict.get('test_suite', {})
            self.from_dict(suite_dict)
            self.suite_full_path = file_path

    def from_yaml_file_Relative_path(self, file_path):
        full_path = file_path
        if full_path.endswith('.yaml') == False:
            full_path = file_path + '.yaml'
        
        if os.path.exists(full_path) == False:
            full_path = TEST_SUITE_PATH / full_path
        
        if os.path.exists(full_path) == False:
            return False
        
        self.from_yaml_file(full_path)

    def verify(self, suite_dict):
        keys = suite_dict.keys()
        result = True
        message = ""
        except_keys = ['name','team','owner','platform','language',
                       'test_cases','check_points','description','project',"account"]
        for key in keys:
            if key not in except_keys:
                message += f"Invalid key in suite_dict: {key}\n"
                result = False

        if result == False:
            LOGGER_ERROR(message)
            raise Exception(message)

    @staticmethod
    def is_a_test_suite_file(file_path):
        full_path = file_path
        if full_path.endswith('.yaml') == False:
            full_path = file_path + '.yaml'

        if os.path.exists(full_path) == False:
            full_path = TEST_SUITE_PATH / full_path

        if os.path.exists(full_path) == False:
            return False
        
        with open(full_path, 'r', encoding='utf-8') as file:
            suite_dict = yaml.safe_load(file)
            case_dict = suite_dict.get('test_suite', None)
            if case_dict is None:
                return False
            
        return True
