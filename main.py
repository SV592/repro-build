import argparse
import os
import colorama

# Colorama for cross-platform ANSI support
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
                print(
                    f"  {Colors.YELLOW}[{i+1}]{Colors.RESET} {os.path.basename(subdir)}"
                )
            print(f"  {Colors.YELLOW}[.]{Colors.RESET} Stay in current directory")
            print(f"  {Colors.YELLOW}[..]{Colors.RESET} Go up one level")
            print(f"  {Colors.YELLOW}[q]{Colors.RESET} Quit")
        else:
            print(
                f"{Colors.YELLOW}No subdirectories found in '{current_path}'.{Colors.RESET}"
            )
            print(f"  {Colors.YELLOW}[.]{Colors.RESET} Stay in current directory")
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
                return project_abs_path
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
            input_path = choice
            project_abs_path = os.path.abspath(
                os.path.join(current_path, input_path)
            )  # Resolve relative to current_path

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
            print(f"{Colors.YELLOW}Operation cancelled by user.{Colors.RESET}")
            return

    print(
        f"{Colors.GREEN}CLI initialized. Analyzing project directory:{Colors.RESET} {Colors.BOLD}{project_abs_path}{Colors.RESET}"
    )
    print(
        f"{Colors.BLUE}Next: Detect project type and gather information.{Colors.RESET}"
    )


if __name__ == "__main__":
    main()
