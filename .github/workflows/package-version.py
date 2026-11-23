import argparse
import datetime
import json
import subprocess
import urllib.error
import urllib.request
from http import HTTPStatus

PACKAGE = "harp-whoami"
PACKAGE_PATHS = ["src", "pyproject.toml"]
PYPI_URL = f"https://pypi.org/pypi/{PACKAGE}/json"
TAG_PATTERN = "v*"
TIMEOUT = 20


def last_release():
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "--match", TAG_PATTERN], capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else None


def package_changed(since):
    if since is None:
        return True
    return subprocess.run(["git", "diff", "--quiet", since, "HEAD", "--", *PACKAGE_PATHS]).returncode != 0


def last_change_date():
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", *PACKAGE_PATHS], capture_output=True, text=True, check=True
    )
    return datetime.datetime.fromtimestamp(int(result.stdout.strip()), datetime.UTC).date()


def published_versions():
    try:
        with urllib.request.urlopen(PYPI_URL, timeout=TIMEOUT) as response:
            return set(json.load(response)["releases"])
    except urllib.error.HTTPError as error:
        if error.code == HTTPStatus.NOT_FOUND:
            return set()
        raise


def next_version(today, published):
    version = f"{today.year}.{today.month}.{today.day}"
    serial = 0
    while (f"{version}.{serial}" if serial else version) in published:
        serial += 1
    return f"{version}.{serial}" if serial else version


def main():
    parser = argparse.ArgumentParser(
        description=f"Prints the next version of {PACKAGE}, dated by its last change, if it changed since the last release."
    )
    parser.parse_args()
    if package_changed(last_release()):
        print(next_version(last_change_date(), published_versions()))


if __name__ == "__main__":
    main()
