# Reproducible Build CLI

This repository hosts a Python Command-Line Interface (CLI) tool designed to assist developers in creating reproducible build environments using Docker, primarily by leveraging existing YAML-based CI/CD configurations (like GitHub Actions workflows). The tool automates the process of identifying project build steps, generating a Dockerfile, and optionally building a Docker image and running a container, ensuring consistent environments for software builds.

## Table of Contents

1.  [Project Overview](#1-project-overview)
2.  [Features](#2-features)
3.  [Installation](#3-installation)
    * [Prerequisites](#prerequisites)
    * [CLI Setup](#cli-setup)
4.  [Usage](#4-usage)
    * [Interactive Mode](#interactive-mode)
    * [Command-Line Arguments](#command-line-arguments)
    * [Workflow Walkthrough](#workflow-walkthrough)
5.  [Project Structure](#5-project-structure)
6.  [Dockerfile and .dockerignore Generation](#6-dockerfile-and-dockerignore-generation)
7.  [Reproducibility Goals](#7-reproducibility-goals)
8.  [Future Enhancements](#8-future-enhancements)

## 1. Project Overview

In software development, ensuring that a build can be consistently reproduced across different environments is crucial for reliability, debugging, and collaboration. This CLI aims to simplify this by extracting build instructions from common YAML configuration files (e.g., `.github/workflows/*.yml` for GitHub Actions) and translating them into a Docker-based reproducible environment. It helps encapsulate the build process, making it independent of the host machine's setup.

## 2. Features

* **Interactive Project Selection**: Browse and select project directories from your filesystem.
* **YAML Configuration Discovery**: Automatically finds `.yml` and `.yaml` files within the selected project, which typically contain CI/CD pipeline definitions.
* **Build Step Extraction**: Parses selected YAML files to identify and extract `run` commands and Node.js version specifications from build jobs.
* **Git Integration**:
    * Automatically detects the current Git commit hash of a project.
    * Allows specifying a target commit hash for checkout, enabling builds of historical project states.
* **Dockerfile Generation**: Creates a Dockerfile tailored to the project's detected Node.js version and extracted build steps.
* **.dockerignore Generation**: Automatically creates or updates a `.dockerignore` file in the project root to exclude `node_modules` (and other common artifacts) from the Docker build context, optimizing image size.
* **Docker Image Building**: Integrates with your local Docker daemon to build a Docker image based on the generated Dockerfile. Images are tagged with the project name and (optionally) the commit hash for versioning.
* **Docker Container Execution**: Provides an option to immediately run a container from the newly built image.
* **Modular Design**: The codebase is split into logical modules for maintainability and extensibility.

## 3. Installation

To use this CLI, you need to have Python 3, Git, and Docker installed on your system.

### Prerequisites

* **Python 3.x**: Download from [python.org](https://www.python.org/downloads/).
* **Git**: Download from [git-scm.com](https://git-scm.com/downloads).
* **Docker Desktop (or Docker Engine)**: Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop). Ensure Docker is running in the background.

### CLI Setup

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/SV592/repro-build.git](https://github.com/SV592/repro-build.git)
    cd repro-build
    ```

2.  **Install Python Dependencies:**
    ```bash
    pip install PyYAML colorama
    ```
    * `PyYAML`: Used for parsing YAML files.
    * `colorama`: Used for colored terminal output.

## 4. Usage

The CLI can be run interactively or with command-line arguments.

### Interactive Mode

Simply run the main script without any arguments:

```bash
python repro_build_cli.py
```

The script will guide you through the process with prompts.

### Command-Line Arguments

You can also provide arguments directly:

```bash
python repro_build_cli.py [PROJECT_DIR] [--commit-hash <HASH>] [--yaml-file <PATH>] [--output-dockerfile <NAME>]
```

* `PROJECT_DIR`: (Optional) The path to your project's root directory. If omitted, the script will prompt you interactively.
* `--commit-hash <HASH>`: (Optional) A specific Git commit hash to check out for the build. If omitted, the script will attempt to auto-detect the current commit or prompt you.
* `--yaml-file <PATH>`: (Optional) The path to a specific YAML configuration file (relative to `PROJECT_DIR`) to use for build instructions. If omitted, the script will list detected YAML files and prompt for selection.
* `--output-dockerfile <NAME>`: (Optional) The desired filename for the generated Dockerfile. Defaults to `<project_name>_<commit_hash>.Dockerfile` or `<project_name>.Dockerfile`.

### Workflow Walkthrough

1.  **Select Project Directory**:
    * The CLI will list subdirectories in your current location. You can navigate up/down, select a numbered directory, or enter a full path.
    * A directory is considered a "YAML Project" if it contains `.yml` or `.yaml` files.

2.  **Specify Git Commit Hash**:
    * If the selected project is a Git repository, the CLI will auto-detect the current commit.
    * You can choose to use the detected commit, enter a different hash, or proceed without a specific commit (using the current state of the branch).
    * If a commit hash is provided, the script will attempt a `git checkout` to that hash.

3.  **Select YAML Configuration File**:
    * The CLI will list all detected `.yml` and `.yaml` files in your project.
    * Select the file that contains the build instructions you want to use (e.g., your GitHub Actions workflow file).

4.  **Select Build Job**:
    * From the selected YAML file, the CLI will list all defined jobs.
    * Choose the specific job that contains the relevant build steps (e.g., `build_and_test`).

5.  **Dockerfile Generation**:
    * A Dockerfile will be generated in the same directory as your `repro_build_cli.py` script.
    * The Dockerfile will be named like `<project_name>_<short_commit_hash>.Dockerfile` (e.g., `my_app_abcdef1.Dockerfile`).
    * It will include `FROM` (Node.js version from YAML), `WORKDIR`, `COPY . .`, and `RUN` commands extracted from your chosen YAML job.

6.  **.dockerignore Generation**:
    * A `.dockerignore` file will be created or updated in your *project's root directory*.
    * It will include `node_modules/` to prevent this large directory from being copied into the Docker image.

7.  **Docker Image Build**:
    * You will be prompted to confirm if you want to build the Docker image.
    * If confirmed, Docker will build the image, tagging it with a name derived from your project and commit hash.

8.  **Docker Container Run**:
    * If the image build is successful, you will be prompted to confirm if you want to run a container from the newly built image.
    * The container will run, executing the default `CMD` specified in the Dockerfile (or overridden if you customize the `run_docker_container` function).

## 5. Project Structure

The CLI is modularized into the following Python files:

* `repro_build_cli.py`: The main entry point. Parses arguments, orchestrates the workflow, and calls functions from other modules.
* `cli_colors.py`: Defines ANSI escape codes for colored terminal output, improving user experience.
* `project_discovery.py`: Handles interactive directory navigation, discovery of YAML files, and detection of project-specific information like package managers.
* `git_operations.py`: Contains functions for interacting with Git repositories, including checking out specific commits and retrieving the current commit hash.
* `yaml_processing.py`: Responsible for parsing YAML configuration files to extract build steps and other relevant project details. Includes logic for interactive YAML and job selection.
* `docker_management.py`: Provides functions for generating the Dockerfile content, building Docker images, and running Docker containers using the `subprocess` module to interact with the Docker CLI.

## 6. Dockerfile and .dockerignore Generation

The CLI automates the creation of essential Docker files:

* **Dockerfile**: Generated in the same directory as `repro_build_cli.py`. It uses `FROM node:<version>-alpine` (where `<version>` is derived from your YAML), sets `WORKDIR /app/<project_name>`, and includes `COPY . .` along with `RUN` commands extracted directly from your selected YAML build job.
* **.dockerignore**: Generated or updated in the *root of your actual project directory*. This file is critical for efficient Docker builds as it explicitly tells the Docker daemon to ignore specified paths (like `node_modules/`) when building the image. This prevents unnecessary files from being copied into the image, resulting in smaller, faster, and more secure images.

## 7. Reproducibility Goals

This CLI enhances reproducibility by:

* **Version Pinning**: By allowing checkout to a specific Git commit, it ensures that the exact state of the code at a given point in time is used.
* **Environment Standardization**: Docker encapsulates the build environment (Node.js version, dependencies, OS) into an image, making it consistent across different machines.
* **Automated Configuration**: Extracts build commands directly from existing CI/CD YAML, reducing manual transcription errors and ensuring the local build environment mirrors the CI environment.
