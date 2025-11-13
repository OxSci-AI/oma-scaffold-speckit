# Implementation Plan: Paper Analysis Agent

**Feature ID**: 002-paper-analysis-agent
**Created**: 2025-11-05
**Status**: Planning Phase
**Related Spec**: [spec.md](./spec.md)

---

## Summary

### Primary Requirement
Develop a Paper Analysis Agent that integrates with the existing `pdf_parser` agent to perform comprehensive manuscript content analysis. The agent extracts structured information including research domain, methodology, key findings, article type, target audience, and citation patterns from academic manuscripts.

### Technical Approach
Multi-agent CrewAI crew implementing the ITaskExecutor interface from OMA framework. The agent orchestrates a sequential workflow:

1. **Input Stage**: Receives `file_id` and manuscript metadata from orchestrator
2. **PDF Processing**: Calls `pdf_parser` agent (existing) to extract structured sections
3. **Content Analysis**: Analyzes extracted sections using specialized sub-agents to identify topics, methodologies, findings
4. **Citation Analysis**: Extracts and counts journal citations from references section
5. **Classification**: Determines article type and target audience based on content structure
6. **Output Stage**: Persists comprehensive analysis results via OMA write tools, returns `paper_analysis_result_id`

**Integration Point**: Consumes `structured_content_overview_id` from `pdf_parser` output, produces `paper_analysis_result_id` for downstream Journal Research Agent.

**Technology Stack**: Python 3.11, CrewAI for agent orchestration, OMA-core 0.3.3 for framework compliance, shared-core 0.5.0 for service integration.

---

## Technical Context

### Language and Framework
- **Language**: Python 3.11 (from pyproject.toml, line 7: `requires-python = ">=3.11,<3.14.0"`)
- **Agent Framework**: CrewAI with @CrewBase decorator pattern
- **OMA Framework**: oxsci-oma-core >= 0.3.3 (with crewai extras)
- **Service Integration**: oxsci-shared-core >= 0.5.0 for BaseConfig and ServiceClient

### Primary Dependencies
From pyproject.toml and framework specifications:
- **CrewAI**: Multi-agent orchestration with sequential process
- **OMA-core 0.3.3**:
  - ITaskExecutor interface for agent implementation
  - BaseAPITool/BaseReadTool/BaseWriteTool for tool development
  - OMAContext for context management
  - TaskScheduler for task polling
- **Shared-core 0.5.0**:
  - BaseConfig for configuration management
  - ServiceClient for inter-service communication
  - Standard response decorators (@standard_response)
- **Pydantic**: For structured output models and validation
- **FastAPI**: Service framework (standard port 8080)

### Storage
- **Development**: Data Service API at localhost:8008/api/database/v1
- **Test Environment**: https://data-service-test.oxsci.ai/api/database/v1 (with Basic Auth: oxsci/admin)
- **Production**: Cloud deployment via oxsci-deploy variable injection
- **Data Models**: Pydantic models in app/utility/data_models.py
- **Persistence**: OMA write tools (CreatePaperAnalysis, CompletePaperAnalysis)

### Testing
- **Framework**: pytest with asyncio support
- **Base Class**: OMAAgentTest from oxsci_oma_core.test_module
- **Mock Services**:
  - MockTaskService for task context
  - MockServiceClientForTool for API calls
- **Test Location**: tests/agents/test_paper_analysis_agent.py
- **Test Data**: tests/sample/ directory (existing sample.pdf and sample_parsed.json)
- **Coverage**: Unit tests for tools, integration tests for full agent workflow

### Target Platform
- **Deployment**: Linux server (containerized via Docker)
- **Container**: Python 3.11-slim base image
- **Orchestration**: ECS deployment with health checks
- **Service Registration**: Automatic registration with Orchestrator at startup
- **Health Endpoint**: /health (no API prefix)
- **Standard Port**: 8080

### Project Type
**Single-project agent service** following OMA architecture:
- One agent crew per file in app/agents/
- Tools in app/tools/ (if custom tools needed)
- Configuration in app/config/ (agents.yaml, tasks.yaml)
- Service-level main.py for agent registration
- Independent deployment unit

### Performance Goals
Based on spec Success Criteria (SC-007):
- **Target**: Complete analysis within 5 minutes for manuscripts up to 50 pages
- **Breakdown**:
  - PDF parsing: ~1-2 minutes (handled by pdf_parser)
  - Content analysis: ~2-3 minutes (3-4 sub-agents processing sections)
  - Citation extraction: ~30 seconds (reference section parsing)
  - Classification: ~30 seconds (LLM-based type determination)
- **Optimization**: Async task execution where possible, context window management
- **Rate Limiting**: max_rpm configuration to avoid API throttling
- **Caching**: Enable LLM response caching for repeated patterns

### Constraints

#### Integration Constraints
- **MUST** consume `structured_content_overview_id` from pdf_parser output
- **MUST** read section content via OMA read tools (GetStructuredSection)
- **CANNOT** directly parse PDF files (must rely on pdf_parser preprocessing)
- **MUST** use context-only communication (no direct agent-to-agent calls)

#### Data Constraints
- Manuscript language: Primarily English (per assumptions in spec)
- Section structure: IMRAD expected but must handle non-standard structures (FR-030)
- References format: Must handle incomplete/improper formatting (FR-017)
- Output fields: All required fields must be populated (FR-025)

#### OMA Framework Constraints
- **NO** global state or singletons (except tool_registry)
- **NO** direct context structure access (use get_shared_data/set_shared_data)
- **NO** manual tool execution tracking (automatic via framework)
- **NO** retry/fallback mechanisms (fail fast principle)
- **NO** default values masking missing data

#### Performance Constraints
- Max execution time: 600 seconds (10 minutes) per agent config
- Token management: Simplified backstories, focused task descriptions
- Context window: respect_context_window=True for large manuscripts
- LLM model: gpt-4o-mini or similar (balance speed vs. accuracy)

### Scale and Scope

#### Agent Architecture
**Single agent crew** with 3-4 specialized sub-agents:
1. **Content Analyzer Agent**: Extracts topics, keywords, discipline from title/abstract/introduction
2. **Methodology Extractor Agent**: Identifies research methods, experimental designs from methods section
3. **Findings Analyzer Agent**: Extracts key findings from results/discussion/conclusion
4. **Citation Processor Agent**: Parses references, counts journal citations

#### Processing Model
- **Sequential Process**: Each sub-agent processes relevant sections in order
- **One Manuscript at a Time**: Orchestrator manages job queue, agent processes single task
- **Section-Based Input**: Receives pre-parsed sections from pdf_parser (not raw PDF)
- **Structured Output**: Single PaperAnalysisResult object per manuscript

#### Expected Load
- Input: ~10-50 pages per manuscript (typical academic paper)
- Sections: ~5-10 major sections per manuscript
- References: ~20-50 citations typical, up to 100+ for review papers
- Output size: ~2-5KB structured JSON per analysis

#### Scalability Considerations
- Horizontal scaling: Multiple agent service instances for concurrent jobs
- Stateless design: No shared state between executions
- Database writes: Batched section analysis, single finalization call
- Memory footprint: Context cleared between tasks

---

## Constitution Check

### Evaluation Against Core Principles

#### I. OMA Framework Compliance (NON-NEGOTIABLE) ✅ PASS

**Assessment**: The Paper Analysis Agent design fully complies with OMA framework requirements.

**Evidence**:
- **ITaskExecutor Implementation**: Agent will implement all required methods:
  - `agent_role = "paper_analysis_agent_v1"` - unique identifier
  - `__init__(self, context: OMAContext, adapter: IAdapter)` - dependency injection
  - `get_agent_config() -> AgentConfig` - metadata definition
  - `async def execute() -> Dict[str, Any]` - workflow execution
- **Tool Inheritance**: All tools inherit from BaseAPITool/BaseReadTool/BaseWriteTool
  - ReadStructuredSection (BaseReadTool) - reads sections from database
  - CreatePaperAnalysis (BaseWriteTool) - creates analysis record
  - CompletePaperAnalysis (BaseWriteTool) - marks analysis complete
- **Context Management**: Exclusive use of get_shared_data/set_shared_data
  - Read: `structured_content_overview_id = context.get_shared_data("structured_content_overview_id")`
  - Write: `context.set_shared_data("paper_analysis_result_id", analysis_id)`
  - NO direct access to `context.task.context["oma_context"]["shared_context"]`
- **Automatic Tracking**: Zero manual tool execution tracking
  - Framework auto-logs all tool calls via OMABaseTool.execute() wrapper
  - Agents receive tool results via CrewAI observation mechanism
- **Dependency Injection**: Context and adapter provided by TaskScheduler, never created internally

**No Violations Detected**

---

#### II. Fail Fast - No Fallbacks (NON-NEGOTIABLE) ✅ PASS

**Assessment**: Design adheres to fail-fast principle with explicit error reporting.

**Evidence**:
- **Error Propagation**: Tools return explicit error status on failures
  ```python
  if not structured_content_id:
      return ToolResult(status="error", message="Missing structured_content_overview_id", output=None)
  ```
- **No Silent Failures**: All edge cases raise exceptions or return error ToolResult
  - Missing sections (FR-031): Return error message identifying missing section
  - Parse failures: Propagate exception to orchestrator
  - Classification uncertainty: Return low confidence score, not fallback value
- **No Retry Logic**: Retries handled by orchestrator config only (agent_config.retry_count)
- **No Simulation**: No mock data in production paths
- **PEP 8 Compliance**: Code follows Python style guide (black formatter, line length 88)

**No Violations Detected**

---

#### III. Oxsci Development Standards Compliance ✅ PASS

**Assessment**: Development will conform to all Oxsci standards from CLAUDE.md.

**Evidence**:
- **Language**: All code comments, git commits, user-facing text in English
- **PEP 8**: Enforced via black and isort (pyproject.toml lines 58-65)
- **Configuration**: All environment variables via BaseConfig inheritance
  ```python
  from oxsci_shared_core.config import BaseConfig
  class Config(BaseConfig):
      # Inherits DATA_SERVICE_URL, LLM_SERVICE_URL, etc.
      pass
  ```
  - NO use of `os.getenv()`
- **API Standards**:
  - @standard_response() decorator for all endpoints (if API routes needed)
  - SuccessResponse[DataModel] type definitions
  - model_validate() for data safety
- **Service Communication**: Exclusive use of ServiceClient.call_service
  ```python
  from oxsci_shared_core.auth_service import ServiceClient
  service_client = ServiceClient(config.SERVICE_NAME)
  data = await service_client.call_service(
      target_service_url=config.DATA_SERVICE_URL,
      method="GET",
      endpoint=f"/analysis/{analysis_id}"
  )
  ```

**No Violations Detected**

---

#### IV. Multi-Agent System Architecture ✅ PASS

**Assessment**: Agent correctly integrates with distributed multi-agent ecosystem.

**Evidence**:
- **Cloud Service Dependencies**: All URLs from config (test environment default)
  - LLM_SERVICE_URL: https://llm-service-test.oxsci.ai/
  - DATA_SERVICE_URL: https://data-service-test.oxsci.ai/
  - ORCHESTRATOR_URL: https://orchestrator-test.oxsci.ai/
- **Standard Port**: 8080 (agent service standard)
- **Task Polling**: TaskScheduler with configurable interval (10 seconds default)
- **Agent Registration**: ServiceRegistration at startup
  ```python
  registration = ServiceRegistration()
  agent_config = PaperAnalysisAgent.get_agent_config()
  await registration.register_agent(agent_config)
  ```
- **Health Endpoint**: /health without API prefix
- **Template Structure**: Follows oma-core app structure
  - app/agents/paper_analysis_agent.py
  - app/config/agents.yaml, tasks.yaml
  - app/core/main.py for registration

**No Violations Detected**

---

#### V. Test-Driven Development for Agents ✅ PASS

**Assessment**: Testing strategy follows OMA test-first methodology.

**Evidence**:
- **Test Framework**: OMAAgentTest base class from oma-core
  ```python
  from oxsci_oma_core.test_module.oma_agent_test import OMAAgentTest

  class TestPaperAnalysisAgent(OMAAgentTest):
      executor_class = PaperAnalysisAgent

      def get_task_input(self) -> dict:
          return {"manuscript_id": "test-123", "user_id": "user-456", "file_id": "file-789"}

      def get_expected_output_keys(self) -> list:
          return ["paper_analysis_result_id"]
  ```
- **Mock Services**: MockTaskService and MockServiceClientForTool
- **Unit Tests**: Tools tested in isolation
  ```python
  from oxsci_oma_core.test_module.mock_task_service import MockTaskService
  from oxsci_oma_core.test_module.mock_service_client_for_tool import MockServiceClientForTool
  ```
- **Test Data**: Existing tests/sample/sample_parsed.json from pdf_parser
- **Test-First**: Tests written before implementation (enforced in workflow)

**No Violations Detected**

---

#### VI. Configuration Management ✅ PASS

**Assessment**: Configuration follows centralized patterns.

**Evidence**:
- **Config Class**: Inherits BaseConfig
  ```python
  class Config(BaseConfig):
      SERVICE_PORT: int = 8080
      API_V1_PREFIX: str = "/api/manuscript/v1"
  ```
- **No New Variables**: Minimal additions, most inherited from shared-core
- **Deployment**: oxsci-deploy handles variable injection for test/prod
- **Local Dev**: .env file for development overrides
- **Private Packages**: Poetry with AWS CodeArtifact
  - oxsci-shared-core >= 0.5.0 (source: oxsci-ca)
  - oxsci-oma-core >= 0.3.3 (source: oxsci-ca)
  - ./entrypoint-dev.sh for 12-hour token

**No Violations Detected**

---

#### VII. Project Structure and Code Organization (NON-NEGOTIABLE) ✅ PASS

**Assessment**: File structure adheres to standardized layout.

**Evidence**:
- **Agent Location**: app/agents/paper_analysis_agent.py (one agent per file)
- **Tool Location**: app/tools/ (if custom tools needed, grouped by domain)
- **Configuration**: app/config/agents.yaml, app/config/tasks.yaml
- **Registration**: app/core/main.py (service startup, agent registration)
- **Tests**: tests/agents/test_paper_analysis_agent.py (mirrors app structure)
- **Naming Conventions**:
  - Agent file: paper_analysis_agent.py (follows {purpose}_agent.py pattern)
  - Test file: test_paper_analysis_agent.py (follows test_{module}.py pattern)
  - Tool files: manuscript_analysis_tools.py (if custom tools created)

**No Violations Detected**

---

#### VIII. High Cohesion, Low Coupling ✅ PASS

**Assessment**: Design maximizes cohesion and minimizes coupling.

**Evidence**:
- **High Cohesion**:
  - One agent file (paper_analysis_agent.py) with single responsibility: manuscript content analysis
  - Related functionality grouped: all content/citation/classification analysis in same crew
  - Sub-agents logically related: content analyzer, methodology extractor, findings analyzer, citation processor
- **Low Coupling**:
  - Context-only communication: Reads `structured_content_overview_id` from shared_context
  - No direct agent references: pdf_parser output consumed via context, not direct call
  - Dependency injection: ServiceClient injected via context, not imported directly
  - Configuration via injected config: No direct imports of config module in agent code
  - No circular dependencies: Linear flow (orchestrator → paper_analysis → journal_research)
- **Anti-patterns Avoided**:
  - ✅ NO multiple unrelated agents in one file
  - ✅ NO scattered tools without domain grouping
  - ✅ NO agents calling other agents directly
  - ✅ NO hard-coded service URLs (all via config)
  - ✅ NO shared mutable state

**No Violations Detected**

---

### Constitution Compliance Summary

**Overall Assessment**: ✅ **FULLY COMPLIANT**

All 8 core principles satisfied:
1. ✅ OMA Framework Compliance - ITaskExecutor, tool patterns, context management
2. ✅ Fail Fast - Error propagation, no fallbacks, PEP 8
3. ✅ Oxsci Standards - English, BaseConfig, ServiceClient, @standard_response
4. ✅ Multi-Agent Architecture - Cloud services, task polling, registration
5. ✅ Test-Driven Development - OMAAgentTest, mock mode, test-first
6. ✅ Configuration Management - BaseConfig inheritance, minimal new vars
7. ✅ Project Structure - Standardized file layout, naming conventions
8. ✅ High Cohesion, Low Coupling - Single responsibility, context communication

**No constitution violations identified. Proceed with implementation.**

---

## Project Structure

### Directory Layout

Based on actual project paths from spec and constitution:

```
D:\Project\oxsci-manuscript-service-speckit\
├── specs/
│   └── 002-paper-analysis-agent/
│       ├── spec.md                          (Feature specification - existing)
│       ├── plan.md                          (This file - implementation plan)
│       ├── research.md                      (Phase 0 - research findings)
│       ├── data-model.md                    (Phase 1 - entity schemas)
│       ├── quickstart.md                    (Phase 1 - setup/run guide)
│       └── contracts/                       (Phase 1 - API contracts if needed)
│
├── app/
│   ├── agents/
│   │   ├── pdf_parser.py                   (Existing - prerequisite)
│   │   └── paper_analysis_agent.py         (NEW - main implementation)
│   │
│   ├── tools/                              (Custom tools if needed)
│   │   └── manuscript_analysis_tools.py    (NEW - if custom tools required)
│   │
│   ├── config/
│   │   ├── agents.yaml                     (Agent configurations)
│   │   └── tasks.yaml                      (Task configurations)
│   │
│   ├── utility/
│   │   └── data_models.py                  (Pydantic models for outputs)
│   │
│   └── core/
│       ├── config.py                       (Service config)
│       └── main.py                         (FastAPI app, agent registration)
│
├── tests/
│   ├── agents/
│   │   └── test_paper_analysis_agent.py   (NEW - OMAAgentTest-based tests)
│   │
│   ├── tools/
│   │   └── test_manuscript_analysis_tools.py (NEW - if custom tools)
│   │
│   └── sample/                             (Test data)
│       ├── sample.pdf
│       ├── sample_parsed.json
│       ├── sample-large.pdf
│       └── sample-large_parsed.json
│
├── pyproject.toml
├── CLAUDE.md
├── .gitignore
└── README.md
```

---

## Complexity Tracking

### Constitution Violations and Deviations

**Status**: ✅ **NONE DETECTED**

This section tracks any violations of the constitution principles during implementation. All design decisions have been evaluated against the 8 core principles.

**Expected State**: EMPTY throughout implementation.

**Current Violations**: None

---

## Implementation Phases

### Phase 0: Research and Prompt Engineering (2-3 days)

**Objective**: Investigate optimal approaches for content analysis, citation extraction, and classification using LLMs.

#### Deliverables
- `specs/002-paper-analysis-agent/research.md` - Research findings with LLM benchmarks, prompt templates, edge case strategies

---

### Phase 1: Data Models and API Contracts (1-2 days)

**Objective**: Define all Pydantic models for structured outputs.

#### Deliverables
- `specs/002-paper-analysis-agent/data-model.md` - Complete model documentation
- `specs/002-paper-analysis-agent/quickstart.md` - Setup and run guide
- `app/utility/data_models.py` - Pydantic model implementations

---

### Phase 2: Agent Configuration (1 day)

**Objective**: Define agent backstories, roles, goals in YAML.

#### Deliverables
- `app/config/agents.yaml` - 4 sub-agent definitions
- `app/config/tasks.yaml` - 6 task definitions with dependencies

---

### Phase 3: Agent Implementation (3-4 days)

**Objective**: Implement PaperAnalysisAgent crew with ITaskExecutor interface.

#### Deliverables
- `app/agents/paper_analysis_agent.py` - Main agent implementation
- `app/tools/manuscript_analysis_tools.py` - Custom tools (if needed)

---

### Phase 4: Testing Implementation (2-3 days)

**Objective**: Write comprehensive tests using OMAAgentTest framework.

#### Deliverables
- `tests/agents/test_paper_analysis_agent.py` - OMAAgentTest-based tests
- `tests/tools/test_manuscript_analysis_tools.py` - Tool unit tests (if custom tools)

---

### Phase 5: Integration and Registration (1 day)

**Objective**: Integrate with service startup, register with orchestrator.

#### Deliverables
- Updated `app/core/main.py` - Agent registration
- Verified `app/core/config.py` - Configuration
- Validated quickstart.md with local testing

---

### Phase 6: Documentation and Handoff (1 day)

**Objective**: Complete documentation, prepare for deployment.

#### Deliverables
- All spec docs complete
- Updated README.md
- Dockerfile validated
- Deployment checklist

---

## Success Metrics

### Functional Metrics (from spec)

1. **SC-001**: Structured output with all required dimensions ✅
2. **SC-002**: 95% completeness for IMRAD manuscripts ✅
3. **SC-003**: 90% article type classification accuracy ✅
4. **SC-004**: 95% citation extraction success ✅
5. **SC-007**: < 5 minutes for 50-page manuscripts ✅
6. **SC-008**: 100% pdf_parser integration success ✅
7. **SC-009**: 100% persistence success ✅
8. **SC-010**: Downstream agent consumption ✅

### Technical Metrics

1. **Test Coverage**: ≥ 80% code coverage
2. **Constitution Compliance**: Zero violations
3. **Performance**: < 5 minutes mean execution time
4. **Reliability**: < 5% error rate

---

## Acceptance Criteria

### Overall Feature Acceptance

**Definition of Done**:
1. All phases completed with gates satisfied
2. All Success Criteria (SC-001 to SC-010) validated
3. Zero constitution violations
4. Code merged to main branch
5. Agent deployed to test environment
6. End-to-end workflow validated
7. Performance targets met
8. Documentation complete

---

**END OF IMPLEMENTATION PLAN**
