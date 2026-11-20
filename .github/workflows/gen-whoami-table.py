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


def main(argv):
    path_to_whoami = argv[0]
    path_to_table = Path(argv[1])
    yml = yaml.load(open(path_to_whoami, encoding="utf-8"), yaml.Loader)
    d = pd.DataFrame.from_dict(yml["devices"], orient="index")
    d.index.names = ["WhoAmI"]
    d = d[["name", "authors", "copyright", "repositoryUrl", "projectUrl"]]
    d = d.fillna("")
    d = d.sort_index()
    path_to_table.parent.mkdir(parents=True, exist_ok=True)
    d.to_markdown(path_to_table)


if __name__ == "__main__":
    main(sys.argv[1:])
