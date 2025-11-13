# Quickstart: Paper Analysis Agent

**Last Updated**: 2025-11-05
**Prerequisites**: Python 3.11+, Poetry, Docker (optional)

## Overview

This guide helps you set up, test, and run the Paper Analysis Agent locally. The agent integrates with the existing pdf_parser to provide comprehensive manuscript analysis.

---

## Prerequisites

### Required Services

1. **Data Service** (localhost:8008)
   - Stores manuscripts, structured content, analysis results
   - Required for all database operations

2. **LLM Service** (via OpenRouter or local)
   - Powers AI analysis agents
   - Default: OpenRouter/OpenAI GPT-4o-mini

### Optional Services (for full system test)

3. **Orchestrator** (localhost:8001)
   - Coordinates agent tasks
   - Required for production deployment, optional for local testing

4. **Journal Insight Service** (localhost:8010)
   - Provides journal metadata (used by downstream agents)
   - Not required for Paper Analysis Agent testing

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/OxSci-AI/xsci-manuscript-service-speckit.git
cd oxsci-manuscript-service-speckit
```

### 2. Install Dependencies

```bash
# Authenticate with AWS CodeArtifact (expires after 12 hours)
./entrypoint-dev.sh

# Install dependencies
poetry install --with dev,test

# Activate virtual environment
poetry shell
```

### 3. Environment Configuration

Create `.env` file in project root:

```bash
# Environment
ENV=dev

# LLM Service
LLM_SERVICE_URL=https://llm-service-test.oxsci.ai/api/llm/v1
OPENROUTER_API_KEY=your_openrouter_key_here

# Data Service
DATA_SERVICE_URL=http://localhost:8008/api/database/v1
# Or use cloud test environment:
# DATA_SERVICE_URL=https://data-service-test.oxsci.ai/api/database/v1
# BASIC_AUTH=True
# BASIC_AUTH_USER=oxsci
# BASIC_AUTH_PWD=admin

# Orchestrator (optional for local testing)
ORCHESTRATOR_URL=http://localhost:8001/api/orchestrator/v1

# Service Configuration
SERVICE_NAME=manuscript-service
SERVICE_PORT=8080
```

---

## Running Data Service Locally

### Option 1: Docker Compose

```bash
# In data-service repository
cd ~/git/oxsci-data-service/
docker-compose up -d

# Verify
curl http://localhost:8008/health
```

### Option 2: Direct Python

```bash
# In data-service repository
cd ~/git/oxsci-data-service/
poetry run uvicorn app.core.main:app --port 8008 --host 0.0.0.0 --reload
```

---

## Testing

### Unit Tests (Mock Mode)

Test Paper Analysis Agent without external dependencies:

```bash
# Run all agent tests
pytest tests/agents/test_paper_analysis_agent.py -v

# Run specific test
pytest tests/agents/test_paper_analysis_agent.py::TestPaperAnalysisAgent::test_successful_analysis -v

# With coverage
pytest tests/agents/test_paper_analysis_agent.py --cov=app.agents.paper_analysis_agent --cov-report=term-missing
```

**Expected Output**:
```
tests/agents/test_paper_analysis_agent.py::TestPaperAnalysisAgent::test_successful_analysis PASSED
tests/agents/test_paper_analysis_agent.py::TestPaperAnalysisAgent::test_missing_sections PASSED
tests/agents/test_paper_analysis_agent.py::TestPaperAnalysisAgent::test_no_references PASSED

===== 3 passed in 12.34s =====
```

### Integration Tests (with Data Service)

Test with real data service and sample manuscript:

```bash
# Ensure data service is running
curl http://localhost:8008/health

# Run integration test
pytest tests/agents/test_paper_analysis_agent.py -v -m integration

# Or run standalone test script
python tests/sample/test_paper_analysis_standalone.py
```

**Test Script** (`tests/sample/test_paper_analysis_standalone.py`):
```python
import asyncio
from oxsci_oma_core import OMAContext
from oxsci_oma_core.adapter.crewai_adapter import CrewAIToolAdapter
from app.agents.paper_analysis_agent import PaperAnalysisAgent

async def main():
    # Setup context with real IDs from database
    task_context = {
        "manuscript_id": "9a94c7f4-e4d0-4586-88cb-5412872a7be8",
        "user_id": "2ae0adad-bb76-4a78-a8e8-19db5ebbf4a9",
        "file_id": "14c302e6-9cf9-4cbe-8d11-393ef02ee228",
    }

    context = OMAContext(
        task_id="test-task-123",
        task_context=task_context,
        tool_service_url={
            "DATA_SERVICE": "http://localhost:8008/api/database/v1"
        }
    )

    adapter = CrewAIToolAdapter(context)

    # Execute agent
    agent = PaperAnalysisAgent(context, adapter)
    result = await agent.execute()

    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        paper_analysis_id = result['result']['paper_analysis_result_id']
        print(f"Analysis ID: {paper_analysis_id}")

        # Retrieve analysis from context
        topics = context.get_shared_data("research_topics")
        print(f"Primary discipline: {topics['primary_discipline']}")
        print(f"Keywords: {topics['keywords']}")
    else:
        print(f"Error: {result['result']['error']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Running Locally (Standalone)

### Direct Execution

```bash
# Start the agent service
poetry run uvicorn app.core.main:app --port 8080 --host 0.0.0.0 --reload
```

**Expected Startup Log**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Registering agent: pdf_parser
INFO:     Registering agent: paper_analysis_agent
INFO:     Starting TaskScheduler for pdf_parser (interval: 10s)
INFO:     Starting TaskScheduler for paper_analysis_agent (interval: 10s)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Health Check

```bash
curl http://localhost:8080/health

# Expected response:
{
  "status": "healthy",
  "service": "manuscript-service",
  "agents": ["pdf_parser", "paper_analysis_agent"]
}
```

---

## Running with Orchestrator

### 1. Start Orchestrator

```bash
# In orchestrator repository
cd ~/git/oxsci-orchestrator/
poetry run uvicorn app.core.main:app --port 8001 --host 0.0.0.0 --reload
```

### 2. Start Manuscript Service

```bash
poetry run uvicorn app.core.main:app --port 8080 --host 0.0.0.0 --reload
```

**Registration Log**:
```
INFO:     Registering with orchestrator: http://localhost:8001
INFO:     Agent 'paper_analysis_agent' registered successfully
```

### 3. Create Task via Orchestrator

```bash
# Create analysis task
curl -X POST http://localhost:8001/api/orchestrator/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "paper_analysis_agent",
    "input": {
      "file_id": "14c302e6-9cf9-4cbe-8d11-393ef02ee228",
      "manuscript_id": "9a94c7f4-e4d0-4586-88cb-5412872a7be8",
      "user_id": "2ae0adad-bb76-4a78-a8e8-19db5ebbf4a9"
    }
  }'

# Response:
{
  "task_id": "task-abc123",
  "status": "pending",
  "agent_id": "paper_analysis_agent"
}
```

### 4. Check Task Status

```bash
# Poll task status
curl http://localhost:8001/api/orchestrator/v1/tasks/task-abc123

# Response (in progress):
{
  "task_id": "task-abc123",
  "status": "running",
  "current_stage": "content_analysis",
  "progress": 40
}

# Response (complete):
{
  "task_id": "task-abc123",
  "status": "completed",
  "output": {
    "paper_analysis_result_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

### 5. Retrieve Analysis Results

```bash
# Get analysis from data service
curl http://localhost:8008/api/database/v1/paper_analyses/a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Response:
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "research_topics": {
    "primary_discipline": "Biomedical Engineering",
    "sub_disciplines": ["Medical Imaging", "AI in Healthcare"],
    "keywords": ["Alzheimer's disease", "MRI", "deep learning"]
  },
  "article_classification": {
    "article_type": "original_research",
    "confidence_score": 0.92,
    "target_audience_breadth": "interdisciplinary"
  },
  "key_findings": [
    {
      "finding_text": "Achieved 94% accuracy in early diagnosis",
      "significance": "Outperforms traditional methods",
      "outcome_type": "quantitative"
    }
  ],
  ...
}
```

---

## Debugging

### Enable Verbose Logging

```python
# In app/core/config.py
class Config(BaseConfig):
    LOG_LEVEL: str = "DEBUG"  # Change from INFO
```

Or via environment:
```bash
export LOG_LEVEL=DEBUG
poetry run uvicorn app.core.main:app --port 8080
```

### View Agent Execution Logs

```bash
# Tail service logs
tail -f logs/manuscript-service.log

# Filter for specific agent
tail -f logs/manuscript-service.log | grep "paper_analysis_agent"

# View tool calls
tail -f logs/manuscript-service.log | grep "Tool execution"
```

### Inspect Shared Context

Add debug logging in agent code:

```python
# In app/agents/paper_analysis_agent.py
async def execute(self):
    logger.debug(f"Context data: {self.context.get_all_shared_data()}")

    # After each stage
    logger.debug(f"After content analysis: {self.context.get_shared_data('research_topics')}")
```

### Common Issues

#### 1. "No module named 'oxsci_oma_core'"

**Solution**:
```bash
# Re-authenticate with CodeArtifact
./entrypoint-dev.sh

# Reinstall
poetry lock && poetry install
```

#### 2. "Connection refused to Data Service"

**Solution**:
```bash
# Check if data service is running
curl http://localhost:8008/health

# If not, start it
cd ~/git/oxsci-data-service/
poetry run uvicorn app.core.main:app --port 8008 --reload
```

#### 3. "pdf_parser failed: file_id not found"

**Solution**:
```bash
# Verify file exists in database
curl http://localhost:8008/api/database/v1/files/14c302e6-9cf9-4cbe-8d11-393ef02ee228

# If not, upload test file first
curl -X POST http://localhost:8008/api/database/v1/files \
  -F "file=@tests/sample/sample.pdf" \
  -F "manuscript_id=9a94c7f4-e4d0-4586-88cb-5412872a7be8"
```

#### 4. "OpenRouter API key invalid"

**Solution**:
```bash
# Get API key from https://openrouter.ai/
# Add to .env
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env

# Reload environment
source .env
```

---

## Sample Data

### Test Manuscripts

Located in `tests/sample/`:

1. **sample.pdf** - Standard IMRAD research paper
   - ~10 pages
   - Well-structured sections
   - Complete references

2. **sample-large.pdf** - Longer research paper
   - ~50 pages
   - Multiple subsections
   - Extensive references

### Test IDs (for development)

Use these IDs in local development (ensure corresponding data exists):

```python
TEST_CONTEXT = {
    "manuscript_id": "9a94c7f4-e4d0-4586-88cb-5412872a7be8",
    "user_id": "2ae0adad-bb76-4a78-a8e8-19db5ebbf4a9",
    "file_id": "14c302e6-9cf9-4cbe-8d11-393ef02ee228",
}
```

---

## Performance Benchmarks

Target performance (from spec SC-007):
- **50-page manuscript**: < 5 minutes total
- **10-page manuscript**: < 2 minutes total

**Typical Breakdown**:
- PDF parsing: 30-60s (existing pdf_parser)
- Content analysis: 60s
- Citation analysis: 30s
- Classification: 20s
- Summary generation: 20s
- Database operations: 10s
- **Total: 170-200s (2.8-3.3 minutes)**

Monitor with:
```python
import time
start = time.time()
result = await agent.execute()
elapsed = time.time() - start
logger.info(f"Analysis completed in {elapsed:.2f}s")
```

---

## Next Steps

1. **Run Tests**: `pytest tests/agents/test_paper_analysis_agent.py -v`
2. **Test Locally**: Use standalone test script with sample PDF
3. **Integrate**: Connect with orchestrator for full workflow
4. **Deploy**: Use Docker image for test environment

---

## References

- **Plan**: `specs/002-paper-analysis-agent/plan.md`
- **Data Models**: `specs/002-paper-analysis-agent/data-model.md`
- **Feature Spec**: `specs/002-paper-analysis-agent/spec.md`
- **OMA Docs**: `docs/agent_design/oma_architecture.md`
- **CrewAI Docs**: `docs/agent_design/crewai_framework_development_specification.md`
