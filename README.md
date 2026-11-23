# WhoAmI registry

This repository serves as a registry for unique identifiers for devices using the Harp Protocol. The registry is published at [harp-tech.org/whoami](https://harp-tech.org/whoami), where a table of the registered devices is rendered from `whoami.yml`.

## Reserving a `WhoAmI` identifier

A `WhoAmI` is reserved by adding the device to the `whoami.yml` file in the root of this repository through a pull request. Each new entry must:

- Use an identifier from 100 to 65535 that is not already reserved, keeping the devices sorted by `WhoAmI`
- Declare an owner, as described in the section on device ownership
- Have a PascalCase name that no other device uses
- Declare a public GitHub repository with a `device.yml` at its root, whose `whoAmI` and name match the entry

These requirements are checked automatically on every pull request.

### Using the registration script

The easiest way to reserve an identifier, or to update the entry of a registered device, is to run the registration script from the root of the device repository:

```
uv run https://harp-tech.org/whoami/register.py
```

The script reads the `WhoAmI` and name from `device.yml` and the repository from the `origin` remote, then asks for the owner and the project website. It checks the entry against the requirements above and offers to open the pull request from a fork of this repository. When the device is already registered, the script compares its entry with `device.yml` and the repository, and offers to update it.

The script needs [uv](https://docs.astral.sh/uv/), git, and a GitHub account signed in with the [GitHub CLI](https://cli.github.com/), or a token in the `GITHUB_TOKEN` environment variable. Run it with `--help` to see all of its arguments.

### Editing the registry by hand

To edit `whoami.yml` directly, open a pull request with the new or updated entry, and update the generated registry module by running `uv run harp-whoami generate` at the root of this repository before committing.

## Declaring device ownership

Ownership is declared once in the `owners` section at the top of `whoami.yml` and referenced from each device with a merge key:

```yaml
owners:
  harptech: &harptech
    authors: harp-tech

devices:
  1216:
    <<: *harptech
    name: Behavior
    repositoryUrl: https://github.com/harp-tech/device.behavior
    projectUrl: https://harp-tech.org/device.behavior
```

The `authors` value is the name shown as the owner in the published table. If your organization is not listed, add it to `owners` in the same pull request, keeping the entries in alphabetical order. Do not set `authors` directly on a device.

## Declaring a device app

A device declares the app sanctioned by its maintainers in an optional `app` section:

```yaml
    app:
      type: dotnetTool
      package: Harp.Behavior.App
```

The `type` states the kind of app. In this case `dotnetTool` is an app published as a .NET tool and resolved from nuget.org, and `package` is the package identifier.