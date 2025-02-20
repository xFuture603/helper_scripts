# YAML Cleanup and Deduplication Script

This script processes multiple YAML files to extract common values into a separate file or remove values that overlap with reference files. It helps maintain cleaner, more structured YAML configurations, particularly in environments where multiple configuration files share redundant data.

## Description

The script takes multiple YAML files, identifies duplicate values across them, and either extracts common values into a separate file or removes values that overlap with a set of reference files. It preserves YAML structure, including block scalars (`|-`), and ensures proper formatting.

## Use Cases

- Consolidate redundant YAML configurations into a shared file.
- Remove overlapping values from stage-specific YAML files based on reference files.
- Maintain clean and DRY (Don't Repeat Yourself) YAML configurations.
- Avoid unnecessary duplication in configuration management workflows, such as Helm values files.

## Requirements

- Python 3
- `ruamel.yaml` (install using `pip install ruamel.yaml`)

## Usage

Run the script from the command line. You must specify the YAML files to process using `--files`. You can either extract common values using `--common` or remove values based on reference files using `--reference`. Backup and dry-run options are also available.

```sh
usage: yaml_deduplicate.py --files FILE [FILE ...] (--common FILE | --reference FILE [FILE ...]) [--dry-run] [--backup] [--no-log]

Extract common YAML values or remove overlapping values using reference files.

options:
  --files FILE [FILE ...]  List of YAML files to process (e.g., values-dev.yml values-test.yml values-prod.yml).
  --common FILE            Filename to store common values. Mutually exclusive with --reference.
  --reference FILE [FILE ...]  Reference file(s) whose keys will be removed from the specified files. Mutually exclusive with --common.
  --dry-run                Enable dry-run mode to show changes without modifying files.
  --backup                 Create a backup of the original files before making changes.
  --no-log                 Disable logging. Logging is enabled by default.
  -h, --help               Show this help message and exit.
```

## Example Scenarios

### Extracting Common Values

```sh
yaml_deduplicate.py --files values-dev.yml values-test.yml values-prod.yml --common common-values.yml
```
This will move values present in all three files to `common-values.yml` and remove them from the original files.

### Removing Overlapping Values Using Reference Files

```sh
yaml_deduplicate.py --files values-dev.yml values-test.yml values-prod.yml --reference reference.yml
```
This will remove any values in `reference.yml` from `values-dev.yml`, `values-test.yml`, and `values-prod.yml`.

### Using Multiple Reference Files

```sh
yaml_deduplicate.py --files values-dev.yml values-test.yml --reference ref1.yml ref2.yml
```
The script will first merge `ref1.yml` and `ref2.yml` and then remove overlapping values from `values-dev.yml` and `values-test.yml`.

### Dry-Run Mode

```sh
yaml_deduplicate.py --files values-dev.yml values-test.yml --common common-values.yml --dry-run
```
This will simulate the changes without modifying the files.

### Backup Original Files

```sh
yaml_deduplicate.py --files values-dev.yml values-test.yml --common common-values.yml --backup
```
This will create `.bak` backups of the original files before modifying them.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
