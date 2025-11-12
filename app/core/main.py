from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import config
from oxsci_shared_core.logging import logger
from oxsci_shared_core.error_handler import ExceptionHandlerMiddleware
from oxsci_shared_core import default_router

# Import OMA-Core components
from oxsci_oma_core.schedule.task_scheduler import TaskScheduler
from oxsci_oma_core.adapter.crew_ai import CrewAIToolAdapter

# Import agent executors
# TODO: Add your agent imports here
# Example: from app.agents.my_agent import MyAgent

# Global scheduler list
schedulers: List[TaskScheduler] = []


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle management.

    This function handles startup and shutdown events for the FastAPI application.
    During startup, it creates and starts TaskSchedulers for all registered agents.
    During shutdown, it stops all schedulers gracefully.
    """
    logger.info(f"Starting {config.SERVICE_NAME} ({config.SERVICE_VERSION})...")

    # Create TaskSchedulers for all agent executors
    # TODO: Add your agent executor classes here
    agent_executors = [
        # Example: MyAgent,
    ]

    for executor_class in agent_executors:
        try:
            # Create TaskScheduler (automatically retrieves agent_config)
            scheduler = TaskScheduler(
                executor_class=executor_class,  # type: ignore
                adapter_class=CrewAIToolAdapter,
            )

            await scheduler.start()
            schedulers.append(scheduler)

            logger.info(
                f"✅ TaskScheduler started for agent: {scheduler.agent_config.agent_id}"
            )

        except Exception as e:
            logger.error(
                f"Failed to start scheduler for executor {executor_class.__name__}: {e}"
            )

    logger.info(f"🚀 {config.SERVICE_NAME} started with {len(schedulers)} agents")

    yield

    # Shutdown phase
    logger.info(f"Shutting down {config.SERVICE_NAME}...")

    # Stop all schedulers
    for scheduler in schedulers:
        try:
            await scheduler.stop()
            logger.info(
                f"✅ Scheduler stopped for agent: {scheduler.agent_config.agent_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to stop scheduler: {e}")

    logger.info(f"👋 {config.SERVICE_NAME} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=config.SERVICE_NAME,
    version=config.SERVICE_VERSION,
    lifespan=lifespan,
)

# Add exception handler middleware
app.add_middleware(ExceptionHandlerMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include default routes (health, version, etc.)
app.include_router(default_router)
