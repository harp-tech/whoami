# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas==2.2.3",
#     "pyyaml==6.0.2",
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
    d = d.fillna("")
    d.to_markdown("whoami.md")


if __name__ == "__main__":
    main(sys.argv[1:])
