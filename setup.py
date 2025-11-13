#!/usr/bin/env python3
"""
OMA Agent Service Setup Script

This script sets up a new OMA agent service by:
1. Prompting for service name and agent name
2. Creating the project directory structure
3. Configuring pyproject.toml with the service name
4. Creating agent file from template
5. Updating main.py to register the agent
6. Updating test_agents.py with the agent test
7. Initializing git repository
"""

import os
import re
import shutil
import sys
from pathlib import Path


def get_input(prompt: str, validator=None) -> str:
    """Get user input with optional validation."""
    while True:
        value = input(prompt).strip()
        if not value:
            print("  Error: Input cannot be empty. Please try again.")
            continue
        if validator and not validator(value):
            continue
        return value


def validate_service_name(name: str) -> bool:
    """Validate service name format."""
    # Allow alphanumeric and hyphens, must start with letter
    if not re.match(r"^[a-z][a-z0-9-]*$", name):
        print(
            "  Error: Service name must start with a letter and contain only lowercase letters, numbers, and hyphens."
        )
        return False
    return True


def validate_agent_name(name: str) -> bool:
    """Validate agent name format."""
    # Allow alphanumeric and underscores, must start with letter
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        print(
            "  Error: Agent name must start with a letter and contain only lowercase letters, numbers, and underscores."
        )
        return False
    return True


def to_pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    parts = re.split(r"[_-]", name)
    return "".join(word.capitalize() for word in parts)


def setup_service():
    """Main setup function."""
    print("=" * 70)
    print("OMA Agent Service Setup")
    print("=" * 70)
    print()

    # Show where the service will be created
    script_dir = Path(__file__).parent
    parent_dir = script_dir.parent
    print(f"Scaffold location: {script_dir}")
    print(f"New service will be created in: {parent_dir}")
    print()

    # Get service name
    print("Step 1: Service Configuration")
    print("-" * 70)
    service_name = get_input(
        "Enter service name (e.g., 'document-processor'): ", validate_service_name
    )
    folder_name = f"oma-{service_name}"
    description = f"OMA {service_name.replace('-', ' ').title()} Service"

    print(f"\n  → Service folder: {folder_name}")
    print(f"  → Description: {description}")
    print()

    # Get agent name
    print("Step 2: Agent Configuration")
    print("-" * 70)
    agent_name = get_input(
        "Enter agent name (e.g., 'document_processor'): ", validate_agent_name
    )
    agent_class = to_pascal_case(agent_name)
    agent_file = f"{agent_name}.py"

    print(f"\n  → Agent class: {agent_class}")
    print(f"  → Agent file: app/agents/{agent_file}")
    print()

    # Confirm setup
    print("Step 3: Confirmation")
    print("-" * 70)
    print(f"Service Name:  {folder_name}")
    print(f"Description:   {description}")
    print(f"Agent Name:    {agent_name}")
    print(f"Agent Class:   {agent_class}")
    print()

    confirm = input("Proceed with setup? (y/n): ").strip().lower()
    if confirm != "y":
        print("\nSetup cancelled.")
        return

    print()
    print("Step 4: Creating Project")
    print("-" * 70)

    # Use parent_dir that was defined at the beginning of the function
    target_dir = parent_dir / folder_name

    # Check if target directory already exists
    if target_dir.exists():
        print(f"\n❌ Error: Directory '{folder_name}' already exists!")
        return

    try:
        # Create target directory
        print(f"Creating directory: {folder_name}")
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files and directories except setup.py and install.py
        print("Copying template files...")
        for item in script_dir.iterdir():
            if item.name in ["setup.py", "install.py", ".git", "__pycache__", ".DS_Store"]:
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
        content = content.replace('name = "oma-service-template"', f'name = "{folder_name}"')
        content = content.replace('description = "OMA Agent Service Template"', f'description = "{description}"')
        pyproject_path.write_text(content, encoding='utf-8')

        # Create agent file from template
        print(f"Creating agent file: app/agents/{agent_file}")
        agent_template_path = target_dir / "app" / "agents" / "agent_template.py"
        agent_path = target_dir / "app" / "agents" / agent_file

        agent_content = agent_template_path.read_text(encoding='utf-8')
        agent_content = agent_content.replace("AgentTemplate", agent_class)
        agent_content = agent_content.replace('agent_role: str = "agent_template"', f'agent_role: str = "{agent_name}"')
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
        agents_init.write_text(f'from .{agent_name} import {agent_class}\n\n__all__ = ["{agent_class}"]\n', encoding='utf-8')

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
            "test_map = {\n        # Add your test functions here\n        # Example:\n        # \"my_agent\": test_my_agent,\n        # \"my_agent_with_input\": test_my_agent_with_input,\n    }",
            f'test_map = {{\n        "{agent_name}": test_{agent_name},\n    }}',
        )

        test_path.write_text(test_content, encoding='utf-8')

        # Create sample directory
        print("Creating sample directory...")
        sample_dir = target_dir / "sample"
        sample_dir.mkdir(exist_ok=True)
        (sample_dir / ".gitkeep").touch()

        # Initialize git repository
        print("Initializing git repository...")
        os.chdir(target_dir)
        os.system("git init")

        # Create .gitignore
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# Poetry
poetry.lock

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
"""
        gitignore_path = target_dir / ".gitignore"
        gitignore_path.write_text(gitignore_content, encoding='utf-8')

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
        print(f"  5. python tests/test_agents.py --test {agent_name}  # Test your agent")
        print()
        print("For more information, see README.md")
        print()

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback

        traceback.print_exc()
        if target_dir.exists():
            print(f"\nCleaning up {folder_name}...")
            shutil.rmtree(target_dir)
        return


if __name__ == "__main__":
    try:
        setup_service()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
