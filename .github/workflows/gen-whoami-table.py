# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas==3.0.5",
#     "pyyaml==6.0.3",
#     "tabulate==0.10.0",
# ]
# ///

import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import escape
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import yaml

APP_TYPES = {
    "dotnetTool": ("https://www.nuget.org/packages/{package}", "bi-box-seam", "{package} on nuget.org"),
}
REPOSITORY_FILES = {
    "device": ("device.yml",),
    "license": ("LICENSE", "LICENSE.md", "LICENSE.txt"),
}
GONE = {404, 410}
HEADERS = {"User-Agent": "whoami-link-check"}
TIMEOUT = 20


def warn(message):
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning::{message}")
    else:
        print(f"warning: {message}", file=sys.stderr)


def probe(url):
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers=HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT):
                return "ok"
        except urllib.error.HTTPError as error:
            if method == "HEAD":
                continue
            return "gone" if error.code in GONE else f"HTTP {error.code}"
        except (urllib.error.URLError, TimeoutError) as error:
            return str(getattr(error, "reason", error))
    return "unknown"


def check_links(urls):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(zip(urls, pool.map(probe, urls)))
    for url, result in sorted(results.items()):
        if result == "gone":
            warn(f"{url} no longer resolves and is left out of the table")
        elif result != "ok":
            warn(f"{url} could not be checked ({result}) and is kept")
    return {url for url, result in results.items() if result != "gone"}


def github_path(repository):
    url = urlparse(repository)
    return url.path.strip("/") if url.hostname == "github.com" else None


def find_repository_files(repositories):
    candidates = {
        (repository, kind, name): f"https://raw.githubusercontent.com/{github_path(repository)}/HEAD/{name}"
        for repository in repositories
        if github_path(repository)
        for kind, names in REPOSITORY_FILES.items()
        for name in names
    }
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(zip(candidates, pool.map(probe, candidates.values())))
    files = {}
    for (repository, kind, name), result in results.items():
        if result == "ok":
            files.setdefault((repository, kind), f"{repository.rstrip('/')}/blob/HEAD/{name}")
    return files


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
    url = files.get((repository, kind))
    return icon_link(url, icon, label) if url else icon_unavailable(icon, f"{label} not available")


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
    urls = {url for url in devices["repositoryUrl"] if url}
    urls |= {url for url in devices["projectUrl"] if url}
    urls |= {url for url in map(app_url, apps) if url}
    alive = check_links(sorted(urls))
    files = find_repository_files(sorted(url for url in devices["repositoryUrl"] if url in alive))
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
