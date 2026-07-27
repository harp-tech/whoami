# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas==3.0.5",
#     "pyyaml==6.0.3",
#     "tabulate==0.10.0",
# ]
# ///

import sys
import pandas as pd
import yaml


def main(argv):
    path_to_whoami = argv[0]
    yml = yaml.load(open(path_to_whoami, encoding="utf-8"), yaml.Loader)
    d = pd.DataFrame.from_dict(yml["devices"], orient="index")
    d.index.names = ["WhoAmI"]
    d = d[["name", "authors", "copyright", "repositoryUrl", "projectUrl"]]
    d = d.fillna("")
    d = d.sort_index()
    d.to_markdown("whoami.md")


if __name__ == "__main__":
    main(sys.argv[1:])
