#!/bin/bash --login
import logging
import os.path
import subprocess
import sys
import time
import json
import psutil

from config.config import *


class WebexInstallation:
    """webex app installation"""


    def __int__(self):
        pass

    def get_platform(self):
        platform = sys.platform
        if 'darwin' in platform:
            return 'mac'
        elif 'win' in platform:
            return 'windows'
        else:
            return 'unsupported'

    def install_app(self, version):
        platform = self.get_platform()

        if platform == 'windows':
            if version == 'main':
                cmd = WEBEXTOOLHUB_PATH + ' -v ' + 'latest -s shanghai'
                subprocess.check_call(cmd, shell=True)
                time.sleep(10)
            elif version == 'release':
                cmd = WEBEXTOOLHUB_PATH + ' -v ' + 'eft -s shanghai'
                subprocess.check_call(cmd, shell=True)
                time.sleep(10)
            else:
                cmd = WEBEXTOOLHUB_PATH + ' -v ' + version + ' -s shanghai'
                subprocess.check_call(cmd, shell=True)
                time.sleep(10)
        else:
            if version == 'master':
                cmd = WEBEXTOOLHUB_PATH + ' latest shanghai'
                subprocess.check_call(cmd, shell=True)
                time.sleep(10)
            else:
                cmd = WEBEXTOOLHUB_PATH + ' ' + version + ' shanghai'
                subprocess.check_call(cmd, shell=True)
                time.sleep(10)

    def launch_app(self):
        platform = self.get_platform()
        if platform == "windows":
            print("open webex app in widowns platform")
            cmd = r'%localappdata%\Programs\"Cisco Spark"\CiscoCollabHost.exe'
            subprocess.check_call(cmd, shell=True)
        else:
            cmd = 'open -a webex.app'
            subprocess.check_call(cmd, shell=True)
            print("open webex app in Mac platform")

    def get_process(self, platform):
        """
            get webex process info, return related pid
        """
        res = []
        if platform == "windows":
            for p in psutil.process_iter(attrs=['name', 'username']):
                if p.info['name'] == 'CiscoCollabHost.exe':
                    res.append(p)
        elif platform == "mac":
            cmd = "ps ax | grep {} | grep -v grep".format('Webex')
            for p in os.popen(cmd):
                if 'Webex' in p:
                    res.append(p.split()[0])
        return res

    def kill_process(self, platform):
        """
            kill all webex processes
        """
        proc = self.get_process(platform)
        if platform == 'windows':
            if len(proc) != 0:
                # logging.info('Try to kill existing {}'.format('CiscoCollabHost.exe'))
                for pid in proc:
                    try:
                        pid.kill()
                        time.sleep(2)
                    except:
                        # logging.info('Process {} killed'.format('CiscoCollabHost.exe'))
                        break
                logging.info('App killed')
                time.sleep(1)
            else:
                logging.info('App not launched...')
        elif platform == 'mac':
            if len(proc) != 0:
                # logging.info('Try to kill existing {}'.format('Webex'))
                for pid in proc:
                    try:
                        cmd = r'kill -9 ' + pid
                        subprocess.check_call(cmd, shell=True)
                        time.sleep(2)
                    except:
                        # logging.info('Process {} killed'.format('Webex'))
                        break
                logging.info('App killed')
                time.sleep(1)
            else:
                logging.info('App not launched...')

    def quit_app(self):
        platform = self.get_platform()
        if platform == "windows":
            self.kill_process(platform)
            print("quit webex app in windows platform")
        else:
            self.kill_process(platform)
            #cmd = 'pkill -x Webex'
            #subprocess.check_call(cmd, shell=True)
            print("quit webex app in Mac platform")

    def uninstall_app(self):
        platform = self.get_platform()
        if platform == 'windows':
            cmd = WEBEXTOOLHUB_PATH + ' ' + '-u'
            subprocess.check_call(cmd, shell=True)
        else:
            cmd = '"/Applications/Webex Toolhub.app/Contents/MacOS/installwebex.sh" uninstall'
            subprocess.check_call(cmd, shell=True)


if __name__ == '__main__':
    webex = WebexInstallation()
    #webex.install_app('master')
    #webex.launch_app()
    #webex.quit_app()
    webex.uninstall_app()
    webex.install_app('master')
