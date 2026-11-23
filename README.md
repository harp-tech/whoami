# WhoAmI registry

This repository serves as a registry for unique identifiers for devices using the Harp Protocol. The registry is published at [harp-tech.org/whoami](https://harp-tech.org/whoami), where a table of the registered devices is rendered from `whoami.yml`.

## Reserving a `WhoAmI` identifier

To reserve a `WhoAmI` please submit a Pull Request adding the device to the `whoami.yml` file in the root of this repository, along with a description of the device. Each new entry must:

- Use an identifier from 100 to 65535 that is not already reserved, keeping the devices sorted by `WhoAmI`
- Declare an owner, as described in the next section
- Have a PascalCase name that no other device uses
- Declare a public GitHub repository with a `device.yml` at its root, whose `whoAmI` and name match the entry
- Update the generated registry module by running `uv run harp-whoami generate` at the root of this repository

These requirements are checked automatically on every Pull Request.

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

The `authors` value is the name shown as the owner in the published table. If your organization is not listed, add it to `owners` in the same Pull Request, keeping the entries in alphabetical order. Do not set `authors` directly on a device.

## Declaring a device app

A device declares the app sanctioned by its maintainers in an optional `app` section:

```yaml
    app:
      type: dotnetTool
      package: Harp.Behavior.App
```

The `type` states the kind of app. In this case `dotnetTool` is an app published as a .NET tool and resolved from nuget.org, and `package` is the package identifier.