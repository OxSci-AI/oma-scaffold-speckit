from typing import List
from oxsci_shared_core.config import BaseConfig


class Config(BaseConfig):
    """
    Service configuration class extending BaseConfig from oxsci-shared-core.

    Add your custom configuration variables here as needed.
    """

    SERVICE_PORT: int = 8080
    # Add your MCP server names here if needed, don't include the ENV suffix, such "mcp-article-processing", not "mcp-article-processing-test"
    MCP_SERVER_NAMES: List[str] = []


config = Config()
