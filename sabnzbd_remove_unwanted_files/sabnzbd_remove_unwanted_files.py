#!/usr/bin/env python3
"""
Script to delete files with unwanted extensions from specified directories.

Usage:
    ./clean_unwanted_files.py [--finished <path_to_finished>] [--incomplete <path_to_incomplete>]
    [--sabnzbd-config <path_to_sabnzbd.ini> | --extensions <comma_separated_list>]
    [--dry-run] [--logfile <path_to_logfile>]

Examples:
    ./clean_unwanted_files.py \
        --finished /mnt/nas/finished_downloads \
        --incomplete /mnt/nas/incomplete_downloads \
        --sabnzbd-config /home/user/.sabnzbd/sabnzbd.ini

    ./clean_unwanted_files.py \
        --finished ./done \
        --extensions "*.exe,*.bat,*.tmp" \
        --dry-run \
        --logfile clean.log
"""

import argparse
import fnmatch
import logging
import os
import sys

# Optional: hardcoded arguments for SABnzbd integration
# Example: HARDCODED_ARGS = ["--finished", "/path", "--extensions", "*.exe,*.nfo"]
HARDCODED_ARGS = None


def setup_logging(logfile=None):
    """
    Configure logging to console and optionally to a file.

    Args:
        logfile: Path to log file, or None to disable file logging.
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    if logfile:
        try:
            file_handler = logging.FileHandler(logfile)
            handlers.append(file_handler)
        except OSError as e:
            logging.error("Failed to create log file %s: %s", logfile, e)
            sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )


def parse_sabnzbd_extensions(config_path):
    """
    Parse unwanted_extensions from sabnzbd.ini, supporting multi-line values.
    """
    found_misc = False
    collecting = False
    ext_lines = []

    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            if stripped.lower() == "[misc]":
                found_misc = True
                continue

            if not found_misc:
                continue

            if stripped.startswith("[") and stripped.endswith("]"):
                # Reached a new section — stop collecting
                break

            if stripped.startswith("unwanted_extensions"):
                # Start collecting multi-line value
                collecting = True
                _, first_part = stripped.split("=", 1)
                ext_lines.append(first_part.strip())
                continue

            if collecting:
                if "=" in stripped:  # reached another key
                    break
                ext_lines.append(stripped)

    if not ext_lines:
        logging.error("Could not find 'unwanted_extensions' in [misc] section.")
        return []

    full_ext_string = ",".join(ext_lines)
    return parse_extensions_string(full_ext_string)


def parse_extensions_string(ext_string):
    """
    Parse and clean extensions from a comma-separated string.

    Args:
        ext_string: String of comma-separated patterns.

    Returns:
        List of normalized extension patterns.
    """
    cleaned = ext_string.replace("\n", " ").replace("    ", " ")
    parts = [e.strip().lower() for e in cleaned.split(",") if e.strip()]
    return parts


def clean_directory(target_path, patterns, dry_run=False):
    """
    Recursively delete or log files matching given patterns.

    Args:
        target_path: Directory to scan.
        patterns: List of patterns to match.
        dry_run: If True, only log deletions.
    """
    deleted_files = []
    for root, _, files in os.walk(target_path):
        for file in files:
            file_lower = file.lower()
            full_path = os.path.join(root, file)
            for pattern in patterns:
                if fnmatch.fnmatch(file_lower, pattern):
                    if dry_run:
                        logging.info("[Dry Run] Would delete: %s", full_path)
                    else:
                        try:
                            os.remove(full_path)
                            logging.info("Deleted: %s", full_path)
                            deleted_files.append(full_path)
                        except OSError as e:
                            logging.error("Failed to delete %s: %s", full_path, e)
                    break
    return deleted_files


def main():
    """
    Parse command-line arguments, configure logging, and scan directories
    for files with unwanted extensions to delete (or simulate deletion).

    Supports reading unwanted file patterns from a sabnzbd.ini config
    or directly via a comma-separated list.

    Logs actions taken, and supports optional dry-run mode and logging to file.
    """
    parser = argparse.ArgumentParser(
        description="Delete files with unwanted extensions from directories."
    )
    parser.add_argument("--finished", help="Path to finished downloads folder")
    parser.add_argument("--incomplete", help="Path to incomplete downloads folder")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--sabnzbd-config", help="Path to sabnzbd.ini to load unwanted_extensions"
    )
    group.add_argument(
        "--extensions",
        help="Comma-separated list of unwanted extensions (e.g., '*.exe,*.tmp')",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Log deletions without deleting"
    )
    parser.add_argument("--logfile", help="Path to log file")

    if len(sys.argv) == 1 and HARDCODED_ARGS:
        args = parser.parse_args(HARDCODED_ARGS)
    else:
        args = parser.parse_args()
    setup_logging(args.logfile)

    if not args.finished and not args.incomplete:
        logging.warning(
            "Neither --finished nor --incomplete was provided. Nothing to scan."
        )
        sys.exit(0)

    if args.sabnzbd_config:
        patterns = parse_sabnzbd_extensions(args.sabnzbd_config)
        logging.info("Loaded %d unwanted extension patterns.", len(patterns))
        logging.debug("Unwanted extensions: %s", ", ".join(patterns))
    else:
        patterns = parse_extensions_string(args.extensions)

    if not patterns:
        logging.error("No unwanted extension patterns were loaded. Exiting.")
        sys.exit(1)

    if args.finished:
        logging.info("Scanning '%s' for unwanted files...", args.finished)
        clean_directory(args.finished, patterns, dry_run=args.dry_run)

    if args.incomplete:
        logging.info("Scanning '%s' for unwanted files...", args.incomplete)
        clean_directory(args.incomplete, patterns, dry_run=args.dry_run)

    logging.info("Scan complete.")


if __name__ == "__main__":
    main()
