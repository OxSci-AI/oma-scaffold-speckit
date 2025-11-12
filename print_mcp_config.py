#!/usr/bin/env python3
"""
Print MCP Configuration and Tool List

This script loads and displays MCP configuration and available tools for testing.
Uses app.core.config to ensure exact same behavior as app runtime.

Usage:
    # Print server list (default environment from app.core.config)
    python print_mcp_config.py

    # Print server list for specific environment
    python print_mcp_config.py --env dev
    python print_mcp_config.py --env test
    python print_mcp_config.py --env prod

    # Print tools from all servers
    python print_mcp_config.py --tools

    # Print tools from specific server
    python print_mcp_config.py --tools --server mcp-article-processing

    # Print tools with detailed metadata (input parameters and output schemas)
    python print_mcp_config.py --tools --detail

    # Combine options
    python print_mcp_config.py --env dev --tools --server journal-insight-service --detail
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir.parent))

# Import app config - this loads .env and sets up environment exactly like app runtime
from app.core.config import config

from oxsci_oma_core.oma_mcp.mcp_config import load_mcp_config, MCPConfig


def print_section(title: str, width: int = 80, char: str = "=") -> None:
    """Print a section header"""
    print("\n" + char * width)
    print(f" {title}")
    print(char * width)


def print_subsection(title: str, width: int = 80) -> None:
    """Print a subsection header"""
    print("\n" + "-" * width)
    print(f" {title}")
    print("-" * width)


def print_server_list(env: str, mcp_config: MCPConfig) -> None:
    """Print MCP server configuration list"""
    enabled_servers = mcp_config.get_enabled_servers()

    if not enabled_servers:
        print("❌ No enabled servers")
        return

    print(f"ENV: {env.upper()}")
    for i, (server_name, config) in enumerate(enabled_servers.items(), 1):
        url = config.get_server_url()
        print(f"{i}. {server_name} ✅")
        print(f"    URL: {url}")


async def print_registered_tools(
    server_name: Optional[str] = None, detail: bool = False
) -> None:
    """Print tools registered in tool_registry

    Args:
        server_name: Specific server name to filter tools
        detail: Print detailed metadata including input/output schemas
    """
    from oxsci_oma_core.tools.registry import tool_registry
    from oxsci_oma_core.tools.mcp.dynamic_tool import get_mcp_tool_info
    import json

    print("\nRegistered Tools")
    print("=" * 80)

    # Trigger MCP tool discovery
    await tool_registry.discover_mcp_tools_if_needed()

    # Get all tool classes
    all_classes = {**tool_registry._tool_classes, **tool_registry._custom_tool_classes}

    if not all_classes:
        print("❌ No tools registered")
        return

    # Filter by server name if specified (for MCP tools)
    if server_name:
        filtered = {}
        for name, cls in all_classes.items():
            tool_info = get_mcp_tool_info(cls)
            if tool_info and tool_info.server == server_name:
                filtered[name] = cls

        if not filtered:
            print(f"❌ No tools found for server '{server_name}'")
            return
        all_classes = filtered

    print(f"Total: {len(all_classes)} tools\n")

    # Print each tool
    for tool_name, tool_class in sorted(all_classes.items()):
        # Get description from MCP tool info
        tool_info = get_mcp_tool_info(tool_class)
        description = tool_info.description if tool_info else "No description"

        print(f"• {tool_name}")
        print(f"  {description}")

        # Print detailed metadata if requested
        if detail and tool_info:
            print(f"  Server: {tool_info.server}")
            print(f"  Version: {tool_info.version}")

            # Print input parameters
            if tool_info.input_parameters:
                print(f"  Input Parameters:")
                for param in tool_info.input_parameters:
                    required_marker = "required" if param.required else "optional"
                    print(f"    - {param.name} ({param.type}, {required_marker})")
                    print(f"      {param.description}")
                    if param.default is not None:
                        print(f"      Default: {param.default}")
                    if param.example is not None:
                        print(f"      Example: {param.example}")
            else:
                print(f"  Input Parameters: None")

            # Print output schema
            if tool_info.output_schema:
                print(f"  Output Schema:")
                schema_str = json.dumps(tool_info.output_schema, indent=4)
                # Indent each line for better formatting
                for line in schema_str.split("\n"):
                    print(f"    {line}")
            else:
                print(f"  Output Schema: Not defined")

        print()  # Add blank line between tools


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Print MCP configuration and tool list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Print server list (default environment)
  poetry run python print_mcp_config.py

  # Print server list for test environment
  ENV=test poetry run python print_mcp_config.py

  # Print tools from all servers
  ENV=test poetry run python print_mcp_config.py --tools

  # Print tools from specific server
  ENV=test poetry run python print_mcp_config.py --tools --server mcp-article-processing

  # Print tools with detailed metadata
  ENV=test poetry run python print_mcp_config.py --tools --detail
        """,
    )
    parser.add_argument(
        "--tools", action="store_true", help="Discover and print tools from MCP servers"
    )
    parser.add_argument(
        "--server", type=str, help="Specific server name to query (use with --tools)"
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Print detailed tool metadata including input parameters and output schemas (use with --tools)",
    )

    args = parser.parse_args()

    # Get environment from app.core.config (same as app runtime)
    env = str(config.ENV).lower()
    # Handle enum value if ENV is Environment enum
    if "." in env:
        env = env.split(".")[-1]

    # Load MCP configuration
    try:
        config_dir = script_dir / "app" / "config" / "mcp"
        # Automatically reads from app.core.config (convention)
        mcp_config = load_mcp_config(config_dir)

        # Print server list
        print_server_list(env, mcp_config)

        # Print tools if requested
        if args.tools:
            asyncio.run(print_registered_tools(args.server, args.detail))

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
