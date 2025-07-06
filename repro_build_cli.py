# repro_build_cli.py

import argparse
import os
import sys

# Import modules
from cli_colors import Colors
from project_discovery import get_project_directory_interactive, find_project_info
from git_operations import git_checkout, get_current_git_commit_hash
from yaml_processing import get_yaml_file_selection, parse_yaml_for_build_info
from docker_management import (
    generate_dockerfile_from_yaml_info,
    build_docker_image,
    run_docker_container,
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
        "--yaml-file",
        type=str,
        help="Optional: Path to a specific YAML file to use for build instructions (relative to project_dir).",
    )
    parser.add_argument(
        "--output-dockerfile",
        type=str,
        default="Dockerfile",
        help="Name of the Dockerfile to generate (default: Dockerfile or <project_name>_<commit_hash>.Dockerfile).",
    )

    args = parser.parse_args()

    while True:  # Loop to allow re-selection of project/commit/YAML
        project_abs_path = None
        commit_hash_to_use = None
        selected_yaml_file_path = None

        # Step 1: Get project directory
        if args.project_dir:
            project_abs_path = os.path.abspath(args.project_dir)
            # Validate if it's a recognized project (YAML-based only)
            # This check is now done within find_project_info, which is called later.
            # For initial validation, we just check if it's a directory.
            if not os.path.isdir(project_abs_path):
                print(
                    f"{Colors.RED}Error: The provided path '{project_abs_path}' is not a valid directory.{Colors.RESET}"
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
                current_repo_commit = get_current_git_commit_hash(project_abs_path)
                if current_repo_commit:
                    print(
                        f"{Colors.CYAN}Detected current Git commit: {current_repo_commit[:7]}...{Colors.RESET}"
                    )
                    prompt_choice = (
                        input(
                            f"{Colors.CYAN}Use this commit ({current_repo_commit[:7]}...)? [Y/n/q] (or enter a different hash): {Colors.RESET}"
                        )
                        .strip()
                        .lower()
                    )
                    if prompt_choice == "y" or prompt_choice == "":
                        commit_hash_to_use = current_repo_commit
                        print(
                            f"{Colors.GREEN}Using current Git commit: {commit_hash_to_use[:7]}...{Colors.RESET}"
                        )
                    elif prompt_choice == "n":
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
                    elif prompt_choice == "q":
                        print(
                            f"{Colors.YELLOW}Operation cancelled by user. Exiting.{Colors.RESET}"
                        )
                        return
                    else:
                        commit_hash_to_use = prompt_choice
                        print(
                            f"{Colors.GREEN}Using provided Git commit: {commit_hash_to_use[:7]}...{Colors.RESET}"
                        )
                else:
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
                commit_hash_to_use = None

        # Step 3: Perform Git checkout if a commit hash is available
        if commit_hash_to_use:
            if not git_checkout(project_abs_path, commit_hash_to_use):
                print(
                    f"{Colors.RED}Git checkout failed. Please select another project or try again.{Colors.RESET}"
                )
                continue

        # Step 4: Find project info based on the potentially checked-out state
        project_info = find_project_info(project_abs_path)

        if project_info:
            project_info["commit_hash"] = commit_hash_to_use

            # Step 5: Select YAML file for parsing
            if args.yaml_file:
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
                    continue
            elif len(project_info["yaml_files"]) == 1:
                selected_yaml_file_path = project_info["yaml_files"][0]
                # Corrected line: Ensure the f-string is complete
                print(
                    f"{Colors.GREEN}Automatically selected single YAML file:{Colors.RESET} {os.path.basename(selected_yaml_file_path)}{Colors.RESET}"
                )
            elif len(project_info["yaml_files"]) > 1:
                selected_yaml_file_path = get_yaml_file_selection(
                    project_info["yaml_files"]
                )
                if not selected_yaml_file_path:
                    print(
                        f"{Colors.YELLOW}YAML file selection cancelled. Please select another project or try again.{Colors.RESET}"
                    )
                    continue
            else:
                print(
                    f"{Colors.YELLOW}No YAML configuration files found in the selected project. Please select another project or navigate.{Colors.RESET}"
                )
                continue

            project_info["selected_yaml_file"] = selected_yaml_file_path

            # Step 6: Parse the selected YAML file for build info and select job
            if selected_yaml_file_path:
                parsed_jobs_info = parse_yaml_for_build_info(selected_yaml_file_path)
                project_info["parsed_jobs_info"] = parsed_jobs_info

                selected_job_name = None
                if len(parsed_jobs_info) == 1:
                    selected_job_name = list(parsed_jobs_info.keys())[0]
                    print(
                        f"{Colors.GREEN}Automatically selected single job '{selected_job_name}' from YAML file.{Colors.RESET}"
                    )
                elif len(parsed_jobs_info) > 1:
                    print(
                        f"\n{Colors.BLUE}Multiple jobs detected in '{os.path.basename(selected_yaml_file_path)}'. Please select the build job:{Colors.RESET}"
                    )
                    job_names = list(parsed_jobs_info.keys())
                    for i, job_n in enumerate(job_names):
                        print(f"  {Colors.YELLOW}[{i+1}]{Colors.RESET} {job_n}")
                    print(f"  {Colors.YELLOW}[q]{Colors.RESET} Quit")

                    while True:
                        job_choice = input(
                            f"{Colors.CYAN}Enter a number or 'q' to quit: {Colors.RESET}"
                        ).strip()
                        if job_choice.lower() == "q":
                            print(
                                f"{Colors.YELLOW}Job selection cancelled. Please select another project or try again.{Colors.RESET}"
                            )
                            continue
                        elif job_choice.isdigit():
                            try:
                                index = int(job_choice) - 1
                                if 0 <= index < len(job_names):
                                    selected_job_name = job_names[index]
                                    print(
                                        f"{Colors.GREEN}Selected job:{Colors.RESET} {selected_job_name}"
                                    )
                                    break
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
                else:
                    print(
                        f"{Colors.YELLOW}No jobs found in the selected YAML file. Cannot extract build steps.{Colors.RESET}"
                    )
                    continue

                if selected_job_name:
                    job_details = parsed_jobs_info.get(selected_job_name, {})
                    project_info["build_steps_from_yaml"] = job_details.get("steps", [])
                    if job_details.get("node_version"):
                        project_info["node_version"] = job_details["node_version"]
                    else:
                        print(
                            f"{Colors.YELLOW}Warning: No Node.js version detected in the selected job '{selected_job_name}'. Defaulting to 'lts'.{Colors.RESET}"
                        )
                        project_info["node_version"] = "lts"
                else:
                    print(
                        f"{Colors.RED}No build job selected. Cannot proceed with build analysis.{Colors.RESET}"
                    )
                    continue

            else:
                print(
                    f"{Colors.RED}No YAML file selected for parsing. Cannot proceed with build analysis.{Colors.RESET}"
                )
                continue

            # Step 7: Generate Dockerfile
            project_name = os.path.basename(project_info["project_path"])
            dockerfile_output_name = args.output_dockerfile

            if dockerfile_output_name == "Dockerfile":
                dockerfile_output_name = project_name
                if project_info["commit_hash"]:
                    dockerfile_output_name += f"_{project_info['commit_hash'][:7]}"
                dockerfile_output_name += ".Dockerfile"

            dockerfile_content = generate_dockerfile_from_yaml_info(project_info)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            dockerfile_path = os.path.join(script_dir, dockerfile_output_name)

            try:
                with open(dockerfile_path, "w", encoding="utf-8") as f:
                    f.write(dockerfile_content)
                print(
                    f"\n{Colors.GREEN}Dockerfile generated successfully at:{Colors.RESET} {Colors.BOLD}{dockerfile_path}{Colors.RESET}"
                )
                print("\n--- Generated Dockerfile Content ---")
                print(dockerfile_content)
                print("------------------------------------\n")
            except IOError as e:
                print(
                    f"{Colors.RED}Error writing Dockerfile to {dockerfile_path}: {e}{Colors.RESET}"
                )
                print(
                    f"{Colors.YELLOW}Please ensure you have write permissions in the script's directory.{Colors.RESET}"
                )
                continue

            # Step 8: Generate or update .dockerignore
            dockerignore_path = os.path.join(project_abs_path, ".dockerignore")
            ignore_entry = "node_modules/"

            try:
                if os.path.exists(dockerignore_path):
                    with open(dockerignore_path, "r+", encoding="utf-8") as f:
                        content = f.read()
                        if ignore_entry not in content:
                            f.write(f"\n{ignore_entry}")
                            print(
                                f"{Colors.GREEN}Added '{ignore_entry}' to existing .dockerignore file.{Colors.RESET}"
                            )
                        else:
                            print(
                                f"{Colors.YELLOW}'.dockerignore' already contains '{ignore_entry}'. No changes made.{Colors.RESET}"
                            )
                else:
                    with open(dockerignore_path, "w", encoding="utf-8") as f:
                        f.write(ignore_entry)
                    print(
                        f"{Colors.GREEN}Created '.dockerignore' file with '{ignore_entry}'.{Colors.RESET}"
                    )
            except IOError as e:
                print(
                    f"{Colors.RED}Error generating/updating .dockerignore at {dockerignore_path}: {e}{Colors.RESET}"
                )
                print(
                    f"{Colors.YELLOW}Please ensure you have write permissions in the project directory.{Colors.RESET}"
                )

            # Step 9: Docker Build and Run
            image_tag = dockerfile_output_name.replace(".Dockerfile", "").lower()

            build_choice = (
                input(
                    f"\n{Colors.CYAN}Do you want to build the Docker image '{image_tag}'? [Y/n]: {Colors.RESET}"
                )
                .strip()
                .lower()
            )
            if build_choice == "y" or build_choice == "":
                # Pass the full path to the generated Dockerfile
                if build_docker_image(project_abs_path, image_tag, dockerfile_path):
                    run_choice = (
                        input(
                            f"{Colors.CYAN}Do you want to run the Docker container from '{image_tag}'? [Y/n]: {Colors.RESET}"
                        )
                        .strip()
                        .lower()
                    )
                    if run_choice == "y" or run_choice == "":
                        run_docker_container(image_tag)
                    else:
                        print(
                            f"{Colors.YELLOW}Skipping Docker container run.{Colors.RESET}"
                        )
                else:
                    print(
                        f"{Colors.RED}Docker image build failed. Skipping container run.{Colors.RESET}"
                    )
            else:
                print(
                    f"{Colors.YELLOW}Skipping Docker image build and container run.{Colors.RESET}"
                )

            print("\n--- Project Information ---")
            for key, value in project_info.items():
                print(f"{key}: {value}")
            print("---------------------------\n")
            print(f"{Colors.BLUE}Process completed.{Colors.RESET}")
            break
        else:
            print(
                f"{Colors.RED}Failed to gather necessary project information. Please select another project or navigate.{Colors.RESET}"
            )
            continue


if __name__ == "__main__":
    main()
