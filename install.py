#!/usr/bin/env python3
"""
OMA Agent Service Installer

Quick install:
    curl -sSL https://raw.githubusercontent.com/OxSci-AI/oma-scaffold/main/install.py | python3 -

This script:
1. Downloads the OMA scaffold template from GitHub
2. Prompts for service name and agent name
3. Creates a new OMA agent service
4. Initializes git repository

Dependencies:
    - Python 3.11+ (only uses Python standard library, no external packages)
    - Git (required for repository initialization)
    - Network connectivity to GitHub (required for downloading template)
    - AWS CLI (checked but not required - needed later for CodeArtifact access)
"""

import argparse
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, Tuple


GITHUB_REPO = "OxSci-AI/oma-scaffold"
GITHUB_BRANCH = "main"
GITHUB_ZIP_URL = (
    f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
)


def detect_platform() -> str:
    """Detect the operating system platform."""
    system = platform.system().lower()
    if system == "linux":
        # Try to detect Linux distribution
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read().lower()
                if "ubuntu" in content:
                    return "ubuntu"
                elif "debian" in content:
                    return "debian"
                elif "centos" in content or "rhel" in content:
                    return "centos"
                elif "arch" in content:
                    return "arch"
                else:
                    return "linux"
        except (OSError, IOError):
            return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def check_python_version() -> Tuple[bool, Optional[str]]:
    """Check if Python 3.11+ is installed."""
    try:
        version = sys.version_info
        if version.major >= 3 and version.minor >= 11:
            return True, f"{version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"{version.major}.{version.minor}.{version.micro}"
    except Exception:
        return False, None


def check_git() -> Tuple[bool, Optional[str]]:
    """Check if Git is installed."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip().split()[2]
            return True, version
        return False, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, None
    except Exception:
        return False, None


def check_network_connectivity() -> bool:
    """Check if network connectivity is available."""
    try:
        # Try to connect to GitHub
        socket.create_connection(("github.com", 443), timeout=5)
        return True
    except (OSError, socket.timeout):
        return False


def check_aws_cli() -> Tuple[bool, Optional[str]]:
    """Check if AWS CLI is installed."""
    try:
        result = subprocess.run(
            ["aws", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # AWS CLI output format: "aws-cli/2.x.x Python/3.x.x ..."
            version_line = result.stdout.strip().split("\n")[0]
            # Extract version part (e.g., "aws-cli/2.x.x")
            version = version_line.split()[0] if version_line else "installed"
            return True, version
        return False, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, None
    except Exception:
        return False, None


def check_environment() -> bool:
    """Check all required environment prerequisites."""
    print("=" * 70)
    print("Environment Check")
    print("=" * 70)
    print()

    # Detect platform
    detected_platform = detect_platform()
    print(f"  Platform: {detected_platform}")
    if detected_platform == "unknown":
        print("  ⚠️  Warning: Unknown platform detected")
    print()

    # Check Python version
    python_ok, python_version = check_python_version()
    if python_ok:
        print(f"  ✅ Python: {python_version} (required: 3.11+)")
    else:
        print(f"  ❌ Python: {python_version if python_version else 'Not found'}")
        print("     Required: Python 3.11 or higher")
        print()
        print("     Installation instructions:")
        if detected_platform == "ubuntu":
            print(
                "       sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv"
            )
        elif detected_platform == "macos":
            print("       brew install python@3.11")
        elif detected_platform == "windows":
            print("       Download from: https://www.python.org/downloads/")
        else:
            print("       Please install Python 3.11+ for your platform")
        return False
    print()

    # Check Git
    git_ok, git_version = check_git()
    if git_ok:
        print(f"  ✅ Git: {git_version}")
    else:
        print("  ❌ Git: Not found")
        print("     Git is required for repository initialization")
        print()
        print("     Installation instructions:")
        if detected_platform == "ubuntu":
            print("       sudo apt-get update && sudo apt-get install -y git")
        elif detected_platform == "macos":
            print("       brew install git")
        elif detected_platform == "windows":
            print("       Download from: https://git-scm.com/download/win")
        else:
            print("       Please install Git for your platform")
        return False
    print()

    # Check network connectivity
    network_ok = check_network_connectivity()
    if network_ok:
        print("  ✅ Network: Connected")
    else:
        print("  ❌ Network: No connection to GitHub")
        print("     Please check your internet connection")
        return False
    print()

    # Check write permissions for current directory
    try:
        test_file = Path.cwd() / ".install_test"
        test_file.touch()
        test_file.unlink()
        print("  ✅ Write permissions: OK")
    except (OSError, IOError):
        print("  ❌ Write permissions: Cannot write to current directory")
        print(f"     Current directory: {Path.cwd()}")
        print(
            "     Please run the script from a directory where you have write permissions"
        )
        return False
    print()

    # Check AWS CLI (warning only, not required for installation)
    aws_ok, aws_version = check_aws_cli()
    if aws_ok:
        print(f"  ✅ AWS CLI: {aws_version}")
        print(
            "     Note: AWS CLI is required for CodeArtifact access after installation"
        )
    else:
        print("  ⚠️  AWS CLI: Not found")
        print("     Warning: AWS CLI is required for CodeArtifact access")
        print("     You can install it later to configure dependency access")
        print()
        print("     Installation instructions:")
        if detected_platform == "ubuntu":
            print("       sudo apt-get update && sudo apt-get install -y awscli")
        elif detected_platform == "macos":
            print("       brew install awscli")
        elif detected_platform == "windows":
            print("       Download from: https://aws.amazon.com/cli/")
        else:
            print("       Please install AWS CLI for your platform")
    print()

    print("=" * 70)
    print("✅ All environment checks passed!")
    print("=" * 70)
    print()

    return True


def is_interactive() -> bool:
    """Check if stdin is available for interactive input."""
    return sys.stdin.isatty()


def get_input(prompt: str, validator=None) -> str:
    """Get user input with optional validation."""
    if not is_interactive():
        raise EOFError(
            "Cannot read input from stdin. Please use command-line arguments:\n"
            "  python3 install.py --service-name <name> --agent-name <name>\n"
            "Or download the script first and run it interactively:\n"
            "  curl -sSL https://raw.githubusercontent.com/OxSci-AI/oma-scaffold/main/install.py > install.py\n"
            "  python3 install.py"
        )
    while True:
        value = input(prompt).strip()
        if not value:
            print("  Error: Input cannot be empty. Please try again.")
            continue
        if validator and not validator(value):
            continue
        return value


def normalize_service_name(name: str) -> str:
    """Normalize service name: lowercase, convert spaces/special chars to hyphens."""
    # Convert to lowercase
    normalized = name.lower().strip()
    # Replace spaces and other non-alphanumeric characters (except hyphens) with hyphens
    normalized = re.sub(r"[^a-z0-9-]+", "-", normalized)
    # Remove leading/trailing hyphens and multiple consecutive hyphens
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    # Ensure it starts with a letter
    if normalized and not normalized[0].isalpha():
        # Find first letter and take from there
        match = re.search(r"[a-z]", normalized)
        if match:
            normalized = normalized[match.start() :]
        else:
            normalized = "service-" + normalized
    return normalized or "service"


def normalize_agent_name(name: str) -> str:
    """Normalize agent name: lowercase, convert spaces/hyphens/special chars to underscores."""
    # Convert to lowercase
    normalized = name.lower().strip()
    # Replace spaces, hyphens, and other non-alphanumeric characters with underscores
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    # Remove leading/trailing underscores and multiple consecutive underscores
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    # Ensure it starts with a letter
    if normalized and not normalized[0].isalpha():
        # Find first letter and take from there
        match = re.search(r"[a-z]", normalized)
        if match:
            normalized = normalized[match.start() :]
        else:
            normalized = "agent_" + normalized
    return normalized or "agent"


def validate_service_name(name: str) -> bool:
    """Validate service name format (after normalization)."""
    if not name or not re.match(r"^[a-z][a-z0-9-]*$", name):
        print(
            "  Error: Service name must start with a letter and contain only lowercase letters, numbers, and hyphens."
        )
        return False
    return True


def validate_agent_name(name: str) -> bool:
    """Validate agent name format (after normalization)."""
    if not name or not re.match(r"^[a-z][a-z0-9_]*$", name):
        print(
            "  Error: Agent name must start with a letter and contain only lowercase letters, numbers, and underscores."
        )
        return False
    return True


def to_pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    parts = re.split(r"[_-]", name)
    return "".join(word.capitalize() for word in parts)


def download_and_extract_scaffold(temp_dir: Path) -> Path:
    """Download and extract scaffold from GitHub."""
    print("Downloading scaffold from GitHub...")

    zip_path = temp_dir / "scaffold.zip"

    try:
        # Download zip file
        with urllib.request.urlopen(GITHUB_ZIP_URL) as response:
            with open(zip_path, "wb") as out_file:
                out_file.write(response.read())

        print("Extracting files...")

        # Extract zip file
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find extracted directory (should be oma-scaffold-main or similar)
        extracted_dirs = [
            d
            for d in temp_dir.iterdir()
            if d.is_dir() and d.name.startswith("oma-scaffold")
        ]

        if not extracted_dirs:
            raise Exception("Could not find extracted scaffold directory")

        return extracted_dirs[0]

    except Exception as e:
        print(f"❌ Failed to download scaffold: {e}")
        print("\nAlternative installation method:")
        print("1. Clone the repository:")
        print(f"   git clone https://github.com/{GITHUB_REPO}.git")
        print("2. Run setup.py:")
        print("   cd oma-scaffold && python setup.py")
        sys.exit(1)


def setup_service(
    service_name: Optional[str] = None,
    agent_name: Optional[str] = None,
    skip_confirm: bool = False,
    skip_env_check: bool = False,
):
    """Main setup function.

    Note: This script should be run from the parent directory where you want to create
    the service. For example, if you want to create the service at /git/oma-service-name/,
    run this script from /git/ directory. The script will create oma-{service-name}/
    in the current working directory.
    """
    print("=" * 70)
    print("OMA Agent Service Installer")
    print("=" * 70)
    print()

    # Show current directory for clarity
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    print("Note: The service will be created in a subdirectory of this location.")
    print()

    # Perform environment checks (unless skipped)
    if not skip_env_check:
        if not check_environment():
            print(
                "\n❌ Environment check failed. Please fix the issues above and try again."
            )
            print(
                "   You can skip this check with --skip-env-check flag (not recommended)"
            )
            sys.exit(1)

    # Get service name
    print("Step 1: Service Configuration")
    print("-" * 70)
    if service_name is None:
        raw_service_name = get_input(
            "Enter service name (e.g., 'document-processor'): "
        )
        service_name = normalize_service_name(raw_service_name)
        if not validate_service_name(service_name):
            sys.exit(1)
        if raw_service_name != service_name:
            print(f"  → Normalized to: {service_name}")
    else:
        original_service_name = service_name
        service_name = normalize_service_name(service_name)
        if not validate_service_name(service_name):
            sys.exit(1)
        if original_service_name != service_name:
            print(
                f"Service name: {original_service_name} → normalized to: {service_name}"
            )
        else:
            print(f"Service name: {service_name}")

    folder_name = f"oma-{service_name}"
    description = f"OMA {service_name.replace('-', ' ').title()} Service"

    print(f"\n  → Service folder: {folder_name}")
    print(f"  → Description: {description}")
    print()

    # Get agent name
    print("Step 2: Agent Configuration")
    print("-" * 70)
    if agent_name is None:
        raw_agent_name = get_input("Enter agent name (e.g., 'document_processor'): ")
        agent_name = normalize_agent_name(raw_agent_name)
        if not validate_agent_name(agent_name):
            sys.exit(1)
        if raw_agent_name != agent_name:
            print(f"  → Normalized to: {agent_name}")
    else:
        original_agent_name = agent_name
        agent_name = normalize_agent_name(agent_name)
        if not validate_agent_name(agent_name):
            sys.exit(1)
        if original_agent_name != agent_name:
            print(f"Agent name: {original_agent_name} → normalized to: {agent_name}")
        else:
            print(f"Agent name: {agent_name}")

    agent_class = to_pascal_case(agent_name)
    agent_file = f"{agent_name}.py"

    print(f"\n  → Agent class: {agent_class}")
    print(f"  → Agent file: app/agents/{agent_file}")
    print()

    # Confirm setup
    if not skip_confirm:
        print("Step 3: Confirmation")
        print("-" * 70)
        print(f"Service Name:  {folder_name}")
        print(f"Description:   {description}")
        print(f"Agent Name:    {agent_name}")
        print(f"Agent Class:   {agent_class}")
        print()

        if is_interactive():
            confirm = input("Proceed with setup? (y/n): ").strip().lower()
            if confirm != "y":
                print("\nSetup cancelled.")
                return
        else:
            print("Note: Non-interactive mode detected. Proceeding with setup...")
            print()

    print()
    print("Step 4: Creating Project")
    print("-" * 70)

    # Determine target parent directory
    # If running from oma-scaffold directory itself, create in parent directory
    # Otherwise, create in current directory (default behavior for downloaded script)
    script_dir = Path(__file__).parent
    if script_dir.name.startswith("oma-scaffold"):
        # Running from local oma-scaffold directory, create in parent (sibling directory)
        parent_dir = script_dir.parent
        print(f"Detected local scaffold directory, creating in: {parent_dir}")
    else:
        # Running from downloaded script, use current working directory
        parent_dir = Path.cwd()
        print(f"Creating in current directory: {parent_dir}")
    print()

    target_dir = parent_dir / folder_name

    # Check if target directory already exists
    if target_dir.exists():
        print(f"\n❌ Error: Directory '{folder_name}' already exists!")
        return

    # Create temporary directory for download
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # Download scaffold
            scaffold_dir = download_and_extract_scaffold(temp_path)

            # Create target directory
            print(f"Creating directory: {folder_name}")
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy all files and directories except setup.py and install.py
            print("Copying template files...")
            for item in scaffold_dir.iterdir():
                if item.name in [
                    "setup.py",
                    "install.py",
                    ".git",
                    "__pycache__",
                    ".DS_Store",
                    "README.md",
                ]:
                    continue

                dest = target_dir / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    shutil.copytree(item, dest)

            # .specify and .claude directories are now included as part of the template

            # Update constitution.md with service name
            print("Configuring constitution.md...")
            constitution_path = target_dir / ".specify" / "memory" / "constitution.md"
            if constitution_path.exists():
                constitution_content = constitution_path.read_text(encoding='utf-8')
                service_title = f"{description}"
                constitution_content = constitution_content.replace(
                    "Oxsci Manuscript Service Constitution",
                    f"{service_title} Constitution"
                )
                constitution_path.write_text(constitution_content, encoding='utf-8')

            # Update pyproject.toml
            print("Configuring pyproject.toml...")
            pyproject_path = target_dir / "pyproject.toml"
            content = pyproject_path.read_text(encoding='utf-8')
            content = content.replace(
                'name = "oma-service-template"', f'name = "{folder_name}"'
            )
            content = content.replace(
                'description = "OMA Agent Service Template"',
                f'description = "{description}"',
            )
            pyproject_path.write_text(content, encoding='utf-8')

            # Create agent file from template
            print(f"Creating agent file: app/agents/{agent_file}")
            agent_template_path = target_dir / "app" / "agents" / "agent_template.py"
            agent_path = target_dir / "app" / "agents" / agent_file

            agent_content = agent_template_path.read_text(encoding='utf-8')
            agent_content = agent_content.replace("AgentTemplate", agent_class)
            agent_content = agent_content.replace(
                'agent_role: str = "agent_template"',
                f'agent_role: str = "{agent_name}"',
            )
            agent_content = agent_content.replace(
                'name="Agent Template"', f'name="{agent_class}"'
            )
            agent_content = agent_content.replace(
                'description="Template agent for demonstration purposes"',
                f'description="{agent_class} agent"',
            )

            agent_path.write_text(agent_content, encoding='utf-8')

            # Remove template file
            agent_template_path.unlink()

            # Create __init__.py for agents
            agents_init = target_dir / "app" / "agents" / "__init__.py"
            agents_init.write_text(
                f'from .{agent_name} import {agent_class}\n\n__all__ = ["{agent_class}"]\n',
                encoding='utf-8'
            )

            # Create __init__.py for app
            app_init = target_dir / "app" / "__init__.py"
            app_init.touch()

            # Update main.py
            print("Updating main.py...")
            main_path = target_dir / "app" / "core" / "main.py"
            main_content = main_path.read_text(encoding='utf-8')

            # Add import after the TODO comment
            import_line = f"from app.agents.{agent_name} import {agent_class}"
            main_content = main_content.replace(
                "# TODO: Add your agent imports here\n# Example: from app.agents.my_agent import MyAgent",
                f"# Agent imports\n{import_line}",
            )

            # Add to agent_executors
            main_content = main_content.replace(
                "agent_executors = [\n        # Example: MyAgent,\n    ]",
                f"agent_executors = [\n        {agent_class},\n    ]",
            )

            main_path.write_text(main_content, encoding='utf-8')

            # Update test_agents.py
            print("Updating test_agents.py...")
            test_path = target_dir / "tests" / "test_agents.py"
            test_content = test_path.read_text(encoding='utf-8')

            # Add import
            import_line = f"from app.agents.{agent_name} import {agent_class}"
            test_content = test_content.replace(
                "# Import your agent classes here\n# Example:\n# from app.agents.my_agent import MyAgent",
                f"# Import agent classes\n{import_line}",
            )

            # Add test function
            test_function = f'''

@agent_test(sample_pdf="sample/sample.pdf")
def test_{agent_name}():
    """Test {agent_class} - processes PDF documents"""
    return {agent_class}
'''
            test_content = test_content.replace(
                "# ============================================================================\n# Single Agent Tests\n# ============================================================================\n\n",
                f"# ============================================================================\n# Single Agent Tests\n# ============================================================================\n{test_function}\n",
            )

            # Add to test_map
            test_content = test_content.replace(
                'test_map = {\n        # Add your test functions here\n        # Example:\n        # "my_agent": test_my_agent,\n        # "my_agent_with_input": test_my_agent_with_input,\n    }',
                f'test_map = {{\n        "{agent_name}": test_{agent_name},\n    }}',
            )

            test_path.write_text(test_content, encoding='utf-8')

            # Create sample directory (in tests directory, relative to test file)
            print("Creating sample directory...")
            sample_dir = target_dir / "tests" / "sample"
            sample_dir.mkdir(parents=True, exist_ok=True)
            (sample_dir / ".gitkeep").touch()

            # Create README.md
            readme_content = f"""# {folder_name}

{description}

## Quick Start

### 1. Configure AWS CodeArtifact

```bash
./entrypoint-dev.sh
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Run Tests

```bash
python tests/test_agents.py --test {agent_name}
```

### 4. Run Service

```bash
poetry run uvicorn app.core.main:app --reload --port 8080
```

## Documentation

For detailed documentation, see: https://github.com/{GITHUB_REPO}
"""
            readme_path = target_dir / "README.md"
            readme_path.write_text(readme_content, encoding='utf-8')

            # Initialize git repository
            print("Initializing git repository...")
            os.chdir(target_dir)
            os.system("git init")

            # Note: .gitignore is copied from template, no need to create it here

            print()
            print("=" * 70)
            print("✅ Setup Complete!")
            print("=" * 70)
            print()
            print(f"Your OMA agent service has been created in: {folder_name}")
            print()
            print("Next steps:")
            print()
            print(f"  1. cd {folder_name}")
            print(f"  2. ./entrypoint-dev.sh          # Configure AWS CodeArtifact")
            print(f"  3. poetry install                # Install dependencies")
            print(f"  4. Edit app/agents/{agent_file}  # Implement your agent logic")
            print(
                f"  5. python tests/test_agents.py --test {agent_name}  # Test your agent"
            )
            print()
            print(f"For more information, see: https://github.com/{GITHUB_REPO}")
            print()

        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            import traceback

            traceback.print_exc()
            if target_dir.exists():
                print(f"\nCleaning up {folder_name}...")
                shutil.rmtree(target_dir)
            return


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="OMA Agent Service Installer - Creates a new OMA agent service in the current directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (download and run separately):
  cd /git
  curl -sSL https://raw.githubusercontent.com/OxSci-AI/oma-scaffold/main/install.py > install.py
  python3 install.py

  # Non-interactive mode with arguments:
  cd /git
  curl -sSL https://raw.githubusercontent.com/OxSci-AI/oma-scaffold/main/install.py | python3 - --service-name document-processor --agent-name document_processor --yes

  # Non-interactive mode with auto-confirm:
  cd /git
  python3 install.py --service-name my-service --agent-name my_agent --yes

Note: 
  - Run this script from the parent directory where you want to create the service
  - Example: To create /git/oma-my-service/, run the script from /git/ directory
  - The script will create oma-{service-name}/ in the current working directory
        """,
    )
    parser.add_argument(
        "--service-name",
        type=str,
        help="Service name (e.g., 'document-processor'). Must start with a letter and contain only lowercase letters, numbers, and hyphens.",
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        help="Agent name (e.g., 'document_processor'). Must start with a letter and contain only lowercase letters, numbers, and underscores.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt (useful for non-interactive mode)",
    )
    parser.add_argument(
        "--skip-env-check",
        action="store_true",
        help="Skip environment prerequisites check (not recommended)",
    )

    args = parser.parse_args()

    # If stdin is not a TTY and no arguments provided, show error
    if not is_interactive() and (args.service_name is None or args.agent_name is None):
        parser.error(
            "Cannot read input from stdin. Please provide --service-name and --agent-name arguments.\n"
            "Example: python3 install.py --service-name document-processor --agent-name document_processor\n"
            "Or download the script first and run it interactively:\n"
            "  curl -sSL https://raw.githubusercontent.com/OxSci-AI/oma-scaffold/main/install.py > install.py\n"
            "  python3 install.py"
        )

    try:
        setup_service(
            service_name=args.service_name,
            agent_name=args.agent_name,
            skip_confirm=args.yes,
            skip_env_check=args.skip_env_check,
        )
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except EOFError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
