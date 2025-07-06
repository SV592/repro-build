import argparse
import os

# For some color
import colorama

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


def get_project_directory_interactive():
    """
    Prompts the user to enter the project directory path.
    """
    while True:
        project_path = input(
            f"{Colors.CYAN}Please enter the path to your NPM project directory: {Colors.RESET}"
        ).strip()
        if not project_path:
            print(
                f"{Colors.YELLOW}Path cannot be empty. Please try again.{Colors.RESET}"
            )
            continue

        project_abs_path = os.path.abspath(project_path)
        if not os.path.isdir(project_abs_path):
            print(
                f"{Colors.RED}Error: The provided path '{project_abs_path}' is not a valid directory. Please try again.{Colors.RESET}"
            )
        else:
            return project_abs_path


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
        # If project_dir was NOT provided, prompt the user
        project_abs_path = get_project_directory_interactive()
        if not project_abs_path:
            print(
                f"{Colors.RED}No valid project directory provided. Exiting.{Colors.RESET}"
            )
            return

    print(
        f"{Colors.GREEN}CLI initialized. Analyzing project directory:{Colors.RESET} {Colors.BOLD}{project_abs_path}{Colors.RESET}"
    )
    print(
        f"{Colors.BLUE}Next: Detect project type and gather information.{Colors.RESET}"
    )


if __name__ == "__main__":
    main()
