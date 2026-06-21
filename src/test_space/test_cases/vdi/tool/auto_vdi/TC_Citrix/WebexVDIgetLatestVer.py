import requests
from bs4 import BeautifulSoup
import subprocess
import os
import time
import argparse
import sys
import re
import urllib.request
import urllib.error
from html.parser import HTMLParser


DEFAULT_URL = "http://dlwebex.jabberqa.cisco.com/Master_windows_qt6.html"
EFTBRANCH_URL = "https://engci-maven-master.cisco.com/artifactory/webex-vdi-builds-generic/webex-vdi/windows/x64/"
ARTIFACTORY_TOKEN_ENV = "WEBEX_VDI_ARTIFACTORY_TOKEN"


def parse_args():
    parser = argparse.ArgumentParser(description="Find the latest VDI version.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Source HTML URL")
    parser.add_argument(
        "--eftbranch",
        help="Find latest version within major.minor or major.minor.patch (e.g. 46.3 or 46.3.0)",
    )
    parser.add_argument(
        "--eft-branch",
        dest="eftbranch",
        help="Alias for --eftbranch",
    )
    return parser.parse_args()


def _normalize_branch_value(value):
    if value is None:
        return None
    return value.strip().strip("/\\")


def _iter_versions(text):
    if text is None:
        return
    normalized = text.replace("/", " ").replace("\\", " ")
    for match in re.finditer(r"\b(\d+)\.(\d+)\.(\d+)\.(\d+)\b", normalized):
        version_tuple = tuple(int(part) for part in match.groups())
        yield version_tuple, match.group(0)


def _extract_full_version_tuple(value):
    name = _normalize_branch_value(value)
    if not name:
        return None
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", name)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _parse_eftbranch(value):
    text = _normalize_branch_value(value)
    if not text:
        return None
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    if not match:
        return None
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = match.group(3)
    if patch is None:
        return (major, minor)
    return (major, minor, int(patch))


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self.links.append(value)


def _fetch_directory_links(url, token=None, timeout=30):
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            data = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}")
        return None
    except urllib.error.URLError as exc:
        print(f"URL error: {exc.reason}")
        return None

    if "text/html" not in content_type:
        print("Unexpected content type; expected HTML directory listing.")
        return None

    parser = _LinkParser()
    parser.feed(data)
    return parser.links


def main():
    args = parse_args()
    url = args.url
    if args.eftbranch:
        url = EFTBRANCH_URL

    if args.eftbranch:
        token = os.getenv(ARTIFACTORY_TOKEN_ENV)
        if not token:
            print(f"Missing token: set {ARTIFACTORY_TOKEN_ENV}")
            return 1
        links = _fetch_directory_links(url, token=token)
        if links is None:
            return 1
        candidates = []
        for link in links:
            version_tuple = _extract_full_version_tuple(link)
            if version_tuple is not None:
                candidates.append((version_tuple, _normalize_branch_value(link)))
    else:
        res = requests.get(url, timeout=None)
        soup = BeautifulSoup(res.text, "html.parser")
        text_content = soup.get_text()
        candidates = list(_iter_versions(text_content))

    if not candidates:
        print("No versions found.")
        return 2

    if args.eftbranch:
        eft_branch = _normalize_branch_value(args.eftbranch)
        prefix = _parse_eftbranch(eft_branch)
        if not prefix:
            print("Invalid eftbranch format; expected major.minor or major.minor.patch (e.g. 46.3 or 46.3.0).")
            return 3
        branch_candidates = [item for item in candidates if item[0][: len(prefix)] == prefix]
        if not branch_candidates:
            print(f"No versions found for {eft_branch}.*")
            return 2
        latest = max(branch_candidates, key=lambda item: item[0])[1]
        print(latest)
        return 0

    latest = max(candidates, key=lambda item: item[0])[1]
    print(latest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
