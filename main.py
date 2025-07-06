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


def get_node_version_from_package_json(package_json_path):
    """
    Reads the package.json file and attempts to extract the Node.js version.
    It looks for the 'engines.node' field. If not found, it suggests a default.
    """
    try:
        with open(package_json_path, "r", encoding="utf-8") as f:
            package_data = json.load(f)

        node_version = package_data.get("engines", {}).get("node")

        if node_version:
            # Clean up the version string, e.g., remove '^', '~', '>', etc.
            # We'll aim for a specific major/minor version for Docker.
            # This regex captures digits, dots, and 'x' (for 16.x.x)
            match = re.match(r"(\d+\.\d+(\.\d+|x)?).*", node_version)
            if match:
                clean_version = match.group(1)
                # Replace 'x' with '0' for a more concrete version if needed, or just use as is.
                # For Docker, '16' or '16.x' is often sufficient to pick the latest patch.
                if clean_version.endswith(".x"):
                    return clean_version.replace(".x", "")  # e.g., '16.x' -> '16'
                return clean_version
            else:
                print(
                    f"{Colors.YELLOW}Warning: Could not parse Node.js version '{node_version}' from engines.node. Using default 'lts'.{Colors.RESET}"
                )
                return "lts"  # Fallback to a common LTS version
        else:
            print(
                f"{Colors.YELLOW}Warning: 'engines.node' field not found in package.json. Using default Node.js 'lts' version.{Colors.RESET}"
            )
            return "lts"  # Default to a common LTS version if not specified

    except FileNotFoundError:
        print(
            f"{Colors.RED}Error: package.json not found at {package_json_path}. This should not happen if called correctly.{Colors.RESET}"
        )
        return None
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Invalid JSON in {package_json_path}.{Colors.RESET}")
        return None
    except Exception as e:
        print(
            f"{Colors.RED}An unexpected error occurred while reading package.json: {e}{Colors.RESET}"
        )
        return None


def find_project_info(project_path):
    """
    Finds project-related files like package.json and extracts necessary info.
    Checks for package.json existence and extracts Node.js version.
    """
    package_json_path = os.path.join(project_path, "package.json")

    if not os.path.exists(package_json_path):
        print(
            f"{Colors.RED}Error: No package.json found in '{project_path}'. "
            "This directory does not appear to be an NPM project.{Colors.RESET}"
        )
        return None

    node_version = get_node_version_from_package_json(package_json_path)

    if node_version:
        print(
            f"{Colors.GREEN}Detected Node.js version:{Colors.RESET} {Colors.BOLD}{node_version}{Colors.RESET}"
        )
        return {
            "node_version": node_version,
            "project_path": project_path,
            "package_manager": "npm",  # Defaulting to npm for now, will refine later
        }
    return None


def get_project_directory_interactive():
    """
    Prompts the user to enter the project directory path,
    offering a list of subdirectories to choose from.
    """
    current_path = os.getcwd()  # Start with the current working directory
    while True:
        print(f"\n{Colors.BOLD}Current directory:{Colors.RESET} {current_path}")
        subdirs = list_subdirectories(current_path)

        if subdirs:
            print(
                f"\n{Colors.BLUE}Detected subdirectories (select by number or enter path):{Colors.RESET}"
            )
            for i, subdir in enumerate(subdirs):
                # Check if the subdir is an NPM project and highlight it
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
            return None  # User chose to quit

        if choice == ".":
            # User chose current directory
            project_abs_path = os.path.abspath(current_path)
            if os.path.isdir(project_abs_path):
                # Before returning, ensure it's an NPM project
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
            # Go up one level
            parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
            if os.path.isdir(parent_path):
                current_path = parent_path
            else:
                print(
                    f"{Colors.RED}Error: Cannot go up from '{current_path}'. Already at root or invalid path.{Colors.RESET}"
                )
            continue  # Loop again to show new directory content
        elif choice.isdigit():
            # User selected a number from the list
            try:
                index = int(choice) - 1
                if 0 <= index < len(subdirs):
                    selected_path = subdirs[index]
                    # Check if the selected path contains package.json to suggest it as a project
                    if os.path.exists(os.path.join(selected_path, "package.json")):
                        print(
                            f"{Colors.GREEN}Selected project:{Colors.RESET} {os.path.basename(selected_path)}"
                        )
                        return selected_path
                    else:
                        # If not an NPM project, treat as a directory to navigate into
                        print(
                            f"{Colors.YELLOW}Selected directory '{os.path.basename(selected_path)}' is not an NPM project. Navigating into it.{Colors.RESET}"
                        )
                        current_path = selected_path
                        continue  # Loop again to show new directory content
                else:
                    print(
                        f"{Colors.RED}Invalid number. Please try again.{Colors.RESET}"
                    )
            except ValueError:
                # This block is technically redundant due to isdigit() but kept for robustness
                print(
                    f"{Colors.RED}Invalid input. Please enter a number, a path, '.', '..', or 'q'.{Colors.RESET}"
                )
        else:
            # User entered a custom path
            input_path = choice.strip('"').strip(
                "'"
            )  # NEW: Strip quotes from the input path

            if os.path.isabs(input_path):
                # If the input is already an absolute path, use it directly
                project_abs_path = os.path.abspath(input_path)
            else:
                # Otherwise, resolve it relative to the current_path
                project_abs_path = os.path.abspath(
                    os.path.join(current_path, input_path)
                )

            if not os.path.isdir(project_abs_path):
                print(
                    f"{Colors.RED}Error: The provided path '{project_abs_path}' is not a valid directory. Please try again.{Colors.RESET}"
                )
            else:
                # If it's a valid directory, check if it's an NPM project or navigate into it
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
                    continue  # Loop again to show new directory content


def main():
    """
    Main function to parse command-line arguments and start the process.
    """
    parser = argparse.ArgumentParser(
        description=f"{Colors.BOLD}CLI for building reproducible NPM project environments with Docker.{Colors.RESET}"
    )
    # Make project_dir optional by setting nargs='?'
    parser.add_argument(
        "project_dir",
        type=str,
        nargs="?",  # This makes the argument optional
        help="Path to the root directory of the NPM project.",
    )

    args = parser.parse_args()

    project_abs_path = None

    if args.project_dir:
        # If project_dir was provided as an argument
        project_abs_path = os.path.abspath(args.project_dir)
        if not os.path.isdir(project_abs_path):
            print(
                f"{Colors.RED}Error: The provided path '{project_abs_path}' is not a valid directory.{Colors.RESET}"
            )
            return
    else:
        # If project_dir was NOT provided, prompt the user with navigation
        project_abs_path = get_project_directory_interactive()
        if not project_abs_path:  # User chose to quit
            print(f"{Colors.YELLOW}Operation cancelled by user. Exiting.{Colors.RESET}")
            return

    print(
        f"{Colors.GREEN}CLI initialized. Analyzing project directory:{Colors.RESET} {Colors.BOLD}{project_abs_path}{Colors.RESET}"
    )

    # Call find_project_info
    project_info = find_project_info(project_abs_path)

    if project_info:
        print("\n--- Project Information ---")
        for key, value in project_info.items():
            print(f"{key}: {value}")
        print("---------------------------\n")
        print(
            f"{Colors.BLUE}Next: Generate the Dockerfile based on this information.{Colors.RESET}"
        )
    else:
        print(
            f"{Colors.RED}Failed to gather necessary project information. Exiting.{Colors.RESET}"
        )


if __name__ == "__main__":
    main()
