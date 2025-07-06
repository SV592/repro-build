import os
import re
import yaml
from cli_colors import Colors  # Import Colors from its new module


def parse_yaml_for_build_info(yaml_file_path):
    """
    Parses a given YAML file to extract potential build instructions and Node.js versions per job.
    Returns a dictionary of job_name -> {'steps': [], 'node_version': None}.
    """
    jobs_info = {}

    try:
        with open(yaml_file_path, "r", encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)

        if isinstance(yaml_content, dict) and "jobs" in yaml_content:
            for job_name, job_details in yaml_content["jobs"].items():
                current_job_steps = []
                current_job_node_version = None

                if isinstance(job_details, dict) and "steps" in job_details:
                    for step in job_details["steps"]:
                        if isinstance(step, dict):
                            if "run" in step:
                                current_job_steps.append(step["run"])
                            if "uses" in step and "actions/setup-node" in step["uses"]:
                                if "with" in step and "node-version" in step["with"]:
                                    if current_job_node_version is None:
                                        node_version_from_yaml = str(
                                            step["with"]["node-version"]
                                        ).strip()
                                        match = re.match(
                                            r"(\d+\.\d+(\.\d+|x)?).*",
                                            node_version_from_yaml,
                                        )
                                        if match:
                                            clean_version = match.group(1)
                                            if clean_version.endswith(".x"):
                                                current_job_node_version = (
                                                    clean_version.replace(".x", "")
                                                )
                                            else:
                                                current_job_node_version = clean_version
                                        else:
                                            current_job_node_version = (
                                                node_version_from_yaml
                                            )
                                        print(
                                            f"{Colors.CYAN}Info: Detected Node.js version '{current_job_node_version}' for job '{job_name}' in '{os.path.basename(yaml_file_path)}'.{Colors.RESET}"
                                        )

                if current_job_steps or current_job_node_version:
                    jobs_info[job_name] = {
                        "steps": current_job_steps,
                        "node_version": current_job_node_version,
                    }

    except yaml.YAMLError as e:
        print(
            f"{Colors.RED}Error parsing YAML file '{yaml_file_path}': {e}{Colors.RESET}"
        )
    except Exception as e:
        print(
            f"{Colors.RED}An unexpected error occurred while parsing '{yaml_file_path}': {e}{Colors.RESET}"
        )

    return jobs_info


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
