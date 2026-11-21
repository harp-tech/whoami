# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas==3.0.5",
#     "pyyaml==6.0.3",
#     "tabulate==0.10.0",
# ]
# ///

import sys
from pathlib import Path
import pandas as pd
import yaml

def format_links(repository, website):
    links = []
    if repository:
        links.append(f"[Repository]({repository})")
    if website:
        links.append(f"[Website]({website})")
    return ", ".join(links)


def main(argv):
    path_to_whoami = argv[0]
    path_to_table = Path(argv[1])
    yml = yaml.load(open(path_to_whoami, encoding="utf-8"), yaml.Loader)
    devices = pd.DataFrame.from_dict(yml["devices"], orient="index").fillna("")
    devices.index.names = ["WhoAmI"]
    table = pd.DataFrame(
        {
            "Name": devices["name"],
            "Authors": devices["authors"],
            "Copyright": devices["copyright"],
            "Links": [
                format_links(repository, website)
                for repository, website in zip(
                    devices["repositoryUrl"], devices["projectUrl"]
                )
            ],
        },
        index=devices.index,
    ).sort_index()
    path_to_table.parent.mkdir(parents=True, exist_ok=True)
    table.to_markdown(path_to_table)


if __name__ == "__main__":
    main(sys.argv[1:])
