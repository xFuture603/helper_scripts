#!/usr/bin/env python3

"""
A script to collect all manual installed applications on your Mac
and try to adopt them to a brew cask:
https://docs.brew.sh/Tips-N'-Tricks#appoint-homebrew-cask-to-manage-a-manually-installed-app
"""

import os
import subprocess
import argparse


# ANSI color codes for terminal output
class colors:
    """
    Declare color variables
    """

    RED = "\033[91m"
    GREEN = "\033[92m"
    ENDC = "\033[0m"


def list_installed_apps(applications_path):
    """
    List all installed applications in the specified directory.

    Args:
        applications_path (str): Path to the directory containing installed applications.

    Returns:
        list: List of installed application filenames ending with '.app'.
    """
    return [f for f in os.listdir(applications_path) if f.endswith(".app")]


def check_cask_available(app_name):
    """
    Check if a Homebrew Cask is available for the given application name.

    Args:
        app_name (str): Name of the application to check.

    Returns:
        bool: True if a Cask is available, False otherwise.
    """
    result = subprocess.run(
        ["brew", "search", app_name], capture_output=True, text=True, check=False
    )
    return app_name in result.stdout.split()


def install_adopt_app(app_name, install_dir):
    """
    Install or adopt an application using Homebrew Cask.

    Args:
        app_name (str): Name of the application to install or adopt.
        install_dir (str): Directory where the application should be installed.

    Returns:
        bool: True if installation or adoption was successful, False otherwise.
    """
    try:
        subprocess.run(
            ["brew", "install", "--cask", "--adopt", app_name, "--appdir", install_dir],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Adopt installation failed for {app_name}:")
        print(f"{colors.RED}{e.stderr.strip()}{colors.ENDC}")
        return False


def is_managed_by_brew(app_name):
    """
    Check if an application is managed by Homebrew Cask.

    Args:
        app_name (str): Name of the application to check.

    Returns:
        bool: True if the application is managed by Homebrew, False otherwise.
    """
    result = subprocess.run(
        ["brew", "list", "--cask", "--versions", app_name],
        capture_output=True,
        text=True,
    )
    return app_name in result.stdout


def is_default_apple_app(app_name):
    """
    Check if an application is a default Apple app that should be skipped.

    Args:
        app_name (str): Name of the application to check.

    Returns:
        bool: True if the application is a default Apple app, False otherwise.
    """
    default_apps = [
        "garageband",
        "keynote",
        "safari",
        "numbers",
        "imovie",
        "pages",
    ]  # Add more apps as needed
    return app_name.lower() in default_apps


def prompt(question):
    """
    Asks the user a yes/no question and returns the response as a boolean value.

    Args:
        question (str): The question to ask the user.

    Returns:
        bool: True if the user answers 'yes', False if the user answers 'no'.
    """
    while True:
        response = input(f"{question} (y/N): ").strip().lower()
        if response in ["yes", "y"]:
            return True
        elif response in ["no", "n"] or not response:
            return False
        else:
            print("Invalid response. Please answer 'yes' or 'no'.")


def normalize_app_name(app_name):
    """
    Normalize the application name for Homebrew Cask by attempting different formats.

    Args:
        app_name (str): Name of the application to normalize.

    Returns:
        str or None: Normalized application name if available as a Homebrew Cask, None otherwise.
    """
    # Attempt with dashes between words
    dashed_name = app_name.replace(" ", "-")
    if check_cask_available(dashed_name):
        return dashed_name

    # Attempt with no spaces
    no_space_name = app_name.replace(" ", "")
    if check_cask_available(no_space_name):
        return no_space_name

    return None


def main(install_dir, manually):
    """
    Main function to manage installed applications using Homebrew Cask.

    Args:
        install_dir (str): Directory where applications are installed.

    """
    print("Checking for installed applications...")
    apps = list_installed_apps(install_dir)
    not_found_apps = []

    terminal_width = os.get_terminal_size()
    delimiter = "\n" + ("=" * terminal_width.columns) + "\n"

    for app in apps:
        app_name = app.replace(".app", "").lower()
        print(delimiter)

        if is_default_apple_app(app_name):
            print(f"Skipping default Apple app: {app_name}")
            continue

        print(f"Checking for {app_name}...")

        # Normalize app name for Homebrew
        normalized_name = normalize_app_name(app_name)

        # Check if managed by Homebrew (exact name and variations)
        if is_managed_by_brew(app_name) or (
            normalized_name is not None and is_managed_by_brew(normalized_name)
        ):
            print(f"{app_name} is already installed and managed via Homebrew.")
            continue

        if manually and not prompt(f"Do you want to adopt {app_name}?"):
            continue

        if normalized_name:
            print(f"Try to installing {normalized_name} with Homebrew...")
            if install_adopt_app(normalized_name, install_dir):
                print(
                    f"{colors.GREEN}Installation of {app_name} succeeded!{colors.ENDC}"
                )
        else:
            print(f"{colors.RED}{app_name} is not available as a cask.{colors.ENDC}")
            not_found_apps.append(app_name)

    if not_found_apps:
        print(f"{colors.RED}Applications not found as Homebrew casks:{colors.ENDC}")
        for app in not_found_apps:
            print(app)
        print("For more available Homebrew Casks, visit https://formulae.brew.sh/cask/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Adopt manually installed applications to Homebrew Cask."
    )
    parser.add_argument(
        "-i",
        "--install-dir",
        type=str,
        default="/Applications",
        help="Directory where applications are installed (default: /Applications)",
    )
    parser.add_argument(
        "-m",
        "--manually",
        action="store_true",
        help="Prompt for adoption confirmation (default: False)",
    )
    args = parser.parse_args()

    main(args.install_dir, args.manually)
