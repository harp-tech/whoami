import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

import yaml
from jsonschema import Draft202012Validator

from harp.whoami import github

NAME_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")
MERGE_TAG = "tag:yaml.org,2002:merge"
MAX_WHOAMI = 65535


@dataclass(frozen=True)
class Diagnostic:
    """A problem found in the registry."""

    level: Literal["error", "warning"]
    """The severity of the problem."""

    message: str
    """The description of the problem."""

    line: int | None = None
    """The line of the registry where the problem was found, if it applies to one entry."""


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


def validate(
    text: str,
    schema: Mapping[str, Any],
    base: Mapping[int, Any],
    access_token: str,
) -> list[Diagnostic]:
    """Validates the text of a registry against its schema and the requirements for each entry.

    Entries that differ from the base devices report errors, and the remaining entries report
    warnings. Raises an exception if the repositories of the entries cannot be checked.
    """
    diagnostics = []

    def emit(level, message, line=None):
        diagnostics.append(Diagnostic(level, message, line))

    root = yaml.compose(text)
    for key, first, line in duplicate_keys(root):
        emit("error", f"duplicate key {key}, first declared on line {first}", line)
    registry = yaml.safe_load(text) or {}
    owners = registry.get("owners") or {}
    devices = registry.get("devices") or {}
    sections = {key.value: value for key, value in root.value}
    lines = {int(key.value): key.start_mark.line + 1 for key, _ in sections["devices"].value if key.value.isdigit()}

    document = {"owners": owners, "devices": {str(key): entry for key, entry in devices.items()}}
    for error in Draft202012Validator(schema).iter_errors(document):
        path = list(error.absolute_path)
        line = lines.get(int(path[1])) if len(path) > 1 and path[0] == "devices" and str(path[1]).isdigit() else None
        emit("error", f"{'/'.join(map(str, path))}: {error.message}", line)

    for key in devices:
        if isinstance(key, int) and key > MAX_WHOAMI:
            emit("error", f"WhoAmI {key} is greater than {MAX_WHOAMI}", lines.get(key))
    if all(isinstance(key, int) for key in devices) and list(devices) != sorted(devices):
        emit("error", "devices are not sorted by WhoAmI")
    if list(owners) != sorted(owners):
        emit("error", "owners are not sorted alphabetically")

    owner_nodes = {id(value): key.value for key, value in sections["owners"].value}
    used = {
        owner_nodes[id(value)]
        for _, entry in sections["devices"].value
        for key, value in entry.value
        if key.tag == MERGE_TAG and id(value) in owner_nodes
    }
    for owner in sorted(set(owners) - used):
        emit("error", f"owner {owner} is not used by any device")

    names = {}
    for key, entry in devices.items():
        name = str(entry.get("name", ""))
        if name.lower() in names:
            emit("error", f"{key} {name}: the name is already used by {names[name.lower()]}", lines.get(key))
        else:
            names[name.lower()] = key

    changed = {key for key, entry in devices.items() if base.get(key) != entry}
    for key in sorted(changed):
        if devices[key].get("legacy") and key not in base:
            emit("error", f"{key} {devices[key].get('name')}: a new entry cannot be marked legacy", lines.get(key))

    candidates = {key: entry for key, entry in sorted(devices.items()) if not entry.get("legacy")}
    for key, entry in candidates.items():
        level, label = "error" if key in changed else "warning", f"{key} {entry.get('name')}"
        if not entry.get("authors"):
            emit(level, f"{label}: no owner is declared", lines.get(key))
        if not NAME_PATTERN.match(str(entry.get("name", ""))):
            emit(level, f"{label}: the name is not PascalCase", lines.get(key))
        if not entry.get("repositoryUrl"):
            emit(level, f"{label}: no repository is declared", lines.get(key))
        elif not github.repository_path(entry["repositoryUrl"]):
            emit(level, f"{label}: the repository is not hosted on GitHub", lines.get(key))

    repositories = sorted({
        entry["repositoryUrl"]
        for entry in candidates.values()
        if github.repository_path(entry.get("repositoryUrl") or "")
    })
    results = github.query(repositories, ["device.yml"], access_token)

    for key, entry in candidates.items():
        repository = entry.get("repositoryUrl")
        if repository not in results:
            continue
        level, label = "error" if key in changed else "warning", f"{key} {entry.get('name')}"
        result = results[repository]
        if result is None:
            emit(level, f"{label}: the repository is not public or does not exist", lines.get(key))
            continue
        if result["url"].lower() != repository.rstrip("/").lower():
            emit("warning", f"{label}: the repository has moved to {result['url']}", lines.get(key))
        if "device.yml" not in result["files"]:
            emit(level, f"{label}: no device.yml at the repository root", lines.get(key))
            continue
        try:
            device = yaml.safe_load(result["files"]["device.yml"])
        except yaml.YAMLError:
            emit(level, f"{label}: device.yml is not valid YAML", lines.get(key))
            continue
        device = device if isinstance(device, dict) else {}
        if device.get("whoAmI") != key:
            emit(level, f"{label}: device.yml declares WhoAmI {device.get('whoAmI')}", lines.get(key))
        declared_name = device.get("name", device.get("device"))
        if declared_name != entry.get("name"):
            emit(level, f"{label}: device.yml declares the name {declared_name}", lines.get(key))

    return diagnostics
