import argparse
import os


def get_project_directory_interactive():
    """
    Prompts the user to enter the project directory path.
    """
    while True:
        project_path = input(
            "Please enter the path to your NPM project directory: "
        ).strip()
        if not project_path:
            print("Path cannot be empty. Please try again.")
            continue

        project_abs_path = os.path.abspath(project_path)
        if not os.path.isdir(project_abs_path):
            print(
                f"Error: The provided path '{project_abs_path}' is not a valid directory. Please try again."
            )
        else:
            return project_abs_path


def main():
    """
    Main function to parse command-line arguments and start the process.
    """
    parser = argparse.ArgumentParser(
        description="CLI for building reproducible NPM project environments with Docker."
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
                f"Error: The provided path '{project_abs_path}' is not a valid directory."
            )
            return
    else:
        # If project_dir was NOT provided, prompt the user
        project_abs_path = get_project_directory_interactive()
        if (
            not project_abs_path
        ):  # Should not happen with current get_project_directory_interactive logic, but good for robustness
            print("No valid project directory provided. Exiting.")
            return

    print(f"CLI initialized. Analyzing project directory: {project_abs_path}")
    print("Next: Detect project type and gather information.")


if __name__ == "__main__":
    main()
