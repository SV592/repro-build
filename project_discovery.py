import os
import yaml
from cli_colors import Colors  # Import Colors from its new module


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
    return sorted(subdirs)


def find_yaml_files(project_path):
    """
    Scans the project directory and its subdirectories for all YAML configuration files.
    Returns a list of paths to detected YAML files.
    """
    yaml_files = []
    excluded_dirs = ["node_modules", "venv", ".git", "__pycache__"]

    try:
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [
                d for d in dirs if d not in excluded_dirs and not d.startswith(".")
            ]

            for file in files:
                if file.lower().endswith((".yml", ".yaml")):
                    full_path = os.path.join(root, file)
                    yaml_files.append(full_path)
    except Exception as e:
        print(
            f"{Colors.YELLOW}Warning: Could not scan directory '{project_path}' for YAML files: {e}{Colors.RESET}"
        )

    return sorted(yaml_files)


def find_project_info(project_path):
    """
    Finds project-related files (YAML files) and extracts necessary info.
    A project is considered valid ONLY if it has YAML files.
    """
    yaml_files = find_yaml_files(project_path)
    has_yaml_files = bool(yaml_files)

    if not has_yaml_files:
        print(
            f"{Colors.RED}Error: No common YAML files found in '{project_path}'. "
            "This directory does not appear to be a recognized project type.{Colors.RESET}"
        )
        return None

    project_type = ["yaml"]
    print(f"{Colors.GREEN}Detected YAML configuration files:{Colors.RESET}")
    for yf in yaml_files:
        print(f"  - {os.path.relpath(yf, project_path)}")

    all_jobs_parsed_info = {}
    # Note: parse_yaml_for_build_info is now in yaml_processing.py

    project_info = {
        "node_version": None,
        "project_path": project_path,
        "package_manager": None,
        "yaml_files": yaml_files,
        "selected_yaml_file": None,
        "project_type": project_type,
        "build_steps_from_yaml": [],
        "parsed_jobs_info": all_jobs_parsed_info,  # This will be populated later
    }
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
                has_yaml = bool(find_yaml_files(subdir))

                label = ""
                color = Colors.YELLOW
                if has_yaml:
                    label = f" {Colors.CYAN}(YAML Project){Colors.RESET}"
                    color = Colors.BLUE

                print(
                    f"  {color}[{i+1}]{Colors.RESET} {os.path.basename(subdir)}{label}"
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
                if bool(find_yaml_files(project_abs_path)):
                    print(
                        f"{Colors.GREEN}Selected project:{Colors.RESET} {os.path.basename(project_abs_path)}"
                    )
                    return project_abs_path
                else:
                    print(
                        f"{Colors.RED}Error: Current directory '{os.path.basename(project_abs_path)}' is not a recognized project (no common YAML files found). Please select a valid project or navigate.{Colors.RESET}"
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
                    if bool(find_yaml_files(selected_path)):
                        print(
                            f"{Colors.GREEN}Selected project:{Colors.RESET} {os.path.basename(selected_path)}"
                        )
                        return selected_path
                    else:
                        print(
                            f"{Colors.YELLOW}Selected directory '{os.path.basename(selected_path)}' is not a recognized project. Navigating into it.{Colors.RESET}"
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
                if bool(find_yaml_files(project_abs_path)):
                    print(
                        f"{Colors.GREEN}Selected project:{Colors.RESET} {os.path.basename(project_abs_path)}"
                    )
                    return project_abs_path
                else:
                    print(
                        f"{Colors.YELLOW}Entered directory '{os.path.basename(project_abs_path)}' is not a recognized project. Navigating into it.{Colors.RESET}"
                    )
                    current_path = project_abs_path
                    continue


# This block allows project_discovery.py to be run directly for testing its interactive part
if __name__ == "__main__":
    print(
        f"{Colors.BOLD}--- Running project_discovery.py directly for testing ---{Colors.RESET}"
    )
    selected_dir = get_project_directory_interactive()
    if selected_dir:
        print(
            f"\n{Colors.GREEN}Interactive selection complete. Selected directory: {selected_dir}{Colors.RESET}"
        )
    else:
        print(f"\n{Colors.YELLOW}No directory selected.{Colors.RESET}")
