"""
Custom Tools Package

Add your custom tools here if needed. Most common tools are available
in oxsci_oma_core.tools.local and oxsci_oma_core.tools.api.

Example custom tool structure:

from typing import Type
from pydantic import BaseModel, Field
from crewai_tools import BaseTool


class MyCustomToolInput(BaseModel):
    '''Input schema for MyCustomTool'''
    param1: str = Field(..., description="Description of param1")
    param2: int = Field(..., description="Description of param2")


class MyCustomTool(BaseTool):
    name: str = "My Custom Tool"
    description: str = "Description of what this tool does"
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, param1: str, param2: int) -> str:
        '''Implement tool logic here'''
        result = f"Processed {param1} with {param2}"
        return result
"""
