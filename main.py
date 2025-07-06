# repro_build_cli.py

import argparse
import os
import colorama
import json
import re

# Initialize Colorama for cross-platform ANSI support
colorama.init()


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def list_subdirectories(path):
    """
    Lists all subdirectories in the given path.
    Returns a list of absolute paths to the subdirectories.
    """
    subdirs = []
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                # Exclude common hidden directories or system directories
                if not item.startswith(".") and item not in [
                    "node_modules",
                    "venv",
                    "__pycache__",
                    ".git",
                ]:
                    subdirs.append(item_path)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: Directory not found at {path}{Colors.RESET}")
    except PermissionError:
        print(f"{Colors.RED}Error: Permission denied to access {path}{Colors.RESET}")
    except Exception as e:
        print(
            f"{Colors.RED}An unexpected error occurred while listing directories: {e}{Colors.RESET}"
        )
    return sorted(subdirs)  # Return sorted list for consistent display


# Removed: get_node_version_from_package_json function
# This functionality is being removed as per user request.


def find_yaml_files(project_path):
    """
    Scans the project directory for common YAML configuration files.
    Returns a list of paths to detected YAML files.
    """
    yaml_files = []
    common_yaml_names = ["docker-compose.yml", "docker-compose.yaml", ".gitlab-ci.yml"]
    github_workflows_dir = os.path.join(project_path, ".github", "workflows")

    # Check for common YAML files in the root
    for name in common_yaml_names:
        file_path = os.path.join(project_path, name)
        if os.path.exists(file_path):
            yaml_files.append(file_path)

    # Check for YAML files in .github/workflows
    if os.path.isdir(github_workflows_dir):
        try:
            for root, _, files in os.walk(github_workflows_dir):
                for file in files:
                    if file.endswith((".yml", ".yaml")):
                        yaml_files.append(os.path.join(root, file))
        except Exception as e:
            print(
                f"{Colors.YELLOW}Warning: Could not scan .github/workflows directory: {e}{Colors.RESET}"
            )

    return sorted(yaml_files)


def find_project_info(project_path):
    """
    Finds project-related files like package.json and extracts necessary info.
    Checks for package.json existence and detects YAML files.
    Node.js version detection from package.json is removed in this version.
    """
    package_json_path = os.path.join(project_path, "package.json")

    if not os.path.exists(package_json_path):
        print(
            f"{Colors.RED}Error: No package.json found in '{project_path}'. "
            "This directory does not appear to be an NPM project.{Colors.RESET}"
        )
        return None

    # Node.js version is no longer automatically detected from package.json
    # It will be provided by other means (e.g., user input or YAML parsing)
    node_version = None  # Explicitly set to None for now

    yaml_files = find_yaml_files(project_path)

    print(
        f"{Colors.GREEN}Found package.json in:{Colors.RESET} {Colors.BOLD}{project_path}{Colors.RESET}"
    )
    project_info = {
        "node_version": node_version,  # This will be None for now
        "project_path": project_path,
        "package_manager": "npm",  # Defaulting to npm for now, will refine later
        "yaml_files": yaml_files,
    }
    if yaml_files:
        print(f"{Colors.GREEN}Detected YAML configuration files:{Colors.RESET}")
        for yf in yaml_files:
            print(f"  - {os.path.relpath(yf, project_path)}")
    else:
        print(
            f"{Colors.YELLOW}No common YAML configuration files detected.{Colors.RESET}"
        )
    return project_info


def get_project_directory_interactive():
    """
    Prompts the user to enter the project directory path,
    offering a list of subdirectories to choose from.
    """
    current_path = os.getcwd()
    while True:
        print(f"\n{Colors.BOLD}Current directory:{Colors.RESET} {current_path}")
        subdirs = list_subdirectories(current_path)

        if subdirs:
            print(
                f"\n{Colors.BLUE}Detected subdirectories (select by number or enter path):{Colors.RESET}"
            )
            for i, subdir in enumerate(subdirs):
                if os.path.exists(os.path.join(subdir, "package.json")):
                    print(
                        f"  {Colors.GREEN}[{i+1}]{Colors.RESET} {os.path.basename(subdir)} {Colors.CYAN}(NPM Project){Colors.RESET}"
                    )
                else:
                    print(
                        f"  {Colors.YELLOW}[{i+1}]{Colors.RESET} {os.path.basename(subdir)}"
                    )
            print(
                f"  {Colors.YELLOW}[.]{Colors.RESET} Stay in current directory (select if this is your project)"
            )
            print(f"  {Colors.YELLOW}[..]{Colors.RESET} Go up one level")
            print(f"  {Colors.YELLOW}[q]{Colors.RESET} Quit")
        else:
            print(
                f"{Colors.YELLOW}No subdirectories found in '{current_path}'.{Colors.RESET}"
            )
            print(
                f"  {Colors.YELLOW}[.]{Colors.RESET} Stay in current directory (select if this is your project)"
            )
            print(f"  {Colors.YELLOW}[..]{Colors.RESET} Go up one level")
            print(f"  {Colors.YELLOW}[q]{Colors.RESET} Quit")

        choice = input(
            f"{Colors.CYAN}Enter a number, a path, '.', '..', or 'q' to quit: {Colors.RESET}"
        ).strip()

        if choice.lower() == "q":
            return None

        if choice == ".":
            project_abs_path = os.path.abspath(current_path)
            if os.path.isdir(project_abs_path):
                if os.path.exists(os.path.join(project_abs_path, "package.json")):
                    print(
                        f"{Colors.GREEN}Selected project:{Colors.RESET} {os.path.basename(project_abs_path)}"
                    )
                    return project_abs_path
                else:
                    print(
                        f"{Colors.RED}Error: Current directory '{os.path.basename(project_abs_path)}' is not an NPM project (no package.json found). Please select a valid project or navigate.{Colors.RESET}"
                    )
                    continue
            else:
                print(
                    f"{Colors.RED}Error: Current path '{project_abs_path}' is not a valid directory.{Colors.RESET}"
                )
                continue
        elif choice == "..":
            parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
            if os.path.isdir(parent_path):
                current_path = parent_path
            else:
                print(
                    f"{Colors.RED}Error: Cannot go up from '{current_path}'. Already at root or invalid path.{Colors.RESET}"
                )
            continue
        elif choice.isdigit():
            try:
                index = int(choice) - 1
                if 0 <= index < len(subdirs):
                    selected_path = subdirs[index]
                    if os.path.exists(os.path.join(selected_path, "package.json")):
                        print(
                            f"{Colors.GREEN}Selected project:{Colors.RESET} {os.path.basename(selected_path)}"
                        )
                        return selected_path
                    else:
                        print(
                            f"{Colors.YELLOW}Selected directory '{os.path.basename(selected_path)}' is not an NPM project. Navigating into it.{Colors.RESET}"
                        )
                        current_path = selected_path
                        continue
                else:
                    print(
                        f"{Colors.RED}Invalid number. Please try again.{Colors.RESET}"
                    )
            except ValueError:
                print(
                    f"{Colors.RED}Invalid input. Please enter a number, a path, '.', '..', or 'q'.{Colors.RESET}"
                )
        else:
            input_path = choice.strip('"').strip("'")

            if os.path.isabs(input_path):
                project_abs_path = os.path.abspath(input_path)
            else:
                project_abs_path = os.path.abspath(
                    os.path.join(current_path, input_path)
                )

            if not os.path.isdir(project_abs_path):
                print(
                    f"{Colors.RED}Error: The provided path '{project_abs_path}' is not a valid directory. Please try again.{Colors.RESET}"
                )
            else:
                if os.path.exists(os.path.join(project_abs_path, "package.json")):
                    print(
                        f"{Colors.GREEN}Selected project:{Colors.RESET} {os.path.basename(project_abs_path)}"
                    )
                    return project_abs_path
                else:
                    print(
                        f"{Colors.YELLOW}Entered directory '{os.path.basename(project_abs_path)}' is not an NPM project. Navigating into it.{Colors.RESET}"
                    )
                    current_path = project_abs_path
                    continue


def main():
    """
    Main function to parse command-line arguments and start the process.
    """
    parser = argparse.ArgumentParser(
        description=f"{Colors.BOLD}CLI for building reproducible NPM project environments with Docker.{Colors.RESET}"
    )
    parser.add_argument(
        "project_dir",
        type=str,
        nargs="?",
        help="Path to the root directory of the NPM project.",
    )

    args = parser.parse_args()

    project_abs_path = None

    if args.project_dir:
        project_abs_path = os.path.abspath(args.project_dir)
        if not os.path.isdir(project_abs_path):
            print(
                f"{Colors.RED}Error: The provided path '{project_abs_path}' is not a valid directory.{Colors.RESET}"
            )
            return
    else:
        project_abs_path = get_project_directory_interactive()
        if not project_abs_path:
            print(f"{Colors.YELLOW}Operation cancelled by user. Exiting.{Colors.RESET}")
            return

    print(
        f"{Colors.GREEN}CLI initialized. Analyzing project directory:{Colors.RESET} {Colors.BOLD}{project_abs_path}{Colors.RESET}"
    )

    project_info = find_project_info(project_abs_path)

    if project_info:
        print("\n--- Project Information ---")
        for key, value in project_info.items():
            print(f"{key}: {value}")
        print("---------------------------\n")
        print(
            f"{Colors.BLUE}Next: Add argument for commit hash and integrate Docker build/run.{Colors.RESET}"
        )
    else:
        print(
            f"{Colors.RED}Failed to gather necessary project information. Exiting.{Colors.RESET}"
        )


if __name__ == "__main__":
    main()
