# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "harp-whoami[registration]",
# ]
# ///

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import NoReturn

import yaml

from harp.whoami import github
from harp.whoami.generation import MODULE_FILE, REGISTRY_FILE, generate
from harp.whoami.validation import validate

REGISTRY_URL = "https://harp-tech.org/whoami/whoami.yml"
SCHEMA_URL = "https://harp-tech.org/whoami/whoami.json"
DEVICE_FILE = "device.yml"
HEADERS = {"User-Agent": "whoami-register"}
TIMEOUT = 20
REMOTE_PATTERN = re.compile(r"^(?:https://|ssh://git@|git@)github\.com[/:](?P<path>[^/]+/[^/]+?)(?:\.git)?/?$")
OWNER_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
DEVICE_KEY = re.compile(r"^  (\d+):\s*$")
OWNER_KEY = re.compile(r"^  ([a-z][a-z0-9-]*): &")


def fail(message) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def read(location):
    if re.match(r"^https?://", location):
        request = urllib.request.Request(location, headers=HEADERS)
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8")
    return Path(location).read_text(encoding="utf-8")


def write(path, text):
    newline = "\r\n" if b"\r\n" in path.read_bytes() else "\n"
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", newline).encode("utf-8"))


def read_device():
    path = Path(DEVICE_FILE)
    if not path.exists():
        fail(f"no {DEVICE_FILE} in the current folder, so run this script from the root of a device repository")
    device = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    whoami, name = device.get("whoAmI"), device.get("name", device.get("device"))
    if not isinstance(whoami, int) or not name:
        fail(f"{DEVICE_FILE} does not declare whoAmI and name")
    return whoami, name


def read_repository():
    try:
        remote = subprocess.run(
            ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        fail("the repository has no origin remote")
    match = REMOTE_PATTERN.match(remote)
    if not match:
        fail(f"the origin remote {remote} is not a GitHub repository")
    return f"https://github.com/{match['path']}"


def choose_owner(owners, owner, authors):
    if owner is None:
        print("Owners:")
        for key, value in owners.items():
            print(f"  {key}: {value.get('authors')}")
        owner = input("Choose an owner, or enter a new key to add one: ").strip()
    if owner in owners:
        return owner, None
    if not OWNER_PATTERN.match(owner):
        fail(f"the owner key {owner} must be lowercase letters, digits and hyphens")
    if authors is None:
        authors = input(f"Enter the name shown as the owner for {owner}: ").strip()
    if not authors:
        fail("a new owner needs a name to show as the owner")
    return owner, authors


def section_end(lines, start):
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end].startswith(" ")):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return end


def insert_block(lines, header, pattern, sort_key, block):
    start = lines.index(header)
    end = section_end(lines, start)
    for index in range(start + 1, end):
        match = pattern.match(lines[index])
        if match and sort_key(match[1]) > sort_key(block.key):
            return lines[:index] + block.lines + lines[index:]
    return lines[:end] + block.lines + lines[end:]


class Block:
    def __init__(self, key, lines):
        self.key = key
        self.lines = lines


def add_entry(text, whoami, name, repository, owner, authors):
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    added = []
    if authors is not None:
        owner_block = Block(owner, [f"  {owner}: &{owner}", f"    authors: {authors}"])
        lines = insert_block(lines, "owners:", OWNER_KEY, str, owner_block)
        added += ["owners:", *owner_block.lines]
    device_block = Block(str(whoami), [
        f"  {whoami}:",
        f"    <<: *{owner}",
        f"    name: {name}",
        f"    repositoryUrl: {repository}",
    ])
    lines = insert_block(lines, "devices:", DEVICE_KEY, int, device_block)
    added += ["devices:", *device_block.lines]
    return newline.join(lines) + newline, "\n".join(added)


def main():
    parser = argparse.ArgumentParser(description="Adds the device in the current repository to the WhoAmI registry.")
    parser.add_argument("--owner", help="the key of an existing owner, or of a new owner to add")
    parser.add_argument("--authors", help="the name shown as the owner, when adding a new owner")
    parser.add_argument("--output", help="the folder of a clone of the registry repository to write the updated files to")
    parser.add_argument("--registry", default=REGISTRY_URL, help="the address or path of the registry to update")
    parser.add_argument("--schema", default=SCHEMA_URL, help="the address or path of the registry schema")
    args = parser.parse_args()

    whoami, name = read_device()
    repository = read_repository()
    try:
        text = read(args.registry)
        schema = json.loads(read(args.schema))
    except (OSError, urllib.error.URLError) as error:
        fail(f"the registry could not be read ({getattr(error, 'reason', error)})")
    registry = yaml.safe_load(text) or {}
    owners, devices = registry.get("owners") or {}, registry.get("devices") or {}
    if whoami in devices:
        fail(f"WhoAmI {whoami} is already registered to {devices[whoami].get('name')}")
    for key, entry in devices.items():
        if str(entry.get("name", "")).lower() == name.lower():
            fail(f"the name {name} is already registered to WhoAmI {key}")

    access_token = github.token()
    if not access_token:
        fail("repositories cannot be checked without a GitHub token, so set GITHUB_TOKEN or sign in with the GitHub CLI")
    try:
        result = github.query([repository], [], access_token)[repository]
    except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
        fail(f"the repository could not be checked ({getattr(error, 'reason', error)})")
    if result is None:
        fail(f"{repository} is not public or does not exist")
    repository = result["url"]

    owner, authors = choose_owner(owners, args.owner, args.authors)
    updated, added = add_entry(text, whoami, name, repository, owner, authors)
    try:
        diagnostics = validate(updated, schema, devices, access_token)
    except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
        fail(f"repositories could not be checked ({getattr(error, 'reason', error)})")
    errors = 0
    for diagnostic in diagnostics:
        if diagnostic.level == "error" or diagnostic.message.startswith(f"{whoami} "):
            print(f"{diagnostic.level}: {diagnostic.message}", file=sys.stderr)
            errors += diagnostic.level == "error"
    if errors:
        sys.exit(1)

    try:
        module = generate(yaml.safe_load(updated))
    except ValueError as error:
        fail(f"the registry module could not be generated ({error})")

    if args.output:
        folder = Path(args.output)
        for path in (folder / REGISTRY_FILE, folder / MODULE_FILE):
            if not path.exists():
                fail(f"no {path}, so specify the folder of a clone of the registry repository")
        write(folder / REGISTRY_FILE, updated)
        write(folder / MODULE_FILE, module)
        print(f"Added {whoami} {name} to {folder / REGISTRY_FILE} and regenerated {folder / MODULE_FILE}")
    else:
        print(f"{whoami} {name} is ready to register:")
        print(added)


if __name__ == "__main__":
    main()
