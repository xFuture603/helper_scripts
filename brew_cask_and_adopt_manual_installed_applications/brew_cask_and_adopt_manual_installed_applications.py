#!/usr/bin/python3

"""
A script to collect all manual installed applications on your Mac
and try to adopt them to a brew cask:
https://docs.brew.sh/Tips-N'-Tricks#appoint-homebrew-cask-to-manage-a-manually-installed-app
"""

import os
import subprocess
import sys


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
    apps = [f for f in os.listdir(applications_path) if f.endswith(".app")]
    return apps


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


def install_or_adopt_app(app_name, install_dir):
    """
    Install or adopt an application using Homebrew Cask.

    Args:
        app_name (str): Name of the application to install or adopt.
        install_dir (str): Directory where the application should be installed.

    Returns:
        bool: True if installation or adoption was successful, False otherwise.
    """
    try:
        result = subprocess.run(
            ["brew", "install", "--cask", "--adopt", app_name, "--appdir", install_dir],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                result.args,
                output=result.stdout,
                stderr=result.stderr,
            )
        return True
    except subprocess.CalledProcessError as e:
        # Check if the error is due to existing app conflict
        if "Error: It seems there is already an App at" in e.stderr:
            print(
                f"Skipping {app_name} installation. There is already an "
                f"application at {install_dir}/{app_name}.app."
            )
        else:
            print(f"Adopt/install failed for {app_name}: {e}")
        return False


def is_managed_by_brew(app_name):
    """
    Check if an application is already managed by Homebrew Cask.

    Args:
        app_name (str): Name of the application to check.

    Returns:
        bool: True if the application is managed by Homebrew, False otherwise.
    """
    result = subprocess.run(
        ["brew", "list", "--cask", "--versions", app_name],
        capture_output=True,
        text=True,
        check=False,
    )
    return app_name in result.stdout.split()


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
    return app_name in default_apps


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


def main(install_dir):
    """
    Main function to manage installed applications using Homebrew Cask.

    Args:
        install_dir (str): Directory where applications are installed.

    """
    apps = list_installed_apps(install_dir)
    not_found_apps = []

    for app in apps:
        app_name = app.replace(".app", "").lower()

        if is_default_apple_app(app_name):
            print(f"Skipping default Apple app: {app_name}")
            print()
            continue

        print(f"Checking for {app_name}...")

        # Check if managed by Homebrew (exact name and variations)
        if is_managed_by_brew(app_name) or is_managed_by_brew(
            app_name.replace(" ", "-")
        ):
            print(f"{app_name} is already installed and managed via Homebrew.")
            print()
            continue

        # Normalize app name for Homebrew
        normalized_name = normalize_app_name(app_name)
        if normalized_name:
            print(
                f"{colors.GREEN}Installing {normalized_name} with Homebrew...{colors.ENDC}"
            )
            install_or_adopt_app(normalized_name, install_dir)
        else:
            print(f"{app_name} is not available as a cask.")
            not_found_apps.append(app_name)

        print()

    if not_found_apps:
        print(f"\n{colors.RED}Applications not found as Homebrew casks:{colors.ENDC}\n")
        for app in not_found_apps:
            print(app)
        print(
            "\nFor more available Homebrew Casks, visit https://formulae.brew.sh/cask/"
        )


if __name__ == "__main__":
    INSTALL_DIR = "/Applications"
    if len(sys.argv) > 1:
        INSTALL_DIR = sys.argv[1]
    main(INSTALL_DIR)
