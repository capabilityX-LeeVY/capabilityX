import argparse

from pathlib import Path
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH, FEATURE_TOGGLE_CONFIG_PATH, APP_VERSION_PATH
from common.handler import fileHandler
from tools.webexApp import appHandler

class SettingsManager:
    def __init__(self, settings_path):
        self.settings_path = settings_path or SETTINGS_PATH
        settings_file = Path(self.settings_path)
        # settings_file.write_text("{}")
        self.settings = DynamicConfig(self.settings_path)
        self.feature_toggle = DynamicConfig(FEATURE_TOGGLE_CONFIG_PATH)

    def settingsSetUp(self):
        args = self._parse_arguments()
        kwargs = self._prepare_kwargs(args)
        self._save_settings(args, kwargs)
        return kwargs

    def _parse_arguments(self):
        parser = argparse.ArgumentParser(description='Install Webex with specified options.')
        def _str2bool(v):
            if isinstance(v, bool):
                return v
            if v.lower() in ('yes', 'true', 't', '1'):
                return True
            elif v.lower() in ('no', 'false', 'f', '0'):
                return False
            else:
                raise argparse.ArgumentTypeError('Boolean value expected.')

        parser.add_argument('--environment', '-env', choices=['ATS', 'BTS', 'GT'], default='BTS',
                            help='Specify the running environment (ATS or BTS).')
        
        parser.add_argument('--version', '-v', default='latest',
                            help='Version to download, "latest" or "eft" or "45.8.0.12345".')
        parser.add_argument('--path', default='',
                            help='Download path.')
        # parser.add_argument('--uninstall', '-u', action='store_true', default=True,
        #                     help='Uninstall Webex.')
        parser.add_argument('--uninstall', '-u', type=_str2bool, nargs='?', const=True, default=True,
                    help='Uninstall Webex (true/false).')
        # parser.add_argument('--keepAPP', '-k', action='store_false', dest='uninstall',
        #                     help='Do not uninstall Webex')
        parser.add_argument('--keepApp', '-k', action='store_true', default=False,
                    help='Skip app insetallation.')
        parser.add_argument('--source', '-s', default='shanghai',
                            help='Webex builds source, can be shanghai, galway and sym.')
        import platform as _platform
        parser.add_argument('--qtversion', '-qt', default='' if _platform.system().lower().startswith('darwin') else '6.8',
                            help='Qt version, 5/6/6.x')
        parser.add_argument('--arch', action='store', default='x64',
                        help='architecture, x64 or arm64')
        parser.add_argument('--cdntoken', action='store', default='',
                            help='token used to download builds from CDN')
        parser.add_argument('--http2', action='store_true', default=True,
                            help='install http2 builds')
        parser.add_argument('--notResetDB', action='store_true', default=False,
                            help='do not reset Webex database')
        parser.add_argument('--downloadonly', action='store_true', default=False,
                            help='download only, do not install')
        parser.add_argument('--cleanupAllVersions', action='store_true', default=False,
                            help='cleanup all version installation packages, otherwise only cleanup older versions')

        parser.add_argument('--openai', '-ai', action='store_true', default=False,
                            help='Analyze data with openAI.')        
        parser.add_argument('--jira', '-j', action='store_true', default=False,
                            help='Report jira issues.')
        parser.add_argument('--recording', '-rec', action='store_true', default=False,
                            help='Enable video recording for test execution.')

        parser.add_argument('--screenReaderFileName', '-sr', type=str, default='WCAG_Screen_Reader_overall_report.md',
                            help='Specify the screen reader file name.')
        parser.add_argument('--fileNBugs', '-nBugs', type=int, default=5,
                            help='pecify the number of bugs to report')  
        
        parser.add_argument('--workflow', '-wf', choices=['is_page', 'guest_join_meeting', 'in_meeting', 'sign_up', 'schedule','audio', 'video', 'share', 'ai_assistant','full_meeting','app_core', 'calling', 'settings'], default='',
                    help='Specify the function to perform.')
        
        parser.add_argument('--continueRun', '-c', action='store_true', default=False,
                    help='continue run the script last time was stopped, default is False')

        parser.add_argument('--account', '-account', type=str, default="default",
                    help='use account name,please refer to src/config/account.json for more details')
        
        parser.add_argument('--botRoomId', '-botRoomId', type=str, default="",
                    help='specify the bot room id to send message to')

        parser.add_argument('--onNewVersion', '-onv', action='store_true', default=False,
                    help='trigger the job automatically upon new app version detection')

        # Create mutually exclusive group for test suite, test case, and test batch
        test_group = parser.add_mutually_exclusive_group()
        test_group.add_argument('--test_suite', '-ts', type=str, default='',
                            help='Specify the test suite to run, e.g., "video_vbg", "audio". If not specified, all test suites will be run.')
        
        test_group.add_argument('--test_case', '-tc', type=str, default='',
                            help='Specify a single test case to run, e.g., "vbg_static_in_meeting".')
        
        test_group.add_argument('--test_batch', '-tb', type=str, default='',
                            help='Specify a test batch to run independent test cases, e.g., "video_vbg". Batch files are located in src/test_space/test_batch/')

        parser.add_argument('--language', '-l', default='en_US',
                    help='The language should be en_US, zh_CN, ja_JP, ko_KR, de_DE, es_ES, fr_FR, it_IT, pt_BR')

        parser.add_argument('--fileName', '-fileName', type=str, default='',
                            help='file bugs file name')
        parser.add_argument('--platform', '-p', choices=['windows', 'mac', 'linux', 'default'], default='default',
                            help='Specify the platform to run the tests on.')

        parser.add_argument('--bundleID', '-bid', type=str, default='Cisco-Systems.Spark',
                            help='Specify the application bundle ID, e.g., "Cisco-Systems.Spark", "com.google.Chrome".')
                           
        return parser.parse_args()

    def _prepare_kwargs(self, args):
        return {key: value for key, value in vars(args).items() if value is not None}

    def _save_settings(self, args, kwargs):
        self.settings.set('environment', args.environment)
        install_options = self.settings.get('installOptions') or {}
        install_options.update({k: v for k, v in kwargs.items() if k not in ['environment', 'keepApp', 'openai', 'jira', 'recording', 'workflow','screenReaderFileName', 'fileNBugs', 'language',"continue","fileName", "test_suite", "test_case", "test_batch", "cleanupAllVersions", "account","platform","botRoomId","onNewVersion"]})
        self.settings.set('installOptions', install_options)
        self.settings.set('bundleID', args.bundleID)
        self.settings.set('openai', args.openai)
        self.settings.set('jira', args.jira)
        self.settings.set('recording', args.recording)
        self.settings.set('cleanupAllVersions', args.cleanupAllVersions)
        self.settings.set('screenReaderFileName', args.screenReaderFileName)
        self.settings.set('fileNBugs', args.fileNBugs)
        self.settings.set('workflow', args.workflow)
        self.settings.set('test_suite', args.test_suite)
        self.settings.set('test_case', getattr(args, 'test_case', ''))
        self.settings.set('test_batch', getattr(args, 'test_batch', ''))
        self.settings.set('account', args.account)
        self.settings.set('botRoomId', args.botRoomId)
        self.settings.set('onNewVersion', args.onNewVersion)
        if args.platform != 'default':
            self.settings.set('platform', args.platform)
        else:
            import platform
            current_platform = platform.system().lower()
            if current_platform.startswith('win'):
                self.settings.set('platform', 'windows')
            elif current_platform.startswith('darwin'):
                self.settings.set('platform', 'mac')
            elif current_platform == 'linux':
                self.settings.set('platform', 'linux')
            else:
                raise Exception(f"Unsupported platform: {current_platform}")
            
        # Set mode based on which parameter was provided
        if getattr(args, 'test_case', ''):
            self.settings.set('mode', 'case')
        elif getattr(args, 'test_batch', ''):
            self.settings.set('mode', 'batch')
        else:
            self.settings.set('mode', 'suite')
        self.settings.set('language', args.language)
        self.settings.set('continueRun', args.continueRun)
        self.settings.set('appVersion', self._get_app_version())
        self.settings.set('fileName', args.fileName)
        if args.keepApp:
            self.feature_toggle.set('installer', False)

    def _get_app_version(self):
        # app_version = fileHandler.readFile(APP_VERSION_PATH)
        app_version = appHandler.get_app_version()
        return app_version

def initSettings(settings_path):
    settings_manager = SettingsManager(settings_path)
    return settings_manager.settingsSetUp()