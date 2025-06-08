# Clean Unwanted Files From Sabnzbd

This script recursively scans specified directories and deletes files matching a list of unwanted extensions. You can source unwanted extensions from a `sabnzbd.ini` configuration file or provide them directly as a comma-separated list. It supports dry-run mode and optional logging to a file. You can also call this script directly from your sabnzbd configuration.

## Use Cases

Use this script to clean up completed or incomplete download directories, especially if you're using SABnzbd and want to remove files like `.exe`, `.lnk`, `.bat`, `.tmp`, etc., based on your configured unwanted extensions.

## Requirements

- Python 3 (no external libraries required)

## Usage

You can run the script from the command line. Provide at least one directory to scan, and specify either a SABnzbd config file or a list of unwanted extensions. Optionally, enable dry-run mode to simulate deletions or log actions to a file.

```sh
python3 clean_unwanted_files.py [--finished <PATH>] [--incomplete <PATH>]
    [--sabnzbd-config <sabnzbd.ini> | --extensions "<ext1>,<ext2>,..."]
    [--dry-run] [--logfile <logfile>]
```

## Arguments

`--finished`: Path to the "finished" downloads directory.

`--incomplete`: Path to the "incomplete" downloads directory.

`--sabnzbd-config`: Path to the sabnzbd.ini file. The script will extract unwanted_extensions from the [misc] section.

`--extensions`: Comma-separated list of unwanted file patterns (e.g., "_.exe,_.bat,\*.tmp").

`--dry-run`: If specified, files will not actually be deleted; actions will be logged.

`--logfile`: Optional path to a file where logs should be written.

Note: Either `--sabnzbd-config` or `--extensions` must be specified.

## Example

Dry-run with custom extensions:

```sh
python3 clean_unwanted_files.py --finished /downloads/complete--extensions "*.exe,*.bat,*.tmp" --dry-run
```

Use SABnzbd config and log to file:

```sh
python3 clean_unwanted_files.py --finished /downloads/complete --incomplete /downloads/incomplete \
--sabnzbd-config /etc/sabnzbd/sabnzbd.ini --logfile /var/log/sabnzbd_remove_unwanted_files.log
```

## Behavior

Only files with matching patterns are deleted.

If `--dry-run` is used, no deletions occur — only log messages are printed.

If no directories are specified, the script exits with a warning.

If the SABnzbd config is malformed or `unwanted_extensions` is missing, the script aborts safely.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
