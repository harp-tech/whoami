import argparse
import subprocess
import sys

import griffe

from harp.whoami.generation import MODULE_FILE

PACKAGE = "harp-whoami"
IMPORT_NAME = "harp.whoami"
SOURCE_FOLDER = "src"
PACKAGE_PATHS = [SOURCE_FOLDER, "pyproject.toml", "register.py"]
TAG_PREFIX = "v"
MINIMUM_VERSION = "0.1.0"
ENUM_PATH = "registry.WhoAmI"
EXCLUDED_MODULES = ("cli", "generation", "github", "validation")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def last_release():
    result = git("describe", "--tags", "--abbrev=0", "--match", f"{TAG_PREFIX}*")
    return result.stdout.strip() if result.returncode == 0 else None


def changed(since, *paths):
    return git("diff", "--quiet", since, "HEAD", "--", *paths).returncode != 0


def load_package(ref=None):
    if ref is None:
        package = griffe.load(IMPORT_NAME, search_paths=[SOURCE_FOLDER])
    else:
        package = griffe.load_git(IMPORT_NAME, ref=ref, search_paths=[SOURCE_FOLDER])
    for name in EXCLUDED_MODULES:
        if name in package.members:
            del package[name]
    return package


def parse_version(version):
    return tuple(int(part) for part in version.split("."))


def bump_version(version, level):
    major, minor, patch = parse_version(version)
    if level == "major" and major > 0:
        return f"{major + 1}.0.0"
    if level in ("major", "minor"):
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def next_version(version, level):
    return max(bump_version(version, level), MINIMUM_VERSION, key=parse_version)


def release_level(since):
    previous, current = load_package(since), load_package()
    breakages = [
        f"{breakage.obj.path}: {breakage.kind.value}" for breakage in griffe.find_breaking_changes(previous, current)
    ]
    if breakages:
        return "major", "\n".join(["the public API changed in a breaking way", *breakages])
    added = set(current[ENUM_PATH].members) - set(previous[ENUM_PATH].members)
    if added:
        return "minor", f"devices were added: {', '.join(sorted(added))}"
    if changed(since, *PACKAGE_PATHS, f":!{MODULE_FILE}"):
        return "minor", "the package code, its metadata or the registration script changed"
    return "patch", "only the records of registered devices changed"


def main():
    parser = argparse.ArgumentParser(
        description=f"Prints the next version of {PACKAGE} if it changed since the last release."
    )
    parser.parse_args()
    since = last_release()
    if since is None:
        print(f"no release yet, so the first release is {MINIMUM_VERSION}", file=sys.stderr)
        print(MINIMUM_VERSION)
        return
    if not changed(since, *PACKAGE_PATHS):
        print(f"the package has not changed since {since}", file=sys.stderr)
        return
    level, reason = release_level(since)
    print(f"{level} release, since {reason}", file=sys.stderr)
    print(next_version(since.removeprefix(TAG_PREFIX), level))


if __name__ == "__main__":
    main()
