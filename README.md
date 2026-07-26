# `WhoAmI`

This repository serves as a registry for unique identifiers for devices using the Harp Protocol.

## Reserving a `WhoAmI` Identifier

To reserve a `WhoAmI` please submit a Pull Request with the desired identifier to the `whoami.yml` file in the root of this repository. Make sure you include a description of the device in the PR along with a source and project website, if applicable.

## Declaring Device Ownership

Ownership is declared once in the `owners` section at the top of `whoami.yml` and referenced from each device with a merge key:

```yaml
owners:
  harptech: &harptech
    authors: harp-tech
    copyright: harp-tech

devices:
  1216:
    <<: *harptech
    name: Behavior
    repositoryUrl: https://github.com/harp-tech/device.behavior
    projectUrl: https://github.com/harp-tech/device.behavior
```

An owner key identifies a combination of `authors` and `copyright` rather than an organization, so a device copyrighted to a different party than its authors needs its own key. If your combination is not listed, add it to `owners` in the same Pull Request, keeping the entries in alphabetical order. Do not set `authors` or `copyright` directly on a device.