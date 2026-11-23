import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import escape
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import yaml

from harp.whoami import github

APP_TYPES = {
    "dotnetTool": ("https://www.nuget.org/packages/{package}", "bi-box-seam", "{package} on nuget.org"),
}
REPOSITORY_FILES = {
    "device": ("device.yml",),
    "license": ("LICENSE", "LICENSE.md", "LICENSE.txt"),
}
HEADERS = {"User-Agent": "whoami-link-check"}
TIMEOUT = 20


def warn(message):
    print(f"warning: {message}", file=sys.stderr)


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def probe(url):
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers=HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT):
                return "ok"
        except urllib.error.HTTPError as error:
            if method == "HEAD":
                continue
            return "missing" if error.code in (HTTPStatus.NOT_FOUND, HTTPStatus.GONE) else f"HTTP {error.code}"
        except (urllib.error.URLError, TimeoutError) as error:
            return str(getattr(error, "reason", error))
    return "unknown"


def check_links(urls):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(zip(urls, pool.map(probe, urls)))
    for url, result in sorted(results.items()):
        if result == "missing":
            warn(f"{url} does not resolve and is left out of the table")
    unchecked = [f"{url} ({result})" for url, result in sorted(results.items()) if result not in ("ok", "missing")]
    if unchecked:
        fail(f"links could not be checked: {', '.join(unchecked)}")
    return {url for url, result in results.items() if result == "ok"}


def check_repositories(repositories):
    access_token = github.token()
    if not access_token:
        fail("repositories cannot be checked without a GitHub token, so set GITHUB_TOKEN or sign in with the GitHub CLI")
    names = [name for candidates in REPOSITORY_FILES.values() for name in candidates]
    try:
        results = github.query(repositories, names, access_token)
    except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
        fail(f"repositories could not be checked ({getattr(error, 'reason', error)})")
    alive, files = set(), {}
    for repository, result in sorted(results.items()):
        if result is None:
            warn(f"{repository} is not publicly available and is left out of the table")
            continue
        alive.add(repository)
        url = result["url"]
        if url.lower() != repository.rstrip("/").lower():
            warn(f"{repository} has moved to {url}")
        license_info = result["license"] or {}
        labels = {
            "device": "Device file",
            "license": license_info["name"] if license_info.get("spdxId") not in (None, "NOASSERTION") else "License",
        }
        for kind, candidates in REPOSITORY_FILES.items():
            name = next((name for name in candidates if name in result["files"]), None)
            if name:
                files[(repository, kind)] = (f"{url}/blob/HEAD/{name}", labels[kind])
    return alive, files


def icon_link(url, icon, label):
    label = escape(label)
    return f'<a class="icon" href="{escape(url)}" title="{label}" aria-label="{label}"><i class="bi {icon}"></i></a>'


def icon_unavailable(icon, label):
    label = escape(label)
    return f'<span class="icon icon-unavailable" role="img" title="{label}" aria-label="{label}"><i class="bi {icon}"></i></span>'


def icon_group(icons):
    return f'<span class="icon-links">{"".join(icons)}</span>'


def app_url(app):
    if not app:
        return None
    if app["type"] not in APP_TYPES:
        warn(f"app type {app['type']} has no icon and is left out of the table")
        return None
    return APP_TYPES[app["type"]][0].format(package=app["package"])


def format_app(app, alive):
    url = app_url(app)
    if url not in alive:
        return icon_group([icon_unavailable("bi-box-seam", "App not available")])
    _, icon, label = APP_TYPES[app["type"]]
    return icon_group([icon_link(url, icon, label.format(package=app["package"]))])


def repository_file_icon(files, repository, kind, icon, label):
    found = files.get((repository, kind))
    if not found:
        return icon_unavailable(icon, f"{label} not available")
    url, found_label = found
    return icon_link(url, icon, found_label)


def format_links(repository, website, alive, files):
    if repository in alive:
        icon = "bi-github" if urlparse(repository).hostname == "github.com" else "bi-git"
        repository_icon = icon_link(repository, icon, "Repository")
    else:
        repository_icon = icon_unavailable("bi-github", "Repository not available")
    if website in alive and website != repository:
        website_icon = icon_link(website, "bi-globe2", "Website")
    else:
        website_icon = icon_unavailable("bi-globe2", "Website not available")
    return icon_group([
        repository_icon,
        repository_file_icon(files, repository, "device", "bi-filetype-yml", "Device file"),
        repository_file_icon(files, repository, "license", "bi-file-earmark-text", "License"),
        website_icon,
    ])


def main(argv):
    path_to_whoami = argv[0]
    path_to_table = Path(argv[1])
    yml = yaml.load(open(path_to_whoami, encoding="utf-8"), yaml.Loader)
    devices = pd.DataFrame.from_dict(yml["devices"], orient="index").fillna("")
    devices.index.names = ["WhoAmI"]
    apps = devices["app"] if "app" in devices else pd.Series("", index=devices.index)
    repositories = sorted({url for url in devices["repositoryUrl"] if url})
    alive, files = check_repositories([url for url in repositories if github.repository_path(url)])
    links = {url for url in repositories if not github.repository_path(url)}
    links |= {url for url in devices["projectUrl"] if url and url not in repositories}
    links |= {url for url in map(app_url, apps) if url}
    alive |= check_links(sorted(links))
    listed = pd.Series(
        [
            app_url(app) in alive or repository in alive or website in alive
            for app, repository, website in zip(apps, devices["repositoryUrl"], devices["projectUrl"])
        ],
        index=devices.index,
    )
    table = pd.DataFrame(
        {
            "Name": devices["name"],
            "Owner": devices["authors"],
            "App": [format_app(app, alive) for app in apps],
            "Links": [
                format_links(repository, website, alive, files)
                for repository, website in zip(
                    devices["repositoryUrl"], devices["projectUrl"]
                )
            ],
        },
        index=devices.index,
    )[listed].sort_index()
    path_to_table.parent.mkdir(parents=True, exist_ok=True)
    table.to_markdown(path_to_table, colalign=("right", "left", "left", "center", "left"))


if __name__ == "__main__":
    main(sys.argv[1:])
