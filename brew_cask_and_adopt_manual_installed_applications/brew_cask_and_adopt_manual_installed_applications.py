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


def brew_search(app_name):
    result = subprocess.run(
        ["brew", "search", "--cask", app_name], capture_output=True, text=True
    )

    if "Error: No formulae or casks found for" in result.stdout:
        return False

    return result.stdout.splitlines()


def choose_alternative_cask(cask_names, original_name):
    """
    Prompt the user to choose an alternative cask from a list of cask names.

    Args:
        cask_names (list): The list of cask names from the brew search command.
        original_name (str): The original app name to search for.

    Returns:
        str or None: The chosen cask name, or None if no valid choice is made.
    """
    if cask_names:
        print(
            f"{colors.RED}Cask '{original_name}' not found. Here are some alternatives:{colors.ENDC}"
        )
        for i, alt in enumerate(cask_names, 1):
            print(f"{i}. {alt}")
        choice = input(
            f"Choose a cask by number (1-{len(cask_names)}), or press Enter to skip: "
        ).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(cask_names):
            selected_cask = cask_names[int(choice) - 1]
            print(f"You selected: {selected_cask}")
            return selected_cask
        else:
            print(f"{colors.RED}Invalid choice. Skipping...{colors.ENDC}")
            return None


def check_cask_available(app_name):
    """
    Check if a Homebrew Cask is available for the given application name.

    Args:
        app_name (str): Name of the application to check.

    Returns:
        bool: True if a Cask is available, False otherwise.
    """
    cask_findings = set()
    if " " in app_name:
        app_name_variations = [app_name.replace(" ", "-"), app_name.replace(" ", "")]
        for variation in app_name_variations:
            search_result = brew_search(variation)
            if search_result:
                cask_findings.update(search_result)
    else:
        search_result = brew_search(app_name)
        if search_result:
            cask_findings.update(search_result)

    cask_findings = sorted(list(cask_findings))

    print(cask_findings)

    if app_name in cask_findings:
        return app_name
    elif cask_findings:
        return choose_alternative_cask(cask_findings, app_name)
    else:
        return False


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


def prompt_yes_no(question):
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
        elif response in ["no", "n", ""]:
            return False
        else:
            print("Invalid response. Please answer 'yes' or 'no'.")


def main(install_dir, manually):
    """
    Main function to manage installed applications using Homebrew Cask.

    Args:
        install_dir (str): Directory where applications are installed.
        manually (bool): Whether to prompt for adoption confirmation.
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

        brew_cask_app_name = check_cask_available(app_name)

        # No valid alternative choosen or skipped
        if brew_cask_app_name is None:
            continue

        if brew_cask_app_name:
            if is_managed_by_brew(brew_cask_app_name):
                print(f"{app_name} is already installed and managed via Homebrew.")
                continue

            if manually and not prompt_yes_no(f"Do you want to adopt {app_name}?"):
                continue

            print(f"Trying to install {brew_cask_app_name} with Homebrew...")
            if install_adopt_app(brew_cask_app_name, install_dir):
                print(
                    f"{colors.GREEN}Installation of {app_name} succeeded!{colors.ENDC}"
                )
        else:
            print(f"{colors.RED}{app_name} is not available as a cask.{colors.ENDC}")
            non_brew_managed_apps.append(app_name)

    if non_brew_managed_apps:
        print(f"\n{colors.RED}Applications not found as Homebrew casks:{colors.ENDC}")
        for app in non_brew_managed_apps:
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
