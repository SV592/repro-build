# repro_build_cli.py

import argparse
import os
import colorama
import json
import re
import subprocess
import yaml

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


def find_yaml_files(project_path):
    """
    Scans the project directory and its subdirectories for all YAML configuration files.
    Returns a list of paths to detected YAML files.
    """
    yaml_files = []
    # Define directories to explicitly exclude from the recursive scan
    excluded_dirs = ["node_modules", "venv", ".git", "__pycache__"]

    try:
        for root, dirs, files in os.walk(project_path):
            # Modify dirs in-place to prune directories we don't want to walk into
            # This prevents os.walk from entering these directories
            dirs[:] = [
                d for d in dirs if d not in excluded_dirs and not d.startswith(".")
            ]

            for file in files:
                # Convert file extension to lowercase for case-insensitive check
                if file.lower().endswith((".yml", ".yaml")):
                    full_path = os.path.join(root, file)
                    yaml_files.append(full_path)
    except Exception as e:
        print(
            f"{Colors.YELLOW}Warning: Could not scan directory '{project_path}' for YAML files: {e}{Colors.RESET}"
        )

    return sorted(yaml_files)


def parse_yaml_for_build_info(yaml_file_path):
    """
    Parses a given YAML file to extract potential build instructions and Node.js versions.
    This is a preliminary parser and will be expanded.
    """
    build_steps = []
    detected_node_version = None

    try:
        with open(yaml_file_path, "r", encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)

        # --- Basic GitHub Actions (workflow) parsing attempt ---
        # Look for jobs and steps
        if isinstance(yaml_content, dict) and "jobs" in yaml_content:
            for job_name, job_details in yaml_content["jobs"].items():
                if isinstance(job_details, dict) and "steps" in job_details:
                    for step in job_details["steps"]:
                        if isinstance(step, dict):
                            # Extract run commands
                            if "run" in step:
                                build_steps.append(step["run"])
                            # Look for node-version in 'uses' actions (e.g., actions/setup-node@vX)
                            if "uses" in step and "actions/setup-node" in step["uses"]:
                                if "with" in step and "node-version" in step["with"]:
                                    node_version_from_yaml = str(
                                        step["with"]["node-version"]
                                    ).strip()
                                    # Clean up version string if it contains ranges or 'x'
                                    match = re.match(
                                        r"(\d+\.\d+(\.\d+|x)?).*",
                                        node_version_from_yaml,
                                    )
                                    if match:
                                        clean_version = match.group(1)
                                        if clean_version.endswith(".x"):
                                            detected_node_version = (
                                                clean_version.replace(".x", "")
                                            )
                                        else:
                                            detected_node_version = clean_version
                                    else:
                                        detected_node_version = node_version_from_yaml  # Use as is if not parsable by regex
                                    print(
                                        f"{Colors.CYAN}Info: Detected Node.js version '{detected_node_version}' from '{os.path.basename(yaml_file_path)}'.{Colors.RESET}"
                                    )
                                    # For now, we take the first one found. Could be refined later.
                                    break  # Exit inner loop once node version is found

                if detected_node_version:
                    break  # Exit outer loop if node version is found

        # --- Basic Docker Compose parsing attempt (for services/build contexts) ---
        # This is more for identifying services, not direct build steps for the host.
        # Could be expanded to extract build commands from service definitions.
        if isinstance(yaml_content, dict) and "services" in yaml_content:
            for service_name, service_details in yaml_content["services"].items():
                if isinstance(service_details, dict) and "build" in service_details:
                    # This indicates a Docker build context, not direct build steps for the host
                    pass  # Placeholder for future Docker Compose specific parsing

    except yaml.YAMLError as e:
        print(
            f"{Colors.RED}Error parsing YAML file '{yaml_file_path}': {e}{Colors.RESET}"
        )
    except Exception as e:
        print(
            f"{Colors.RED}An unexpected error occurred while parsing '{yaml_file_path}': {e}{Colors.RESET}"
        )

    return build_steps, detected_node_version


def find_project_info(project_path):
    """
    Finds project-related files (YAML files) and extracts necessary info.
    A project is considered valid ONLY if it has YAML files.
    """
    yaml_files = find_yaml_files(project_path)
    has_yaml_files = bool(yaml_files)  # True if list is not empty

    if not has_yaml_files:
        print(
            f"{Colors.RED}Error: No common YAML files found in '{project_path}'. "
            "This directory does not appear to be a recognized project type.{Colors.RESET}"
        )
        return None

    project_type = ["yaml"]  # Project type is now always 'yaml' if found
    print(f"{Colors.GREEN}Detected YAML configuration files:{Colors.RESET}")
    for yf in yaml_files:
        print(f"  - {os.path.relpath(yf, project_path)}")

    # Initialize build_instructions and node_version from YAML
    # These will now be populated AFTER user selects a specific YAML file
    all_build_steps = []
    final_node_version = None

    project_info = {
        "node_version": final_node_version,
        "project_path": project_path,
        "package_manager": None,
        "yaml_files": yaml_files,  # List of all detected YAML files
        "selected_yaml_file": None,  # New: To store the user's selected YAML file
        "project_type": project_type,
        "build_steps_from_yaml": all_build_steps,
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
                has_yaml = bool(
                    find_yaml_files(subdir)
                )  # Check for YAML files in subdir

                label = ""
                color = Colors.YELLOW  # Default for non-project folders
                if has_yaml:
                    label = f" {Colors.CYAN}(YAML Project){Colors.RESET}"
                    color = Colors.BLUE  # Use blue for YAML-only projects

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
                # Check ONLY for YAML files to consider it a project
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
                    # Check ONLY for YAML files to consider it a project
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
                # Check ONLY for YAML files to consider it a project
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


def git_checkout(repo_path, commit_hash):
    """
    Performs a git checkout to the specified commit hash in the given repository path.
    """
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(
            f"{Colors.RED}Error: '{repo_path}' is not a Git repository. Cannot perform checkout.{Colors.RESET}"
        )
        return False

    print(
        f"{Colors.BLUE}Attempting to checkout commit:{Colors.RESET} {Colors.BOLD}{commit_hash}{Colors.RESET} {Colors.BLUE}in '{repo_path}'...{Colors.RESET}"
    )
    try:
        # Use subprocess.run for better control and error handling
        result = subprocess.run(
            ["git", "checkout", commit_hash],
            cwd=repo_path,  # Execute the command in the project directory
            capture_output=True,  # Capture stdout and stderr
            text=True,  # Decode output as text
            check=True,  # Raise CalledProcessError if the command returns a non-zero exit code
        )
        print(f"{Colors.GREEN}Git checkout successful!{Colors.RESET}")
        # print(f"Output:\n{result.stdout}") # Uncomment for verbose git output
        return True
    except subprocess.CalledProcessError as e:
        print(
            f"{Colors.RED}Error during Git checkout to '{commit_hash}':{Colors.RESET}"
        )
        print(f"{Colors.RED}Command: {' '.join(e.cmd)}{Colors.RESET}")
        print(f"{Colors.RED}Stderr:\n{e.stderr}{Colors.RESET}")
        print(
            f"{Colors.YELLOW}Please ensure the commit hash is valid and the repository is clean (no uncommitted changes).{Colors.RESET}"
        )
        return False
    except FileNotFoundError:
        print(
            f"{Colors.RED}Error: 'git' command not found. Please ensure Git is installed and in your system's PATH.{Colors.RESET}"
        )
        return False
    except Exception as e:
        print(
            f"{Colors.RED}An unexpected error occurred during Git checkout: {e}{Colors.RESET}"
        )
        return False


def get_yaml_file_selection(yaml_files):
    """
    Presents a list of detected YAML files and prompts the user to select one.
    Returns the path to the selected YAML file, or None if the user quits.
    """
    while True:
        print(
            f"\n{Colors.BLUE}Multiple YAML files detected. Please select one to use for build instructions:{Colors.RESET}"
        )
        for i, yf_path in enumerate(yaml_files):
            print(f"  {Colors.YELLOW}[{i+1}]{Colors.RESET} {os.path.relpath(yf_path)}")
        print(f"  {Colors.YELLOW}[q]{Colors.RESET} Quit")

        choice = input(
            f"{Colors.CYAN}Enter a number or 'q' to quit: {Colors.RESET}"
        ).strip()

        if choice.lower() == "q":
            return None
        elif choice.isdigit():
            try:
                index = int(choice) - 1
                if 0 <= index < len(yaml_files):
                    selected_file = yaml_files[index]
                    print(
                        f"{Colors.GREEN}Selected YAML file:{Colors.RESET} {os.path.basename(selected_file)}"
                    )
                    return selected_file
                else:
                    print(
                        f"{Colors.RED}Invalid number. Please choose a number from the list.{Colors.RESET}"
                    )
            except ValueError:
                print(
                    f"{Colors.RED}Invalid input. Please enter a number or 'q'.{Colors.RESET}"
                )
        else:
            print(
                f"{Colors.RED}Invalid input. Please enter a number or 'q'.{Colors.RESET}"
            )


def main():
    """
    Main function to parse command-line arguments and start the process.
    """
    parser = argparse.ArgumentParser(
        description=f"{Colors.BOLD}CLI for building reproducible project environments with Docker.{Colors.RESET}"
    )
    parser.add_argument(
        "project_dir",
        type=str,
        nargs="?",
        help="Path to the root directory of the project.",
    )
    parser.add_argument(
        "--commit-hash",
        type=str,
        help="Optional: Git commit hash for the build to reproduce.",
    )
    parser.add_argument(
        "--yaml-file",  # New argument for direct YAML file selection
        type=str,
        help="Optional: Path to a specific YAML file to use for build instructions (relative to project_dir).",
    )

    args = parser.parse_args()

    while True:  # Loop to allow re-selection of project/commit/YAML
        project_abs_path = None
        commit_hash_to_use = None
        selected_yaml_file_path = None  # New variable to store the selected YAML file

        # Step 1: Get project directory
        if args.project_dir:
            project_abs_path = os.path.abspath(args.project_dir)
            # Now, validate if it's a recognized project (YAML-based only)
            if not os.path.isdir(project_abs_path) or not bool(
                find_yaml_files(project_abs_path)
            ):
                print(
                    f"{Colors.RED}Error: The provided path '{project_abs_path}' is not a valid directory or contains no common YAML files.{Colors.RESET}"
                )
                return  # Exit if argument path is invalid
            print(
                f"{Colors.GREEN}Selected project from argument:{Colors.RESET} {os.path.basename(project_abs_path)}"
            )
        else:
            project_abs_path = get_project_directory_interactive()
            if not project_abs_path:
                print(
                    f"{Colors.YELLOW}Operation cancelled by user. Exiting.{Colors.RESET}"
                )
                return  # Exit main if user quits interactive selection

        print(
            f"{Colors.GREEN}CLI initialized. Analyzing project directory:{Colors.RESET} {Colors.BOLD}{project_abs_path}{Colors.RESET}"
        )

        # Step 2: Get commit hash (from arg or interactively)
        if args.commit_hash:
            commit_hash_to_use = args.commit_hash
            print(
                f"{Colors.GREEN}Using commit hash from argument:{Colors.RESET} {Colors.BOLD}{commit_hash_to_use}{Colors.RESET}"
            )
        else:
            # Check if it's a Git repo before asking for commit hash
            if os.path.isdir(os.path.join(project_abs_path, ".git")):
                commit_hash_to_use = input(
                    f"{Colors.CYAN}Enter the Git commit hash for reproduction (leave blank for current state): {Colors.RESET}"
                ).strip()
                if not commit_hash_to_use:
                    print(
                        f"{Colors.YELLOW}No commit hash provided. Proceeding with current state of the project.{Colors.RESET}"
                    )
                else:
                    print(
                        f"{Colors.GREEN}Using commit hash from interactive input:{Colors.RESET} {Colors.BOLD}{commit_hash_to_use}{Colors.RESET}"
                    )
            else:
                print(
                    f"{Colors.YELLOW}Project is not a Git repository. Cannot use commit hash.{Colors.RESET}"
                )
                commit_hash_to_use = None  # Ensure it's None if not a git repo

        # Step 3: Perform Git checkout if a commit hash is available
        if commit_hash_to_use:
            if not git_checkout(project_abs_path, commit_hash_to_use):
                print(
                    f"{Colors.RED}Git checkout failed. Please select another project or try again.{Colors.RESET}"
                )
                # If checkout fails, restart the loop to allow re-selection
                continue

        # Step 4: Find project info based on the potentially checked-out state
        project_info = find_project_info(project_abs_path)

        if project_info:
            project_info["commit_hash"] = commit_hash_to_use

            # Step 5: Select YAML file for parsing
            if args.yaml_file:
                # If --yaml-file argument is provided, validate it
                arg_yaml_path = os.path.abspath(
                    os.path.join(project_abs_path, args.yaml_file)
                )
                if arg_yaml_path in project_info["yaml_files"]:
                    selected_yaml_file_path = arg_yaml_path
                    print(
                        f"{Colors.GREEN}Using YAML file from argument:{Colors.RESET} {os.path.basename(selected_yaml_file_path)}{Colors.RESET}"
                    )
                else:
                    print(
                        f"{Colors.RED}Error: Specified YAML file '{args.yaml_file}' not found in the project or is not a recognized YAML file. Please select from the detected files.{Colors.RESET}"
                    )
                    continue  # Restart loop to allow re-selection
            elif len(project_info["yaml_files"]) == 1:
                # If only one YAML file is found, automatically select it
                selected_yaml_file_path = project_info["yaml_files"][0]
                print(
                    f"{Colors.GREEN}Automatically selected single YAML file:{Colors.RESET} {os.path.basename(selected_yaml_file_path)}{Colors.RESET}"
                )
            elif len(project_info["yaml_files"]) > 1:
                # If multiple YAML files, prompt user to select
                selected_yaml_file_path = get_yaml_file_selection(
                    project_info["yaml_files"]
                )
                if not selected_yaml_file_path:
                    print(
                        f"{Colors.YELLOW}YAML file selection cancelled. Please select another project or try again.{Colors.RESET}"
                    )
                    continue  # Restart loop if user cancels YAML selection
            else:
                # This case should ideally be caught by find_project_info returning None
                print(
                    f"{Colors.YELLOW}No YAML configuration files found in the selected project. Please select another project or navigate.{Colors.RESET}"
                )
                continue  # Restart the loop if no YAML files

            project_info["selected_yaml_file"] = selected_yaml_file_path

            # Step 6: Parse the selected YAML file for build info
            if selected_yaml_file_path:
                build_steps, node_v = parse_yaml_for_build_info(selected_yaml_file_path)
                project_info["build_steps_from_yaml"] = build_steps
                # Only update node_version if it was found in the selected YAML
                if node_v:
                    project_info["node_version"] = node_v
            else:
                # If no YAML file was selected (e.g., user quit selection)
                print(
                    f"{Colors.RED}No YAML file selected for parsing. Cannot proceed with build analysis.{Colors.RESET}"
                )
                continue  # Restart the loop

            # Finally, print project info and break the main loop
            print("\n--- Project Information ---")
            for key, value in project_info.items():
                print(f"{key}: {value}")
            print("---------------------------\n")
            print(
                f"{Colors.BLUE}Next: Generate the Dockerfile based on this information and execute build.{Colors.RESET}"
            )
            break  # Exit the while loop as a valid YAML project with selected file is found
        else:
            # If find_project_info returned None (meaning no YAML found in that path)
            print(
                f"{Colors.RED}Failed to gather necessary project information. Please select another project or navigate.{Colors.RESET}"
            )
            continue  # Restart the loop to allow re-selection


if __name__ == "__main__":
    main()
