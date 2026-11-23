import json
import os
import subprocess
import urllib.error
import urllib.request
from http import HTTPStatus
from urllib.parse import urlparse

API_URL = "https://api.github.com"
GRAPHQL_URL = f"{API_URL}/graphql"
HEADERS = {"User-Agent": "whoami-registry"}
TIMEOUT = 20


def repository_path(url):
    """Returns the owner and name of a GitHub repository from its address, or None for other hosts."""
    parsed = urlparse(url)
    return parsed.path.strip("/") if parsed.hostname == "github.com" else None


def token():
    """Returns the GitHub token from GITHUB_TOKEN or the GitHub CLI, or None if neither has one."""
    value = os.environ.get("GITHUB_TOKEN")
    if value:
        return value
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def query(repositories, files, access_token):
    """Returns each public repository with its canonical URL, website, license and the text of the
    specified files found at its root, or None when the repository is private or does not exist."""
    fields = "isPrivate url homepageUrl licenseInfo { spdxId name } " + " ".join(
        f'f{i}: object(expression: "HEAD:{name}") {{ ... on Blob {{ text }} }}' for i, name in enumerate(files)
    )
    variables, declarations, selections = {}, [], []
    for i, repository in enumerate(repositories):
        variables[f"owner{i}"], variables[f"name{i}"] = repository_path(repository).split("/", 1)
        declarations.append(f"$owner{i}: String!, $name{i}: String!")
        selections.append(f"r{i}: repository(owner: $owner{i}, name: $name{i}) {{ {fields} }}")
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({
            "query": f"query({', '.join(declarations)}) {{ {' '.join(selections)} }}",
            "variables": variables,
        }).encode(),
        headers={**HEADERS, "Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        result = json.load(response)
    for error in result.get("errors", []):
        if error.get("type") != "NOT_FOUND":
            raise RuntimeError(error.get("message"))
    data = result.get("data") or {}
    found = {}
    for i, repository in enumerate(repositories):
        entry = data.get(f"r{i}")
        if not entry or entry["isPrivate"]:
            found[repository] = None
            continue
        texts = {}
        for j, name in enumerate(files):
            blob = entry[f"f{j}"] or {}
            if blob.get("text") is not None:
                texts[name] = blob["text"]
        found[repository] = {
            "url": entry["url"],
            "homepage": entry["homepageUrl"] or None,
            "license": entry["licenseInfo"],
            "files": texts,
        }
    return found


def pages_url(repository, access_token):
    """Returns the address of the GitHub Pages site of a repository, or None if it has none."""
    request = urllib.request.Request(
        f"{API_URL}/repos/{repository_path(repository)}/pages",
        headers={**HEADERS, "Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.load(response).get("html_url")
    except urllib.error.HTTPError as error:
        if error.code == HTTPStatus.NOT_FOUND:
            return None
        raise
