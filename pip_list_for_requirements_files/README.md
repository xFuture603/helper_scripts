# Pip package checker

This script checks which packages listed in a requirements file are currently installed on your system.

## Description

The script reads a requirements file, compares its contents with the packages installed in your Python environment, and prints a list of packages that are installed (including installed versions). It helps ensure that all necessary dependencies are installed for your project or just filters out installed versions for larger projects for example.

## Use Cases

Helps to list the version of each installed package that you use in your requirements file.

## Requirements

- Python 3

## Usage

The script can be run from the command line. It requires specifying the path to the requirements file.

```sh
python3 pip_list_for_requirement_files.py <requirements_file>
```

## Example Output

```sh
Packages from requirements.txt that are installed:
package1==1.0.0
package2==2.1.0
package3 is installed but version 3.0.0 does not satisfy requirement package3>=3.0.1
package4 is not installed
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
