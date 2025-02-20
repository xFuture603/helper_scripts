#!/usr/bin/env python3
import argparse
import shutil
import logging
from ruamel.yaml import YAML
import sys


class YAMLProcessor:
    def __init__(
        self,
        file_list,
        common_file=None,
        dry_run=False,
        backup=False,
        reference_files=None,
        logger=None,
    ):
        self.file_list = file_list
        self.common_file = common_file
        self.dry_run = dry_run
        self.backup = backup
        self.reference_files = reference_files
        self.logger = logger or logging.getLogger(__name__)
        self.yaml_instance = YAML()
        self.yaml_instance.preserve_quotes = True
        self.yaml_instance.indent(mapping=2, sequence=4, offset=2)
        self.data_by_file = {}

    def load_yaml(self, file_path):
        try:
            with open(file_path, "r") as f:
                data = self.yaml_instance.load(f)
                return data if data is not None else {}
        except Exception as e:
            self.logger.error(f"Error loading YAML file {file_path}: {e}")
            raise

    def save_yaml(self, data, file_path):
        try:
            if self.dry_run:
                self.logger.info(f"Dry-run: Changes to {file_path} would be written.")
                return
            with open(file_path, "w") as f:
                self.yaml_instance.dump(data, f)
            self.logger.info(f"File saved: {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving YAML file {file_path}: {e}")
            raise

    def backup_file(self, file_path):
        try:
            backup_path = file_path + ".bak"
            if self.dry_run:
                self.logger.info(
                    f"Dry-run: Backup from {file_path} to {backup_path} would be created."
                )
                return
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Backup created: {backup_path}")
        except Exception as e:
            self.logger.error(f"Error creating backup for {file_path}: {e}")
            raise

    def intersect_dicts(self, dicts):
        if not dicts:
            return {}
        common = {}
        first = dicts[0]
        for key, value in first.items():
            if all(key in d for d in dicts):
                values = [d[key] for d in dicts]
                if all(isinstance(v, dict) for v in values):
                    nested = self.intersect_dicts(values)
                    if nested:
                        common[key] = nested
                elif all(isinstance(v, list) for v in values) and all(
                    v == value for v in values
                ):
                    common[key] = value
                elif all(v == value for v in values):
                    common[key] = value
        return common

    def remove_common(self, original, common):
        for key in list(common.keys()):
            if key in original:
                if isinstance(common[key], dict) and isinstance(original[key], dict):
                    self.remove_common(original[key], common[key])
                    if not original[key]:
                        del original[key]
                else:
                    del original[key]

    def clean_empty(self, data):
        if isinstance(data, dict):
            keys_to_delete = [
                key
                for key, value in data.items()
                if isinstance(value, dict) and not value or value in [None, ""]
            ]
            for key in keys_to_delete:
                del data[key]

    def merge_references(self, ref_list):
        merged = {}
        for ref in ref_list:
            merged = self._merge_two(merged, ref)
        return merged

    def _merge_two(self, d1, d2):
        result = dict(d1)
        for key, value in d2.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_two(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

    def process_files(self):
        for file in self.file_list:
            try:
                self.logger.info(f"Loading file: {file}")
                self.data_by_file[file] = self.load_yaml(file)
            except Exception as e:
                self.logger.error(f"Skipping file {file} due to an error: {e}")

        if not self.data_by_file:
            self.logger.error("No files were successfully loaded. Exiting.")
            sys.exit(1)

        if self.reference_files:
            ref_data_list = []
            for ref_file in self.reference_files:
                try:
                    self.logger.info(f"Loading reference file: {ref_file}")
                    ref_data = self.load_yaml(ref_file)
                    ref_data_list.append(ref_data)
                except Exception as e:
                    self.logger.error(f"Error loading reference file {ref_file}: {e}")
                    sys.exit(1)
            merged_reference = self.merge_references(ref_data_list)
            self.logger.info("Merged reference definitions created.")
            for file, data in self.data_by_file.items():
                if self.backup:
                    self.backup_file(file)
                self.remove_common(data, merged_reference)
                self.clean_empty(data)
                self.save_yaml(data, file)
            self.logger.info(
                "Removal of keys based on merged reference files completed."
            )
        else:
            common = self.intersect_dicts(list(self.data_by_file.values()))
            self.logger.info("Common definitions determined.")
            for file, data in self.data_by_file.items():
                if self.backup:
                    self.backup_file(file)
                self.remove_common(data, common)
                self.clean_empty(data)
                self.save_yaml(data, file)
            self.save_yaml(common, self.common_file)
            self.logger.info("Processing and extraction of common values completed.")


def setup_logging():
    logger = logging.getLogger("YAMLProcessor")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Extract common YAML values or remove overlapping values using reference files."
    )

    parser.add_argument(
        "--files",
        metavar="FILE",
        nargs="+",
        required=True,
        help="List of YAML files to process (e.g., values-dev.yml values-test.yml values-prod.yml).",
    )
    parser.add_argument(
        "--common",
        metavar="FILE",
        help="Filename to store common values. Mutually exclusive with --reference.",
    )
    parser.add_argument(
        "--reference",
        metavar="FILE",
        nargs="+",
        help="Reference file(s) whose keys will be removed from the specified files. Mutually exclusive with --common.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enable dry-run mode to show changes without modifying files.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a backup of the original files before making changes.",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Disable logging. Logging is enabled by default.",
    )

    args = parser.parse_args()

    if args.common and args.reference:
        parser.error(
            "The --common and --reference options are mutually exclusive. Use only one."
        )

    return args


def main():
    args = parse_arguments()
    if args.no_log:
        logger = logging.getLogger("YAMLProcessor")
        logger.disabled = True
    else:
        logger = setup_logging()

    processor = YAMLProcessor(
        file_list=args.files,
        common_file=args.common,
        dry_run=args.dry_run,
        backup=args.backup,
        reference_files=args.reference,
        logger=logger,
    )
    try:
        processor.process_files()
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
