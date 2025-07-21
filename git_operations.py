import os
import subprocess
from cli_colors import Colors


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
        result = subprocess.run(
            ["git", "checkout", commit_hash],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"{Colors.GREEN}Git checkout successful!{Colors.RESET}")
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


def get_current_git_commit_hash(repo_path):
    """
    Gets the current full commit hash of the Git repository at repo_path.
    Returns the commit hash string or None if not a Git repo or error occurs.
    """
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        return None

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(
            f"{Colors.YELLOW}Warning: Could not get current Git commit hash for '{repo_path}': {e.stderr.strip()}{Colors.RESET}"
        )
        return None
    except FileNotFoundError:
        print(
            f"{Colors.YELLOW}Warning: 'git' command not found. Cannot auto-detect commit hash.{Colors.RESET}"
        )
        return None
    except Exception as e:
        print(
            f"{Colors.YELLOW}Warning: An unexpected error occurred while getting Git commit hash: {e}{Colors.RESET}"
        )
        return None
