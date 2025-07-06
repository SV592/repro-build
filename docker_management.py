import os
import subprocess
from cli_colors import Colors  # Import Colors from its new module


def generate_dockerfile_from_yaml_info(project_info):
    """
    Generates the content for a Dockerfile based on information extracted from YAML.
    """
    node_version = project_info.get("node_version", "lts")
    build_steps = project_info.get("build_steps_from_yaml", [])
    project_name = os.path.basename(project_info["project_path"])

    dockerfile_content = f"""
# Use a specific Node.js version for reproducibility, derived from YAML
FROM node:{node_version}-alpine

# Set the working directory in the container
WORKDIR /app/{project_name}

# Copy all project files into the container
COPY . .

# Install dependencies and run build steps as defined in YAML
# These steps are extracted from the selected YAML file.
"""
    if build_steps:
        dockerfile_content += "\n# Build steps from YAML:\n"
        for i, step in enumerate(build_steps):
            cleaned_step = step.replace("\n", " \\\n    ")
            dockerfile_content += f"RUN {cleaned_step}\n"
    else:
        dockerfile_content += (
            "# No specific build steps found in the selected YAML file.\n"
        )
        dockerfile_content += (
            "# You may need to add manual installation/build commands here.\n"
        )

    return dockerfile_content.strip()


def build_docker_image(project_path, image_name, dockerfile_path_in_script_dir):
    """
    Builds a Docker image from the Dockerfile in the script's directory, using project_path as context.
    """
    print(
        f"\n{Colors.BLUE}Attempting to build Docker image '{image_name}' from '{project_path}'...{Colors.RESET}"
    )
    try:
        command = [
            "docker",
            "build",
            "-t",
            image_name,
            "-f",
            dockerfile_path_in_script_dir,
            project_path,
        ]
        print(f"{Colors.CYAN}Executing: {' '.join(command)}{Colors.RESET}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(
            f"{Colors.GREEN}Docker image '{image_name}' built successfully!{Colors.RESET}"
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error during Docker image build:{Colors.RESET}")
        print(f"{Colors.RED}Command: {' '.join(e.cmd)}{Colors.RESET}")
        print(f"{Colors.RED}Stderr:\n{e.stderr}{Colors.RESET}")
        return False
    except FileNotFoundError:
        print(
            f"{Colors.RED}Error: 'docker' command not found. Please ensure Docker is installed and in your system's PATH.{Colors.RESET}"
        )
        return False
    except Exception as e:
        print(
            f"{Colors.RED}An unexpected error occurred during Docker build: {e}{Colors.RESET}"
        )
        return False


def run_docker_container(
    image_name, container_name=None, port_mapping=None, command=None
):
    """
    Runs a Docker container from the specified image.
    """
    print(
        f"\n{Colors.BLUE}Attempting to run Docker container from image '{image_name}'...{Colors.RESET}"
    )
    run_command = ["docker", "run", "--rm"]

    if container_name:
        run_command.extend(["--name", container_name])

    if port_mapping:
        run_command.extend(["-p", port_mapping])

    run_command.append(image_name)

    if command:
        run_command.extend(command.split())

    print(f"{Colors.CYAN}Executing: {' '.join(run_command)}{Colors.RESET}")
    try:
        subprocess.run(run_command, check=True, text=True, stdout=None, stderr=None)
        print(
            f"{Colors.GREEN}Docker container '{container_name or image_name}' started successfully!{Colors.RESET}"
        )
        print(
            f"{Colors.GREEN}Press Ctrl+C to stop the container (if running in foreground).{Colors.RESET}"
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error during Docker container run:{Colors.RESET}")
        print(f"{Colors.RED}Command: {' '.join(e.cmd)}{Colors.RESET}")
        print(f"{Colors.RED}Stderr:\n{e.stderr}{Colors.RESET}")
        return False
    except FileNotFoundError:
        print(
            f"{Colors.RED}Error: 'docker' command not found. Please ensure Docker is installed and in your system's PATH.{Colors.RESET}"
        )
        return False
    except Exception as e:
        print(
            f"{Colors.RED}An unexpected error occurred during Docker run: {e}{Colors.RESET}"
        )
        return False
