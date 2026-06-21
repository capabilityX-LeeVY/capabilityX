#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from optparse import OptionParser
import os
import requests
import subprocess
from http.cookiejar import CookieJar
import time
import argparse
import json
import copy


def find_like(text, l):
    return list(filter(lambda item: not item.find(text), l))


def find_by_keyname(text, l):
    return list(filter(lambda item: item['name'] == text, l))


def parse_args():
    parser = argparse.ArgumentParser(description="Pocess Get ICA file Argument")

    parser.add_argument('-s', '--sfurl', required=True, help="http://10.140.74.33/Citrix/StoreWeb/")
    parser.add_argument('-i', '--icapath', required=True, help="myica.ica")
    parser.add_argument('-u', '--username', required=True, help="Username")
    parser.add_argument('-p', '--password', required=True, help="password")
    parser.add_argument('-d', '--domain', required=True, help="domain")
    parser.add_argument('-a', '--appname', required=True, help="appname")
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()
    sfurl = args.sfurl
    appname = args.appname
    icapath = args.icapath
    username = args.username
    password = args.password
    argdomain = args.domain
    request_timeout = 30

    print
    sfurl, appname, icapath, username, password, argdomain
    if os.path.exists(icapath):
        print("removing old ICA file...")
        os.remove(icapath)

    headers = {"Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               "Upgrade-Insecure-Requests": "1"}
    s = requests.Session()

    try:
        r = s.get(sfurl, headers=headers, timeout=request_timeout)

        headers = {"Accept": 'application/xml, text/xml, */*; q=0.01', "Content-Length": "0",
                   "X-Requested-With": "XMLHttpRequest", "X-Citrix-IsUsingHTTPS": "No", "Referer": sfurl}
        r = s.post(sfurl + "Home/Configuration", headers=headers, timeout=request_timeout)

        csrf = ""
        cookiedomain = ""
        for domain in s.cookies.list_domains():
            csrf_cookie_names = find_like("CsrfToken", list(s.cookies.get_dict(domain=domain).keys()))
            if len(csrf_cookie_names) == 1:
                csrf = s.cookies.get(csrf_cookie_names[0]).strip()
                cookiedomain = domain
            elif len(csrf_cookie_names) > 1:
                raise Exception("there are more than one crsf token!")
                break
            if not csrf:
                raise Exception("not found csrf token!")

            headers = {"Content-Type": 'application/x-www-form-urlencoded; charset=UTF-8',
                       "Accept": 'application/json, text/javascript, */*; q=0.01', "X-Citrix-IsUsingHTTPS": "No",
                       "Csrf-Token": csrf, "Referer": sfurl, "format": 'json&resourceDetails=Default'}

            r = s.post(sfurl + "Resources/List", headers=headers, timeout=request_timeout)

            headers = {"Accept": 'application/xml, text/xml, */*; q=0.01', "Content-Length": "0",
                       "X-Citrix-IsUsingHTTPS": "No", "Referer": sfurl, "Csrf-Token": csrf}
            r = s.post(sfurl + "Authentication/GetAuthMethods", headers=headers, timeout=request_timeout)

            # Start Login Process
            headers = {"Accept": "application/xml, text/xml, */*; q=0.01", "Csrf-Token": csrf,
                       "X-Citrix-IsUsingHTTPS": "No", "Content-Length": "0"}

            # Add cookies that would normally prompt
            s.cookies.set('CtxsUserPreferredClient', 'Native', domain=cookiedomain)
            s.cookies.set('CtxsClientDetectionDon', 'true', domain=cookiedomain)
            s.cookies.set('CtxsHasUpgradeBeenShown', 'true', domain=cookiedomain)

            r = s.post(sfurl + "ExplicitAuth/Login", headers=headers, timeout=request_timeout)

            # Explicit Authentication
            headers = {"Content-Type": 'application/x-www-form-urlencoded; charset=UTF-8',
                       "Accept": 'application/json, text/javascript, /; q=0.01', "X-Citrix-IsUsingHTTPS": "No",
                       "Csrf-Token": csrf, "Referer": sfurl, "X-Requested-With": "XMLHttpRequest"}
            body = {"domain": argdomain, "loginBtn": "Log On", "password": password, "saveCredentials": "false",
                    "username": username, "StateContext": ""}
            r = s.post(sfurl + "ExplicitAuth/LoginAttempt", headers=headers, data=body, timeout=request_timeout)

            # Gets resources and required ICA URL
            headers = {"Content-Type": 'application/x-www-form-urlencoded; charset=UTF-8',
                       "Accept": 'application/json, text/javascript, */*; q=0.01', "X-Citrix-IsUsingHTTPS": "No",
                       "Csrf-Token": csrf, "Referer": sfurl, "X-Requested-With": "XMLHttpRequest"}
            body = {"format": 'json', "resourceDetails": 'Default'}
            content = s.post(sfurl + "Resources/List", headers=headers, data=body, timeout=request_timeout)

            # Creates ICA file
            resources = content.json()
            resourceoutput = resources["resources"]
            resourceurl = find_by_keyname(appname, resourceoutput)

            if len(resourceurl) > 1:
                raise Exception("MULTIPLE APPS FOUND for $appname.  Check APP NAME!")
            if len(resourceurl) == 0:
                raise Exception("APP NOT FOUND for $appname.  Check APP NAME!")

            print
            resourceurl[0]["launchurl"], resourceurl[0]["name"]
            with open(icapath, 'wb') as f:
                r = s.get(sfurl + resourceurl[0][
                    "launchurl"] + '?CsrfToken=' + csrf + "&IsUsingHttps=No&displayNameDesktopTitle=" + resourceurl[0][
                              "name"], timeout=request_timeout)
                f.write(r.content)
    except requests.exceptions.Timeout:
        print("ERROR: Connection timed out while retrieving ICA file.")
        sys.exit(1)
    except requests.exceptions.RequestException as exc:
        print("ERROR: Connection failed while retrieving ICA file: {0}".format(exc))
        sys.exit(1)