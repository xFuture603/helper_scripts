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
        handlers=handlers
    )


def parse_sabnzbd_extensions(config_path):
    """
    Manually parse unwanted_extensions from sabnzbd.ini
    while ignoring lines before the first section header.

    Args:
        config_path: Path to sabnzbd.ini file.

    Returns:
        List of extension patterns.
    """
    found_misc = False
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.lower() == "[misc]":
                found_misc = True
            elif found_misc and line.startswith("unwanted_extensions"):
                try:
                    _, ext_string = line.split("=", 1)
                    return parse_extensions_string(ext_string.strip())
                except ValueError:
                    logging.error("Malformed unwanted_extensions line: %s", line)
                    return []
    logging.error("Could not find [misc] section or unwanted_extensions in %s", config_path)
    return []


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
    group.add_argument("--sabnzbd-config", help="Path to sabnzbd.ini to load unwanted_extensions")
    group.add_argument(
        "--extensions", help="Comma-separated list of unwanted extensions (e.g., '*.exe,*.tmp')"
    )
    parser.add_argument("--dry-run", action="store_true", help="Log deletions without deleting")
    parser.add_argument("--logfile", help="Path to log file")

    args = parser.parse_args()
    setup_logging(args.logfile)

    if not args.finished and not args.incomplete:
        logging.warning("Neither --finished nor --incomplete was provided. Nothing to scan.")
        sys.exit(0)

    if args.sabnzbd_config:
        patterns = parse_sabnzbd_extensions(args.sabnzbd_config)
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
