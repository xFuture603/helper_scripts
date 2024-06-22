# Manage Installed Applications with Homebrew Cask

This script manages installed applications on your macOS system using Homebrew. It checks which applications are already managed by Homebrew, installs or adopts applications if they are available as Homebrew Casks, and lists applications that are not found as Homebrew Casks.

[More information about `brew --cask --adopt`](https://docs.brew.sh/Tips-N'-Tricks#appoint-homebrew-cask-to-manage-a-manually-installed-app)

## Description

The script scans the `/Applications` directory (or a specified directory) for installed applications. It interacts with Homebrew to check if each application is already managed, attempts to normalize application names for Homebrew Cask compatibility, and provides status updates during the process.

**Note:** Homebrew will install the latest version of each application!

## Use Cases

- Ensures that all applications on your system are managed consistently via Homebrew Cask.
- Automates the installation or adoption of applications available as Homebrew Casks.
- Identifies applications that are not available as Homebrew Casks for manual handling.

## Requirements

- Python 3
- Homebrew (for managing applications with Homebrew Cask)

## Usage

The script can be run from the command line. By default, it checks applications in `/Applications`. Optionally, you can specify a different directory.

```sh
python3 brew_cask_and_adopt_manual_installed_applications.py <install_directory>
```

## Example Output

```sh
Checking for tor browser...
tor browser is already installed and managed via Homebrew.

Checking for visual studio code...
visual studio code is already installed and managed via Homebrew.

Checking for raycast...
raycast is already installed and managed via Homebrew.

Checking for rectangle...
rectangle is already installed and managed via Homebrew.

Applications not found as Homebrew casks:

wireguard
alttab
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
