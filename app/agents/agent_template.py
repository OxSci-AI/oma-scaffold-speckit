"""
Agent Template

This template provides a basic structure for creating a new agent using CrewAI framework.
Replace the placeholders with your agent's specific implementation.
"""

from __future__ import annotations

from typing import Any, Dict
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase
from oxsci_shared_core.logging import logger


# Import OMA-Core interfaces
from oxsci_oma_core import OMAContext, IAdapter
from oxsci_oma_core.models.adapter import ITaskExecutor
from oxsci_oma_core.models.agent_config import AgentConfig


@CrewBase
class AgentTemplate(ITaskExecutor):
    """
    Template Agent for [Brief Description]

    This agent [describe the agent's purpose and functionality].

    Implements ITaskExecutor interface to be used with TaskScheduler.
    """

    # Agent role identifier (must be unique across all agents)
    agent_role: str = "agent_template"

    def __init__(self, context: OMAContext, adapter: IAdapter):
        """
        Initialize the agent.

        Args:
            context: OMA context containing task input and environment
            adapter: Framework adapter (e.g., CrewAIToolAdapter) for tool conversion
        """
        self.context = context
        self.adapter = adapter
        # Create LLM instance with appropriate model and temperature
        self.llm = self.adapter.create_llm(
            # set model in orchestrator.agents.context or use default
            model=context.get_shared_data("model", "openrouter/openai/gpt-4o-mini"),
            temperature=0.1,  # Adjust based on creativity needs (0.0 = deterministic, 1.0 = creative)
        )
        self.logger = logger

    @classmethod
    def get_agent_config(cls) -> AgentConfig:
        """
        Get agent configuration.

        This configuration defines:
        - Agent metadata (ID, name, description)
        - Expected input parameters
        - Expected output parameters
        - Performance estimates (tools count, execution time)
        - Error handling settings (timeout, retry count)

        Returns:
            AgentConfig: Agent configuration object
        """
        return AgentConfig(
            agent_id=cls.agent_role,
            name="Agent Template",
            description="Template agent for demonstration purposes",
            estimated_tools_cnt=5,  # Estimated number of tool calls
            estimated_total_time=60,  # Estimated execution time in seconds
            timeout=300,  # Maximum execution time in seconds
            retry_count=3,  # Number of retries on failure
            input={
                # Define input parameters and their descriptions
                # Example: "file_id": "string - file ID to process",
                # model will inject by orchestrator from orchestrator.agents.context
                "model": "string - LLM model to use (default: openrouter/openai/gpt-4o-mini)",
            },
            output={
                # Define output parameters and their descriptions
                # Example: "result_id": "string - result ID",
            },
        )

    async def execute(self) -> Dict[str, Any]:
        """
        Execute the agent task (ITaskExecutor interface method).

        This method is called by TaskScheduler to run the agent.
        It should:
        1. Create the crew
        2. Execute the crew
        3. Return results in a standardized format

        Returns:
            Dict containing:
                - status: "success" or "error"
                - result: execution results or error information
        """
        try:
            self.logger.info(f"Starting {self.agent_role} execution")
            crew_instance = self.crew()
            result = await crew_instance.kickoff_async()
            self.logger.info(f"{self.agent_role} execution completed")

            return {
                "status": "success",
                "result": {
                    "raw_output": str(result),
                    "agent_role": self.agent_role,
                },
            }
        except Exception as e:
            self.logger.error(f"{self.agent_role} execution failed: {e}")
            return {
                "status": "error",
                "result": {
                    "error": str(e),
                    "agent_role": self.agent_role,
                },
            }

    def worker_agent(self) -> Agent:
        """
        Create a worker agent that performs the main task.

        Define:
        - role: The agent's job title/function
        - goal: What the agent aims to achieve
        - backstory: Agent's expertise and guidelines
        - tools: Available tools for this agent
        """
        tool_list = [
            # Add tools this agent can use
            # Example: DirectoryReadTool,
        ]

        return Agent(
            role="Worker",
            goal="Accomplish the specified task efficiently",
            backstory="""You are a skilled worker agent responsible for [describe responsibilities].

            Your workflow:
            1. [Step 1 description]
            2. [Step 2 description]
            3. [Step 3 description]

            Guidelines:
            - Always verify your work
            - Use appropriate tools for each task
            - Report any issues encountered
            """,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=30,  # Maximum iterations for the agent
            tools=self.adapter.get_tools(tool_list) if self.adapter else [],
        )

    def main_task(self) -> Task:
        """
        Create the main task for the agent to complete.

        Define:
        - description: Detailed task instructions
        - expected_output: What the task should produce
        - tools: Task-specific tools (execution tools like create, update, delete)
        """
        task_tools = [
            # Add task-specific tools here
            # Example: CreateResource, UpdateResource
        ]

        return Task(
            description="""[Detailed task description]

            OBJECTIVE:
            [What needs to be accomplished]

            WORKFLOW:
            1. [Step 1]
            2. [Step 2]
            3. [Step 3]

            QUALITY STANDARDS:
            - [Quality requirement 1]
            - [Quality requirement 2]
            - [Quality requirement 3]

            FINAL DELIVERABLE:
            [What should be produced at the end]
            """,
            tools=self.adapter.get_tools(task_tools) if self.adapter else [],
            expected_output="[Brief description of expected output]",
        )

    def crew(self) -> Crew:
        """
        Create and configure the crew.

        Crew can be:
        - Sequential: Tasks run one after another
        - Hierarchical: Manager delegates to specialized agents
        - Parallel: Tasks run concurrently
        """
        return Crew(
            agents=[
                self.worker_agent(),
                # Add more agents as needed
            ],
            tasks=[
                self.main_task(),
                # Add more tasks as needed
            ],
            process=Process.sequential,  # or Process.hierarchical
            verbose=True,
        )
