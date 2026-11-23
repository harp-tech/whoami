import keyword
from collections.abc import Mapping
from typing import Any

REGISTRY_FILE = "whoami.yml"
MODULE_FILE = "src/harp/whoami/registry.py"
DEVICE_FIELDS = {
    "name": "name",
    "authors": "authors",
    "repositoryUrl": "repository_url",
    "projectUrl": "project_url",
}
APP_TYPES = {
    "dotnetTool": "DotnetToolApp",
}


def app_literal(key, app):
    app_type = app.get("type")
    if app_type not in APP_TYPES:
        raise ValueError(f"{key}: the app type {app_type} is not supported")
    arguments = ", ".join(f"{field}={value!r}" for field, value in app.items() if field != "type")
    return f"{APP_TYPES[app_type]}({arguments})"


def generate(registry: Mapping[str, Any]) -> str:
    """Generates the source of the module declaring the WhoAmI identifiers of a registry.

    Raises ValueError if the name of a device cannot be declared as a Python identifier,
    or if the type of its app is not supported.
    """
    devices = {
        key: entry
        for key, entry in sorted((registry.get("devices") or {}).items())
        if not (isinstance(entry, dict) and entry.get("legacy"))
    }
    names = set()
    for key, entry in devices.items():
        name = entry.get("name") if isinstance(entry, dict) else None
        if not isinstance(name, str):
            raise ValueError(f"{key}: the entry has no name")
        if not name.isidentifier() or keyword.iskeyword(name):
            raise ValueError(f"{key} {name}: the name is not a valid Python identifier")
        if name in names:
            raise ValueError(f"{key} {name}: the name is already used")
        names.add(name)
    records, app_types = [], set()
    for key, entry in devices.items():
        arguments = [f"whoami=WhoAmI.{entry['name']}"]
        arguments += [f"{field}={entry[source]!r}" for source, field in DEVICE_FIELDS.items() if source in entry]
        if entry.get("app"):
            arguments.append(f"app={app_literal(key, entry['app'])}")
            app_types.add(APP_TYPES[entry["app"]["type"]])
        records.append(f"    WhoAmI.{entry['name']}: DeviceRecord({', '.join(arguments)}),")
    imports = ", ".join(sorted({"DeviceRecord", *app_types}))
    lines = [
        f'"""The registry of WhoAmI identifiers, generated from {REGISTRY_FILE} by harp-whoami generate."""',
        "",
        "from enum import IntEnum",
        "from types import MappingProxyType",
        "",
        f"from harp.whoami import {imports}",
        "",
        "",
        "class WhoAmI(IntEnum):",
        '    """The WhoAmI identifiers of the registered devices."""',
        "",
    ]
    lines += [f"    {entry['name']} = {key}" for key, entry in devices.items()]
    lines += ["", "", "DEVICES = MappingProxyType({", *records, "})"]
    lines += ['"""The record of each registered device."""', ""]
    return "\n".join(lines)
