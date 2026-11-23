# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "harp-whoami[registration]",
#     "questionary",
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
from urllib.parse import urlparse

import questionary
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
NEW_OWNER = "+"
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
ENTRY_FIELDS = ("name", "repositoryUrl", "projectUrl")
MERGE_LINE = re.compile(r"^    <<: \*([a-z][a-z0-9-]*)\s*$")


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


def interactive():
    return sys.stdin.isatty() and sys.stdout.isatty()


def ask(question):
    answer = question.ask()
    if answer is None:
        fail("the registration was cancelled")
    return answer


def check_authors(text):
    return bool(text.strip()) or "Enter the name to show as the owner"


def check_owner_key(owners):
    def check(text):
        if text in owners:
            return f"{text} is already an owner"
        if not OWNER_PATTERN.match(text):
            return "Use lowercase letters, digits and hyphens, starting with a letter"
        return True

    return check


def ask_authors(owner=None):
    if not interactive():
        fail("a new owner needs --authors when the script does not run in a terminal")
    prompt = f"Name shown as the owner {owner}" if owner else "Name shown as the owner"
    return ask(questionary.text(prompt, validate=check_authors)).strip()


def choose_owner(owners, owner, authors, current=None):
    if owner is None:
        if not interactive():
            fail("specify --owner when the script does not run in a terminal")
        choices = [questionary.Choice(f"{value.get('authors')} ({key})", value=key) for key, value in owners.items()]
        choices += [questionary.Separator(), questionary.Choice("Add a new owner", value=NEW_OWNER)]
        default = current if current in owners else None
        owner = ask(questionary.select("Owner of the device", choices=choices, default=default))
        if owner != NEW_OWNER:
            return owner, None
        authors = ask_authors()
        default = re.sub(r"[^a-z0-9]", "", authors.lower())
        owner = ask(questionary.text("Key of the new owner", default=default, validate=check_owner_key(owners)))
        return owner, authors
    if owner in owners:
        return owner, None
    if not OWNER_PATTERN.match(owner):
        fail(f"the owner key {owner} must be lowercase letters, digits and hyphens")
    return owner, authors if authors else ask_authors(owner)


def same_url(first, second):
    return bool(first and second) and first.rstrip("/").lower() == second.rstrip("/").lower()


def normalize_url(text):
    text = text.strip()
    return text if URL_SCHEME.match(text) else f"https://{text}"


def check_url(url):
    if not urlparse(url).hostname:
        return f"{url} is not a valid address"
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers=HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT):
                return None
        except urllib.error.HTTPError as error:
            if method == "GET":
                return f"{url} answered with HTTP {error.code}"
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            return f"{url} could not be reached ({getattr(error, 'reason', error)})"
    return None


def validate_url(text):
    return not text.strip() or check_url(normalize_url(text)) or True


def choose_project_url(current, detected, given):
    if given is not None:
        url = normalize_url(given)
        problem = check_url(url)
        if problem:
            fail(problem)
        return url
    if not interactive():
        return detected or current
    if detected and not same_url(detected, current):
        if ask(questionary.confirm(f"Use {detected} as the project website?")):
            return detected
    hint = f"Enter to keep {current}" if current else "Enter to skip"
    answer = ask(questionary.text(f"Project website ({hint})", validate=validate_url, validate_while_typing=False))
    return normalize_url(answer) if answer.strip() else current


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


def add_owner(lines, owner, authors):
    block = Block(owner, [f"  {owner}: &{owner}", f"    authors: {authors}"])
    return insert_block(lines, "owners:", OWNER_KEY, str, block), ["owners:", *block.lines]


def remove_owner(lines, owner):
    start = lines.index(f"  {owner}: &{owner}")
    end = start + 1
    while end < len(lines) and lines[end].startswith("    "):
        end += 1
    return lines[:start] + lines[end:]


def owner_uses(text, owner):
    return sum(1 for line in text.splitlines() if (match := MERGE_LINE.match(line)) and match[1] == owner)


def entry_bounds(lines, whoami):
    start = next(index for index, line in enumerate(lines) if DEVICE_KEY.match(line) and line.strip() == f"{whoami}:")
    end = start + 1
    while end < len(lines) and lines[end].startswith("    "):
        end += 1
    return start, end


def entry_owner(text, whoami):
    lines = text.splitlines()
    start, end = entry_bounds(lines, whoami)
    return next((match[1] for line in lines[start + 1 : end] if (match := MERGE_LINE.match(line))), None)


def add_entry(text, whoami, name, repository, project_url, owner, authors):
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    added = []
    if authors is not None:
        lines, added = add_owner(lines, owner, authors)
    device_lines = [f"  {whoami}:", f"    <<: *{owner}", f"    name: {name}", f"    repositoryUrl: {repository}"]
    if project_url:
        device_lines.append(f"    projectUrl: {project_url}")
    lines = insert_block(lines, "devices:", DEVICE_KEY, int, Block(str(whoami), device_lines))
    added += ["devices:", *device_lines]
    return newline.join(lines) + newline, "\n".join(added)


def edit_entry(text, whoami, changes, authors=None):
    newline = "\r\n" if "\r\n" in text else "\n"
    previous = entry_owner(text, whoami)
    lines, shown = text.splitlines(), []
    if "owner" in changes and authors is not None:
        lines, shown = add_owner(lines, changes["owner"], authors)
    start, end = entry_bounds(lines, whoami)
    if "owner" in changes:
        found = [index for index in range(start + 1, end) if MERGE_LINE.match(lines[index])]
        if found:
            lines[found[0]] = f"    <<: *{changes['owner']}"
        else:
            lines.insert(start + 1, f"    <<: *{changes['owner']}")
            end += 1
    for field in ENTRY_FIELDS:
        if field not in changes:
            continue
        found = [index for index in range(start + 1, end) if lines[index].startswith(f"    {field}:")]
        if changes[field] is None:
            if found:
                del lines[found[0]]
                end -= 1
            continue
        line = f"    {field}: {changes[field]}"
        if found:
            lines[found[0]] = line
            continue
        earlier = ENTRY_FIELDS[: ENTRY_FIELDS.index(field)]
        anchors = [index for index in range(start + 1, end) if lines[index].split(":")[0].strip() in earlier]
        position = max(anchors) + 1 if anchors else end
        lines.insert(position, line)
        end += 1
    shown += ["devices:", *lines[start:end]]
    updated = newline.join(lines) + newline
    if previous and "owner" in changes and not owner_uses(updated, previous):
        updated = newline.join(remove_owner(updated.splitlines(), previous)) + newline
    return updated, "\n".join(shown)


def show_changes(text, whoami, entry, current_owner, changes):
    if not changes:
        print(f"The entry of {whoami} {entry.get('name')} is up to date")
        return
    print("Changes to the entry:")
    if "owner" in changes:
        print(f"  owner: {current_owner or '(none)'} -> {changes['owner']}")
        if current_owner and owner_uses(text, current_owner) == 1:
            print(f"  owners: {current_owner} is removed, since no other device uses it")
    for field in ENTRY_FIELDS:
        if field in changes:
            print(f"  {field}: {entry.get(field) or '(none)'} -> {changes[field] or '(removed)'}")


def main():
    parser = argparse.ArgumentParser(
        description="Adds the device in the current repository to the WhoAmI registry, or updates its entry."
    )
    parser.add_argument(
        "--owner", help="the key of an existing or new owner, which also changes the owner of a registered device"
    )
    parser.add_argument("--authors", help="the name shown as the owner, when adding a new owner")
    parser.add_argument("--project-url", help="the address of the home page of the device")
    parser.add_argument(
        "--remove-project-url", action="store_true", help="remove the address of the home page of a registered device"
    )
    parser.add_argument(
        "--edit", action="store_true", help="change the owner or remove the home page of a registered device"
    )
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
    for key, entry in devices.items():
        if key != whoami and str(entry.get("name", "")).lower() == name.lower():
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
    try:
        detected = result["homepage"] or github.pages_url(repository, access_token)
    except (urllib.error.URLError, TimeoutError):
        detected = None

    entry = devices.get(whoami)
    if entry is None:
        print(f"Registering {whoami} {name} from {repository}")
        owner, authors = choose_owner(owners, args.owner, args.authors)
        project_url = choose_project_url(None, detected, args.project_url)
        updated, added = add_entry(text, whoami, name, repository, project_url, owner, authors)
        action = "register"
    else:
        print(f"{whoami} {entry.get('name')} is already registered, checking its entry")
        current_owner = entry_owner(text, whoami)
        project_url = choose_project_url(entry.get("projectUrl"), detected, args.project_url)
        values = {"name": name, "repositoryUrl": repository, "projectUrl": project_url}
        changes = {
            field: value
            for field, value in values.items()
            if value and value != entry.get(field) and not same_url(value, entry.get(field))
        }
        authors = None
        if args.owner and args.owner != current_owner:
            changes["owner"], authors = choose_owner(owners, args.owner, args.authors)
        if args.remove_project_url and entry.get("projectUrl"):
            changes["projectUrl"] = None
        if interactive():
            edit = args.edit
            if not edit:
                show_changes(text, whoami, entry, current_owner, changes)
                choices = [
                    questionary.Choice("Apply the changes" if changes else "Done", value="apply"),
                    questionary.Choice("Change the owner or remove the project website", value="edit"),
                    questionary.Choice("Cancel", value="cancel"),
                ]
                choice = ask(questionary.select("What would you like to do?", choices=choices))
                if choice == "cancel":
                    return
                edit = choice == "edit"
            if edit:
                owner, new_authors = choose_owner(owners, None, None, current=current_owner)
                changes.pop("owner", None)
                authors = None
                if owner != current_owner:
                    changes["owner"], authors = owner, new_authors
                website = changes.get("projectUrl", entry.get("projectUrl"))
                if website and ask(questionary.confirm(f"Remove the project website {website}?", default=False)):
                    if entry.get("projectUrl"):
                        changes["projectUrl"] = None
                    else:
                        changes.pop("projectUrl")
                show_changes(text, whoami, entry, current_owner, changes)
                if changes and not ask(questionary.confirm("Apply the changes?")):
                    return
        else:
            show_changes(text, whoami, entry, current_owner, changes)
        if not changes:
            return
        updated, added = edit_entry(text, whoami, changes, authors)
        action = "update"
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

    print(f"{whoami} {name} is ready to {action}:")
    print(added)
    if args.output:
        folder = Path(args.output)
        for path in (folder / REGISTRY_FILE, folder / MODULE_FILE):
            if not path.exists():
                fail(f"no {path}, so specify the folder of a clone of the registry repository")
        if interactive() and not ask(questionary.confirm(f"Write the updated registry to {folder}?")):
            return
        write(folder / REGISTRY_FILE, updated)
        write(folder / MODULE_FILE, module)
        print(f"Updated {folder / REGISTRY_FILE} and regenerated {folder / MODULE_FILE}")


if __name__ == "__main__":
    main()
