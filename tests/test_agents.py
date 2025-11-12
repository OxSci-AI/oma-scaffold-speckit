#!/usr/bin/env python3
"""
Test file for OMA Agents

This file uses the decorator-based testing approach from oxsci-oma-core.
See oxsci-oma-core test_module documentation for more details.

Usage:
    # Run specific test
    python tests/test_agents.py --test my_agent

    # Run integration test
    python tests/test_agents.py --integration full_pipeline

    # Run all tests
    python tests/test_agents.py --all

    # Enable verbose logging
    python tests/test_agents.py --test my_agent -v
"""

import sys
from pathlib import Path

from oxsci_oma_core.test_module import agent_test, integration_test, run_tests_from_cli

# Import your agent classes here
# Example:
# from app.agents.my_agent import MyAgent


# ============================================================================
# Single Agent Tests
# ============================================================================


# Example single agent test with PDF sample
# @agent_test(sample_pdf="sample/sample.pdf")
# def test_my_agent():
#     """Test MyAgent - processes PDF documents"""
#     return MyAgent


# Example agent test with custom input
# @agent_test(
#     task_input={
#         "param1": "value1",
#         "param2": "value2",
#     },
# )
# def test_my_agent_with_input():
#     """Test MyAgent with custom input parameters"""
#     return MyAgent


# ============================================================================
# Integration Tests
# ============================================================================


# Example integration test with multiple agents
# @integration_test(
#     crews=[
#         FirstAgent,
#         SecondAgent,
#         ThirdAgent,
#     ],
#     sample_pdf="sample/sample.pdf",
# )
# def test_full_pipeline():
#     """Test full processing pipeline
#
#     Tests:
#     - Step 1: FirstAgent processes PDF
#     - Step 2: SecondAgent analyzes content
#     - Step 3: ThirdAgent generates report
#
#     Data flows automatically between agents via shared context
#     """
#     pass


# ============================================================================
# CLI Entry Point
# ============================================================================


def main():
    """CLI entry point for running tests"""
    # Define test map
    test_map = {
        # Add your test functions here
        # Example:
        # "my_agent": test_my_agent,
        # "my_agent_with_input": test_my_agent_with_input,
    }

    integration_tests = {
        # Add your integration test functions here
        # Example:
        # "full_pipeline": test_full_pipeline,
    }

    # Run tests from CLI
    sys.exit(run_tests_from_cli(test_map, integration_tests))


if __name__ == "__main__":
    main()
