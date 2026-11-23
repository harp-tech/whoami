import argparse
import json
import subprocess
import sys
import urllib.error
from typing import NoReturn

from harp.whoami import github
from harp.whoami.generation import MODULE_FILE, REGISTRY_FILE, generate

try:
    import yaml

    from harp.whoami.validation import Diagnostic, validate
except ModuleNotFoundError as ex:
    raise SystemExit(f"error: harp-whoami needs the registration extra, from harp-whoami[registration] ({ex})")


def report(path, diagnostic):
    location = f"{path}:{diagnostic.line}" if diagnostic.line else path
    print(f"{location}: {diagnostic.level}: {diagnostic.message}", file=sys.stderr)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def base_devices(path, ref):
    merge_base = git("merge-base", "HEAD", ref)
    relative = git("ls-files", "--full-name", path)
    return (yaml.safe_load(git("show", f"{merge_base}:{relative}")) or {}).get("devices") or {}


def run_validate(args):
    errors = 0

    def fail(message) -> NoReturn:
        report(args.registry, Diagnostic("error", message))
        sys.exit(1)

    try:
        base = base_devices(args.registry, args.base)
    except subprocess.CalledProcessError as error:
        fail(f"changes cannot be found against {args.base} ({error.stderr.strip()})")
    access_token = github.token()
    if not access_token:
        fail("repositories cannot be checked without a GitHub token, so set GITHUB_TOKEN or sign in with the GitHub CLI")
    text = open(args.registry, encoding="utf-8").read()
    schema = json.load(open(args.schema, encoding="utf-8"))
    try:
        diagnostics = validate(text, schema, base, access_token)
    except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
        fail(f"repositories could not be checked ({getattr(error, 'reason', error)})")
    for diagnostic in diagnostics:
        report(args.registry, diagnostic)
        errors += diagnostic.level == "error"
    sys.exit(1 if errors else 0)


def run_generate(args):
    try:
        registry = yaml.safe_load(open(args.registry, encoding="utf-8")) or {}
        source = generate(registry)
    except (OSError, yaml.YAMLError, ValueError) as error:
        report(args.registry, Diagnostic("error", f"the registry module could not be generated ({error})"))
        sys.exit(1)
    with open(args.output, "w", encoding="utf-8") as file:
        file.write(source)


def main():
    parser = argparse.ArgumentParser(prog="harp-whoami", description="Tools for the WhoAmI registry.")
    commands = parser.add_subparsers(required=True)
    command = commands.add_parser("validate", description="Validates the WhoAmI registry.")
    command.add_argument("registry", help="the registry file to validate")
    command.add_argument("schema", help="the JSON Schema of the registry")
    command.add_argument("--base", default="origin/main", help="the branch that changed entries are found against")
    command.set_defaults(run=run_validate)
    command = commands.add_parser("generate", description="Generates the module declaring the WhoAmI identifiers.")
    command.add_argument("registry", nargs="?", default=REGISTRY_FILE, help="the registry file to read")
    command.add_argument("output", nargs="?", default=MODULE_FILE, help="the module file to write")
    command.set_defaults(run=run_generate)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
