# OMA Agent Service Template

A scaffold template for building OMA (OxSci Multi-Agent) services using the CrewAI framework. More frameworks will be added in the future.

## Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- AWS CLI configured with access to CodeArtifact (for installing dependencies from CodeArtifact)

> **Note**: Docker is only required for CI/CD deployment workflows, not for local development.

## Installation

### Installation Prerequisites

The installer script itself only requires **Python 3.11+** (uses only Python standard library, no external packages needed).

However, to complete the installation, you also need:
- **Git** installed (for initializing the repository)
- **Network connectivity** to GitHub (for downloading the template)
- **Write permissions** in the directory where you'll run the script

The installer will also check for:
- **AWS CLI** (warning only - required later for CodeArtifact access, but not needed during installation)

The installer will automatically check these prerequisites before proceeding.

### Option 1: Quick Install (Recommended)

Install directly from GitHub with a single command. You can use either command-line arguments (recommended) or interactive prompts.

> **Important**: Run the script from the **parent directory** where you want to create the service. For example:
> - To create `/git/oma-my-service/`, run the script from `/git/` directory
> - The script will create `oma-{service-name}/` in the current working directory

#### Direct Installation with Arguments (Recommended)

The simplest way - directly download and execute with parameters:

```bash
# Navigate to the parent directory where you want to create the service
cd /git

# Run the installer
curl -sSL https://raw.githubusercontent.com/OxSci-AI/oma-scaffold/main/install.py | python3 - \
  --service-name document-processor \
  --agent-name document_processor \
  --yes
```

Command-line options:
- `--service-name`: Service name (must start with a letter, lowercase letters/numbers/hyphens only)
- `--agent-name`: Agent name (must start with a letter, lowercase letters/numbers/underscores only)
- `--yes` or `-y`: Skip confirmation prompt (recommended for non-interactive mode)
- `--skip-env-check`: Skip environment prerequisites check (not recommended)

#### Interactive Mode

If you prefer to answer prompts interactively, download the script first:

```bash
# Navigate to the parent directory where you want to create the service
cd /git

# Download and run interactively
curl -sSL https://raw.githubusercontent.com/OxSci-AI/oma-scaffold/main/install.py > install.py
python3 install.py
```

The script will:
1. **Check environment prerequisites** (Python 3.11+, Git, network connectivity)
2. **Show current directory** and confirm where the service will be created
3. **Prompt for service name** (e.g., `document-processor` - will create `oma-document-processor` directory)
4. **Prompt for agent name** (e.g., `document_processor` - will create the agent file and configure it)

> **Note**: If you try to use the pipe method without arguments, you'll get an `EOFError` because stdin is redirected. Always provide `--service-name` and `--agent-name` when using the pipe method.

The installer will:
1. Verify environment prerequisites (Python 3.11+, Git, network)
2. Download the latest scaffold template from GitHub
3. Create a new project directory with all files configured
4. Initialize a git repository
5. Set up the agent structure and configuration files

### Option 2: Manual Setup

If you prefer to clone the repository first:

```bash
# Clone the repository
git clone https://github.com/OxSci-AI/oma-scaffold.git
cd oma-scaffold

# Run setup script
python setup.py
```

The setup script will prompt you for:
- Service name (will create `oma-{service-name}` directory)
- Agent name (will create the agent file and configure it)

## Quick Start

After installation, navigate to your new service directory:

```bash
cd oma-{your-service-name}
```

### 1. Configure AWS CodeArtifact

Before installing dependencies, configure access to the private package repository:

```bash
# Make the script executable (if not already)
chmod +x entrypoint-dev.sh

# Run the configuration script (valid for 12 hours)
./entrypoint-dev.sh
```

> **Note**: The authentication token expires after 12 hours. Re-run this script when needed.

### 2. Install Dependencies

```bash
poetry install
```

### 3. Configure MCP Tools (Optional)

MCP (Model Context Protocol) tools provide external capabilities to your agents, such as article processing, journal insights, and more.

#### Understanding MCP Configuration

MCP servers are configured through JSON files in `app/config/mcp/`:

- **base.json**: Default configuration for all MCP servers (defines all available servers with default settings)
- **dev.json**: Development environment overrides (enables local MCP servers)
- **test.json**: Test environment overrides (uses cloud MCP services)
- **prod.json**: Production environment overrides

The configuration system uses inheritance: environment-specific files (dev/test/prod) override values from base.json.

#### Checking Available MCP Tools

Use the `print_mcp_config.py` script to inspect configured MCP servers and their available tools:

```bash
# List all configured MCP servers
poetry run python print_mcp_config.py

# List all available tools from MCP servers
poetry run python print_mcp_config.py --tools

# List tools with detailed metadata (input parameters, output schemas)
poetry run python print_mcp_config.py --tools --detail

# Filter tools by specific MCP server
poetry run python print_mcp_config.py --tools --server journal-insight-service

# Combine filters with detailed output
poetry run python print_mcp_config.py --tools --server mcp-article-processing --detail
```

#### Configuring MCP Servers

1. **Development (Local)**: Edit `app/config/mcp/dev.json` to enable/disable MCP servers
   ```json
   {
     "servers": {
       "mcp-article-processing": {
         "enabled": true
       }
     }
   }
   ```

2. **Test/Production (Cloud)**: MCP servers can use proxy mode for cloud access
   - Set `"proxy": true` in environment-specific config
   - Configure `MCP_PROXY_URL` and `PROXY_API_KEY` environment variables

For local development, ensure the required MCP services are running on their configured ports (see base.json).

### 4. Development

#### Run Tests

```bash
# Run all tests
python tests/test_agents.py --all

# Run specific agent test
python tests/test_agents.py --test your_agent_name

# Run integration tests
python tests/test_agents.py --integration full_pipeline

# Enable verbose logging
python tests/test_agents.py --test your_agent_name -v
```

#### Run Service Locally

```bash
poetry run uvicorn app.core.main:app --reload --port 8080
```

Access the API documentation at: http://localhost:8080/docs

## Project Structure

```
oma-{service-name}/
├── .github/
│   └── workflows/
│       └── docker-builder.yml    # CI/CD workflow for building and deploying
├── .claude/
│   └── commands/                 # Claude Code slash commands
│       ├── speckit.specify.md    # Feature specification command
│       ├── speckit.plan.md       # Implementation planning command
│       ├── speckit.tasks.md      # Task generation command
│       ├── speckit.clarify.md    # Clarification workflow command
│       ├── speckit.implement.md  # Implementation execution command
│       ├── speckit.analyze.md    # Cross-artifact analysis command
│       ├── speckit.checklist.md  # Custom checklist generation command
│       └── speckit.constitution.md # Constitution management command
├── .specify/
│   ├── memory/
│   │   └── constitution.md       # Project constitution and principles
│   ├── templates/
│   │   ├── spec-template.md      # Feature specification template
│   │   ├── plan-template.md      # Implementation plan template
│   │   ├── tasks-template.md     # Task breakdown template
│   │   ├── checklist-template.md # Custom checklist template
│   │   └── agent-file-template.md # Agent file documentation template
│   └── scripts/
│       └── powershell/           # PowerShell automation scripts
│           ├── create-new-feature.ps1
│           ├── setup-plan.ps1
│           ├── update-agent-context.ps1
│           ├── check-prerequisites.ps1
│           └── common.ps1
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Service configuration
│   │   └── main.py               # FastAPI application entry point
│   ├── config/
│   │   └── mcp/                  # MCP tool configuration
│   │       ├── base.json         # Base MCP server definitions
│   │       ├── dev.json          # Development environment overrides
│   │       ├── test.json         # Test environment overrides
│   │       └── prod.json         # Production environment overrides
│   ├── agents/
│   │   └── {agent_name}.py       # Your agent implementation
│   └── tools/
│       └── __init__.py           # Custom tools (if needed)
├── tests/
│   ├── test_agents.py            # Agent tests
│   └── sample/                   # Sample test files (PDFs, etc.)
│       └── .gitkeep
├── .vscode/
│   └── extensions.json           # Recommended VS Code extensions
├── Dockerfile                     # Multi-stage Docker build
├── entrypoint-dev.sh             # CodeArtifact configuration script
├── print_mcp_config.py           # MCP configuration and tool inspection utility
├── pyproject.toml                # Project dependencies and configuration
└── README.md                      # This file
```

## SpecKit Workflow (Optional)

This template includes an integrated specification and planning workflow powered by SpecKit:

### What is SpecKit?

SpecKit provides a structured approach to feature development through Claude Code slash commands:

1. **`/speckit.specify`** - Create feature specifications from natural language descriptions
2. **`/speckit.clarify`** - Identify and resolve ambiguities in specifications
3. **`/speckit.plan`** - Generate detailed implementation plans
4. **`/speckit.tasks`** - Break down plans into actionable tasks
5. **`/speckit.implement`** - Execute implementation tasks automatically
6. **`/speckit.analyze`** - Validate cross-artifact consistency

### Project Constitution

The `.specify/memory/constitution.md` file defines core principles for your project:

- OMA Framework compliance requirements
- Development standards and patterns
- Testing requirements
- Code organization guidelines

This constitution is automatically customized with your service name during installation and guides all feature development decisions.

### Using SpecKit Commands

```bash
# In Claude Code, use slash commands to drive development:
/speckit.specify Add user authentication with OAuth2 support
/speckit.plan
/speckit.tasks
/speckit.implement
```

The workflow creates organized feature branches and documentation in `specs/[number]-[feature-name]/` directories.

For detailed SpecKit documentation, see `.claude/commands/` for individual command instructions.

## MCP Tool Configuration

### What are MCP Tools?

MCP (Model Context Protocol) tools are external services that provide specialized capabilities to your agents:

- **journal-insight-service**: Article search, journal information, PDF processing
- **mcp-article-processing**: Structured content processing, section management

MCP tools are automatically discovered and registered at startup based on your configuration.

### Configuration Files

MCP servers are configured using JSON files in `app/config/mcp/`:

1. **base.json**: Defines all available MCP servers with complete configuration
   - Server endpoints (service_name, port)
   - Connection settings (timeout, retry_interval)
   - Proxy configuration (for cloud access)
   - Default: all servers disabled

2. **Environment-specific files** (dev.json, test.json, prod.json):
   - Override base.json settings
   - Enable/disable servers per environment
   - Set environment-specific URLs or proxy settings

Example base.json:

```json
{
  "servers": {
    "journal-insight-service": {
      "enabled": false,
      "service_name": "journal-insight-service-prod",
      "port": 8010,
      "timeout": 30,
      "proxy": false,
      "proxy_url": "${MCP_PROXY_URL}",
      "api_key": "${PROXY_API_KEY}"
    }
  }
}
```

Example dev.json (only overrides):

```json
{
  "servers": {
    "journal-insight-service": {
      "enabled": true
    }
  }
}
```

### Using MCP Tools in Agents

MCP tools are automatically available to all agents through the tool registry. You don't need to import them explicitly - just reference them by name in your agent configuration:

```python
from crewai import Agent, Task

agent = Agent(
    role="Research Assistant",
    goal="Find and analyze academic articles",
    tools=[
        "search_articles",      # MCP tool from journal-insight-service
        "get_article",          # MCP tool from journal-insight-service
        "get_pdf_pages"         # MCP tool from mcp-article-processing
    ]
)
```

Use `print_mcp_config.py --tools` to see all available MCP tools and their descriptions.

## Agent Development

### Creating a New Agent

1. Create a new file in `app/agents/` (e.g., `my_agent.py`)
2. Extend the `ITaskExecutor` interface
3. Implement required methods:
   - `get_agent_config()`: Define agent metadata and I/O schema
   - `execute()`: Main execution logic
   - Agent and task definitions using CrewAI

Refer to `app/agents/agent_template.py` for a complete example.

### Registering Your Agent

Add your agent to the `agent_executors` list in `app/core/main.py`:

```python
from app.agents.my_agent import MyAgent

agent_executors = [
    MyAgent,
    # Add more agents here
]
```

## Testing

The project uses the `oxsci-oma-core` test module which provides:

- `@agent_test` decorator for single agent tests
- `@integration_test` decorator for multi-agent pipeline tests
- Automatic test environment setup and teardown
- Sample PDF processing for document-based agents

See `tests/test_agents.py` for examples.

## Deployment

### Building Docker Image

The CI/CD workflow automatically builds and pushes Docker images when:

- Tags matching `v*` are pushed
- Manually triggered via workflow_dispatch

### Manual Deployment

```bash
# Build image
docker build -t your-agent-service .

# Run container
docker run -p 8080:8080 \
  -e ENV=test \
  your-agent-service
```

## Configuration

Service configuration is managed through environment variables. See `app/core/config.py` for available options.

Key environment variables:

- `SERVICE_PORT`: Port to run the service (default: 8080)
- `ENV`: Environment (development/test/production)
- `LOG_LEVEL`: Logging level

## Tools and Frameworks

This template integrates:

- **FastAPI**: Web framework for building APIs
- **CrewAI**: Multi-agent orchestration framework
- **oxsci-oma-core**: Core OMA agent functionality
- **oxsci-shared-core**: Shared utilities and configuration

## License

© 2025 OxSci.AI. All rights reserved.
