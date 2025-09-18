# Upgrading From Previous Versions

## Upgrading

This guide is intended to help you upgrade from version 1.x of the software to 2.x versions.

The steps, depending on your version

- moving customized files to a user directory
- installing the remote control software

### Moving Customized Files

If you have an older version of the software (V1.6 or earlier), it is highly recommended that you copy your configuration files into the user configuration directory.

The user configuration files and directory are explained in the `~/weather_map/config.json` section.

If you have not already migrated to a version that has the user configuration files, open a command line on the Raspberry Pi and execute the following commands:

```bash
cd ~/categorical-sectional
mkdir ~/weather_map
cp data/*.json ~/weather_map/
```

### Updating The Stations File Location

Please note that you may need to modify the value of `"airports_file"`. You will most like need to replace the `data/` portion with `~/weather_map/`

For example: `"airports_file": "data/kawo_to_kosh.json"` would become `"airports_file": "~/weather_map/kawo_to_kosh.json"`

Once you have performed this backup process and are sure that your files are in the new location, you may update the software.

### Updating The Code

**WARNING**: The following steps will discard any modifications you have performed.

```bash
cd ~/categorical-sectional
git fetch
git reset --hard HEAD
git checkout release
git pull
```

### Installing The Remote Code

If you have not installed MapConfig, Please follow the instructions in [MapConfig/readme.md](../MapConfig/readme.md)

If you have already install MapConfig, then the `fetch`/`pull` instructions will have updated your system to the latest version.
