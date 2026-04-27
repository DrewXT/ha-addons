# Contributing

Thanks for helping improve these add-ons!

## Reporting Issues

Open an issue and include:
- Add-on version (from the **Info** tab in HA)
- HA version
- The full log from the add-on **Log** tab
- What you expected vs what happened

## Making Changes

1. Fork the repo and create a branch: `git checkout -b fix/my-change`
2. Make your changes.
3. Test locally by copying the add-on folder to your HA `addons/` directory and rebuilding.
4. Update the `version` in `config.yaml` following [semver](https://semver.org/) and add a `### x.y.z` entry to the `README.md` changelog.
5. Open a pull request — CI will validate the config and run a Docker build check automatically.

## Releasing (maintainer)

Tag the commit with the add-on name and version:

```bash
git tag speedtest-mqtt/v1.0.1
git push origin speedtest-mqtt/v1.0.1
```

The release workflow will create a GitHub Release automatically, pulling the
changelog entry from the README.
