#!/usr/bin/python3

"""
A script to gather all installed python packages via `pip list`
but only for specific requirement files
"""

import sys
import pkg_resources
from packaging.requirements import Requirement

def read_requirements(file_path):
    """
    Reads the requirements file and returns a list of Requirement objects.

    Args:
        file_path (str): The path to the requirements file.

    Returns:
        list: A list of Requirement objects.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        requirements = file.read().splitlines()
    return [Requirement(req) for req in requirements]

def get_installed_packages():
    """
    Returns a dictionary of installed packages with their versions.

    Returns:
        dict: A dictionary where keys are package names and values are versions.
    """
    installed_packages = pkg_resources.working_set
    if not isinstance(installed_packages, list):
        installed_packages = list(installed_packages)
    return {pkg.key: pkg.version for pkg in installed_packages}

def main(req_file):
    """
    Checks which packages listed in the requirements file are installed and prints them.

    Args:
        req_file (str): The path to the requirements file.
    """
    requirements = read_requirements(req_file)
    installed_packages = get_installed_packages()

    print(f"Packages from {req_file} that are installed:")
    for req in requirements:
        package_name = req.name.lower()
        if package_name in installed_packages:
            installed_version = installed_packages[package_name]
            if req.specifier.contains(installed_version):
                print(f"{package_name}=={installed_version}")
            else:
                print(f"{package_name} is installed but version {installed_version} "
                      f"does not satisfy requirement {req}")
        else:
            print(f"{package_name} is not installed")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 check_requirements.py <requirements_file>")
        sys.exit(1)

    requirements_file = sys.argv[1]
    main(requirements_file)
