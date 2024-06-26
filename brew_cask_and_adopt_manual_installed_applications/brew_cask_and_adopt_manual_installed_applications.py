#!/usr/bin/env python3

"""
A script to collect all manually installed applications on your Mac
and try to adopt them to a brew cask:
https://docs.brew.sh/Tips-N'-Tricks#appoint-homebrew-cask-to-manage-a-manually-installed-app
"""

import os
import subprocess
import argparse


# ANSI color codes for terminal output
class Colors:
    """
    Declare color variables
    """

    RED = "\033[91m"
    GREEN = "\033[92m"
    ENDC = "\033[0m"


def print_colored(message, color):
    """
    Print a message with the specified ANSI color.

    Args:
        message (str): The message to print.
        color (str): The ANSI color code.
    """
    print(f"{color}{message}{Colors.ENDC}")


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
    """
    Search for an application available as a Homebrew cask.

    Args:
        app_name (str): Name of the application to check.

    Returns:
        list: List of available cask applications found for the given application name.
    """
    applications = []

    try:
        result = subprocess.run(
            ["brew", "search", "--cask", app_name],
            capture_output=True,
            text=True,
            check=True,
        )

        if "Error: No formulae or casks found for" not in result.stdout:
            applications.extend(result.stdout.splitlines())
    except subprocess.CalledProcessError as e:
        print_colored(
            f'Brew search failed for "{app_name}":\n{e.stderr.strip()}', Colors.RED
        )

    return applications


def choose_alternative_cask(cask_names, original_name):
    """
    Prompt the user to choose an alternative cask from a list of cask names.

    Args:
        cask_names (list): List of cask names from the brew search command.
        original_name (str): The original app name to search for.

    Returns:
        str or None: The chosen cask name, or None if no valid choice is made.
    """
    print_colored(
        f'Cask "{original_name}" not found. Here are some alternatives:', Colors.RED
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
        print_colored("Invalid choice. Skipping...", Colors.RED)
        return None


def check_cask_available(app_name):
    """
    Check if a Homebrew Cask is available for the given application name.

    Args:
        app_name (str): Name of the application to check.

    Returns:
        str: The valid Homebrew Cask application name.
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

    if app_name in cask_findings:
        return app_name
    elif cask_findings:
        return choose_alternative_cask(cask_findings, app_name)
    else:
        return None


def brew_install(app_name, install_dir, mode="adopt", retry_count=0):
    """
    Install or adopt an application using Homebrew Cask.

    Args:
        app_name (str): Name of the application to install or adopt.
        install_dir (str): Directory where the application should be installed.
        mode (str): Installation mode, either "adopt" or "force".
        retry_count (int): Current retry attempt count to avoid infinity loop.

    Returns:
        bool: True if installation or adoption was successful, False otherwise.
    """
    install_command = [
        "brew",
        "install",
        "--cask",
        app_name,
        f"--{mode}",
        "--appdir",
        install_dir,
    ]

    try:
        subprocess.run(
            install_command,
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        if "It seems the existing App is different" in e.stderr and retry_count < 1:
            if prompt_yes_no(
                "It seems the existing App is different from the one being installed.\nDo you want to force install?"
            ):
                return brew_install(
                    app_name, install_dir, mode="force", retry_count=retry_count + 1
                )

        print_colored(
            f'Installation failed for "{app_name}":\n{e.stderr.strip()}',
            Colors.RED,
        )
        return False


def is_managed_by_brew(app_name):
    """
    Check if an application is managed by Homebrew Cask.

    Args:
        app_name (str): Name of the application to check.

    Returns:
        bool: True if the application is managed by Homebrew.
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
        bool: True if the application is a default Apple app.
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
    Ask the user a yes/no question and return the response as a boolean value.

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
    installed_apps = list_installed_apps(install_dir)
    non_brew_managed_apps = []

    for app in installed_apps:
        # Split path and extract app name only
        app_name = os.path.splitext(app)[0].lower()

        print("")

        # Skip if application is an Apple app
        if is_default_apple_app(app_name):
            print(f'Skipping default Apple app "{app_name}"')
            continue

        print(f'Checking for "{app_name}"...')

        # Check for valid cask name or suggest alternative name
        brew_cask_app_name = check_cask_available(app_name)

        # No valid alternative chosen or skipped
        if brew_cask_app_name is None:
            print_colored(f'"{app_name}" is not available as a cask.', Colors.RED)
            non_brew_managed_apps.append(app_name)
            continue

        # Application already managed by Homebrew
        if is_managed_by_brew(brew_cask_app_name):
            print(
                f'"{brew_cask_app_name}" is already installed and managed via Homebrew.'
            )
            continue

        # For manually mode prompt to ask for adoption
        if manually and not prompt_yes_no(
            f'Do you want to adopt "{brew_cask_app_name}"?'
        ):
            continue

        # Try to install application with Homebrew
        print(f'Trying to install "{brew_cask_app_name}" with Homebrew...')
        if brew_install(brew_cask_app_name, install_dir):
            print_colored(
                f'Installation of "{brew_cask_app_name}" succeeded!', Colors.GREEN
            )

    if non_brew_managed_apps:
        print_colored("\nApplications not found as Homebrew casks:\n", Colors.RED)
        for app in non_brew_managed_apps:
            print(app)
        print(
            "\nFor more available Homebrew Casks, visit https://formulae.brew.sh/cask/"
        )


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
