# WhoAmI registry

This repository serves as a registry for unique identifiers for devices using the Harp Protocol. The registry is published at [harp-tech.org/whoami](https://harp-tech.org/whoami), where the full table of reserved identifiers is rendered from `whoami.yml`.

## Reserving a `WhoAmI` identifier

To reserve a `WhoAmI` please submit a Pull Request with the desired identifier to the `whoami.yml` file in the root of this repository. Make sure you include a description of the device in the PR along with a source and project website, if applicable.

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