# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "jsonschema==4.25.1",
#     "pyyaml==6.0.3",
# ]
# ///

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error

import yaml
from jsonschema import Draft202012Validator

import github_repositories

NAME_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")
MERGE_TAG = "tag:yaml.org,2002:merge"
MAX_WHOAMI = 65535


class Report:
    def __init__(self, path):
        self.path = path
        self.errors = 0

    def emit(self, level, message, line=None):
        if level == "error":
            self.errors += 1
        if os.environ.get("GITHUB_ACTIONS"):
            location = f" file={self.path},line={line}" if line else ""
            print(f"::{level}{location}::{message}")
        else:
            print(f"{level}: {message}" + (f" (line {line})" if line else ""), file=sys.stderr)


def duplicate_keys(node, visited=None):
    visited = set() if visited is None else visited
    if id(node) in visited:
        return
    visited.add(id(node))
    if isinstance(node, yaml.MappingNode):
        seen = {}
        for key, value in node.value:
            if key.tag != MERGE_TAG:
                if key.value in seen:
                    yield key.value, seen[key.value], key.start_mark.line + 1
                else:
                    seen[key.value] = key.start_mark.line + 1
            yield from duplicate_keys(value, visited)
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            yield from duplicate_keys(item, visited)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def base_devices(path, ref):
    merge_base = git("merge-base", "HEAD", ref)
    relative = git("ls-files", "--full-name", path)
    return (yaml.safe_load(git("show", f"{merge_base}:{relative}")) or {}).get("devices") or {}


def main():
    parser = argparse.ArgumentParser(description="Validates the WhoAmI registry.")
    parser.add_argument("registry", help="the registry file to validate")
    parser.add_argument("schema", help="the JSON Schema of the registry")
    parser.add_argument("--base", default="origin/main", help="the branch that changed entries are found against")
    args = parser.parse_args()
    report = Report(args.registry)

    text = open(args.registry, encoding="utf-8").read()
    root = yaml.compose(text)
    for key, first, line in duplicate_keys(root):
        report.emit("error", f"duplicate key {key}, first declared on line {first}", line)
    registry = yaml.safe_load(text) or {}
    owners = registry.get("owners") or {}
    devices = registry.get("devices") or {}
    sections = {key.value: value for key, value in root.value}
    lines = {int(key.value): key.start_mark.line + 1 for key, _ in sections["devices"].value if key.value.isdigit()}

    schema = json.load(open(args.schema, encoding="utf-8"))
    document = {"owners": owners, "devices": {str(key): entry for key, entry in devices.items()}}
    for error in Draft202012Validator(schema).iter_errors(document):
        path = list(error.absolute_path)
        line = lines.get(int(path[1])) if len(path) > 1 and path[0] == "devices" and str(path[1]).isdigit() else None
        report.emit("error", f"{'/'.join(map(str, path))}: {error.message}", line)

    for key in devices:
        if isinstance(key, int) and key > MAX_WHOAMI:
            report.emit("error", f"WhoAmI {key} is greater than {MAX_WHOAMI}", lines.get(key))
    if all(isinstance(key, int) for key in devices) and list(devices) != sorted(devices):
        report.emit("error", "devices are not sorted by WhoAmI")
    if list(owners) != sorted(owners):
        report.emit("error", "owners are not sorted alphabetically")

    owner_nodes = {id(value): key.value for key, value in sections["owners"].value}
    used = {
        owner_nodes[id(value)]
        for _, entry in sections["devices"].value
        for key, value in entry.value
        if key.tag == MERGE_TAG and id(value) in owner_nodes
    }
    for owner in sorted(set(owners) - used):
        report.emit("error", f"owner {owner} is not used by any device")

    names = {}
    for key, entry in devices.items():
        name = str(entry.get("name", ""))
        if name.lower() in names:
            report.emit("error", f"{key} {name}: the name is already used by {names[name.lower()]}", lines.get(key))
        else:
            names[name.lower()] = key

    try:
        base = base_devices(args.registry, args.base)
    except subprocess.CalledProcessError as error:
        report.emit("error", f"changes cannot be found against {args.base} ({error.stderr.strip()})")
        sys.exit(1)
    changed = {key for key, entry in devices.items() if base.get(key) != entry}
    for key in sorted(changed):
        if devices[key].get("legacy") and key not in base:
            report.emit("error", f"{key} {devices[key].get('name')}: a new entry cannot be marked legacy", lines.get(key))

    candidates = {key: entry for key, entry in sorted(devices.items()) if not entry.get("legacy")}
    for key, entry in candidates.items():
        level, label = "error" if key in changed else "warning", f"{key} {entry.get('name')}"
        if not entry.get("authors"):
            report.emit(level, f"{label}: no owner is declared", lines.get(key))
        if not NAME_PATTERN.match(str(entry.get("name", ""))):
            report.emit(level, f"{label}: the name is not PascalCase", lines.get(key))
        if not entry.get("repositoryUrl"):
            report.emit(level, f"{label}: no repository is declared", lines.get(key))
        elif not github_repositories.repository_path(entry["repositoryUrl"]):
            report.emit(level, f"{label}: the repository is not hosted on GitHub", lines.get(key))

    repositories = sorted({
        entry["repositoryUrl"]
        for entry in candidates.values()
        if github_repositories.repository_path(entry.get("repositoryUrl") or "")
    })
    access_token = github_repositories.token()
    if not access_token:
        report.emit("error", "repositories cannot be checked without a GitHub token, so set GITHUB_TOKEN or sign in with the GitHub CLI")
        sys.exit(1)
    try:
        results = github_repositories.query(repositories, ["device.yml"], access_token)
    except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
        report.emit("error", f"repositories could not be checked ({getattr(error, 'reason', error)})")
        sys.exit(1)

    for key, entry in candidates.items():
        repository = entry.get("repositoryUrl")
        if repository not in results:
            continue
        level, label = "error" if key in changed else "warning", f"{key} {entry.get('name')}"
        result = results[repository]
        if result is None:
            report.emit(level, f"{label}: the repository is not public or does not exist", lines.get(key))
            continue
        if result["url"].lower() != repository.rstrip("/").lower():
            report.emit("warning", f"{label}: the repository has moved to {result['url']}", lines.get(key))
        if "device.yml" not in result["files"]:
            report.emit(level, f"{label}: no device.yml at the repository root", lines.get(key))
            continue
        try:
            device = yaml.safe_load(result["files"]["device.yml"])
        except yaml.YAMLError:
            report.emit(level, f"{label}: device.yml is not valid YAML", lines.get(key))
            continue
        device = device if isinstance(device, dict) else {}
        if device.get("whoAmI") != key:
            report.emit(level, f"{label}: device.yml declares WhoAmI {device.get('whoAmI')}", lines.get(key))
        declared_name = device.get("name", device.get("device"))
        if declared_name != entry.get("name"):
            report.emit(level, f"{label}: device.yml declares the name {declared_name}", lines.get(key))

    sys.exit(1 if report.errors else 0)


if __name__ == "__main__":
    main()
