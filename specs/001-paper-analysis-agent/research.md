# Research: Paper Analysis Agent

**Phase**: 0 - Research & Technology Selection
**Date**: 2025-11-05
**Status**: Complete

## Overview

This document consolidates research findings for implementing the Paper Analysis Agent, which performs comprehensive manuscript content analysis by integrating the existing pdf_parser and adding intelligent analysis layers.

---

## 1. LLM Selection for Content Analysis

### Decision: OpenRouter/OpenAI GPT-4o-mini

**Rationale**:
- **Cost-effectiveness**: GPT-4o-mini provides strong performance at lower cost compared to full GPT-4o
- **Speed**: Faster response times crucial for 5-minute target completion
- **Proven track record**: Already used successfully in pdf_parser.py with good results
- **Context window**: Sufficient for analyzing manuscript sections (128K tokens)
- **Instruction following**: Excellent at structured output and following complex prompts

**Alternatives Considered**:
1. **GPT-4o (full)** - More capable but 10x cost, unnecessary for text analysis tasks
2. **Claude 3.5 Sonnet** - Strong at analysis but slightly slower, higher cost
3. **Mixtral 8x7B** - Open source alternative but less reliable for structured outputs
4. **GPT-3.5-turbo** - Cheaper but noticeably weaker at nuanced classification tasks

**Configuration**:
```python
llm = adapter.create_llm(
    model="openrouter/openai/gpt-4o-mini",
    temperature=0.3,  # Low for consistent analysis
    timeout=300,
    max_retries=3,
)
```

**Cost Analysis** (per manuscript):
- Estimated tokens per analysis: ~20K tokens (sections + prompts + outputs)
- Cost: $0.02-0.05 per manuscript
- Budget-friendly for production scale

---

## 2. Prompt Engineering Strategy

### Decision: Structured Multi-Stage Analysis with Explicit Instructions

**Rationale**:
- **PDF parser lesson**: pdf_parser succeeds with highly explicit, structured prompts
- **Token efficiency**: Shorter, focused prompts per sub-agent vs one massive prompt
- **Clarity**: Explicit instructions reduce ambiguity and improve output consistency
- **Maintainability**: Modular prompts easier to debug and refine per analysis dimension

**Prompt Structure Template**:
```
Role: [Specific analyst role]
Goal: [Clear, measurable objective]
Backstory: [Concise context + CRITICAL INSTRUCTIONS]

MANDATORY WORKFLOW:
1. [Explicit first action]
2. [Explicit second action]
3. [Explicit output format]

FORBIDDEN BEHAVIORS:
- [Anti-patterns to avoid]
- [Common mistakes]

Expected Output: PURE JSON matching [Schema]
```

**Key Principles** (from pdf_parser success):
1. **Action-oriented**: "Call tool NOW" not "I will call"
2. **Format enforcement**: "PURE JSON ONLY. No explanatory text."
3. **Explicit workflows**: Number each step, no ambiguity
4. **Forbidden list**: Explicitly state what NOT to do
5. **Schema reference**: Always cite expected Pydantic model

**Alternatives Considered**:
1. **Zero-shot prompts** - Too unreliable for structured outputs
2. **Few-shot examples** - Token-heavy, diminishing returns for clear tasks
3. **Chain-of-thought** - Adds latency without clear benefit for classification

---

## 3. Agent Architecture Pattern

### Decision: Sequential 4-Agent Crew

**Architecture**:
```
PaperAnalysisAgent (ITaskExecutor)
  ├── Stage 1: pdf_parser (existing) → structured_content_overview_id
  ├── Stage 2: Content Analyzer Agent → extracts topics, methods, findings
  ├── Stage 3: Citation Analyzer Agent → identifies top journals from references
  ├── Stage 4: Classification Agent → determines article type and audience
  └── Stage 5: Summary Generator Agent → produces human-readable summary
```

**Rationale**:
- **Separation of concerns**: Each agent has single, clear responsibility
- **Parallel-ready**: Stages 2-4 could be parallelized in future if needed
- **Debuggable**: Easy to isolate which analysis stage fails
- **Reusable**: Individual agents can be used independently
- **Token efficient**: Focused prompts per stage vs one giant prompt

**Alternatives Considered**:
1. **Single monolithic agent** - Risk of prompt confusion, harder to debug
2. **Hierarchical with manager** - Unnecessary overhead for sequential workflow
3. **6+ micro-agents** - Over-engineering, diminishing returns

**Process Type**: `Process.sequential`
- Stages must run in order (can't classify before content extraction)
- Clear data flow: each stage enriches shared context
- Memory=False (don't need conversation history between stages)

---

## 4. Data Flow and Context Management

### Decision: OMA Shared Context Pattern with Staged Enrichment

**Data Flow**:
```
Input: file_id
  ↓
pdf_parser.execute()
  ↓
shared_context["structured_content_overview_id"] = "uuid"
  ↓
Content Analyzer reads sections via GetStructuredSections tool
  ↓
shared_context["primary_topics"] = [...]
shared_context["methodologies"] = [...]
shared_context["key_findings"] = [...]
  ↓
Citation Analyzer reads references section
  ↓
shared_context["reference_journals"] = [{"name": "...", "count": N}]
  ↓
Classification Agent reads all context
  ↓
shared_context["article_type"] = "original_research"
shared_context["target_audience"] = {...}
  ↓
Summary Generator reads all context
  ↓
shared_context["analysis_summary"] = "..."
  ↓
CreatePaperAnalysis tool persists all to database
  ↓
Output: paper_analysis_result_id
```

**Key Patterns**:
1. **Progressive enrichment**: Each stage adds to shared_context
2. **Tool-mediated persistence**: Use OMA tools for all reads/writes
3. **Explicit field names**: Clear, consistent naming (primary_topics not topics)
4. **Structured data**: Pydantic models for type safety

**Rationale**:
- **Transparent**: Easy to inspect context at any stage
- **OMA compliant**: Uses get_shared_data/set_shared_data exclusively
- **Traceable**: Tool execution tracking shows data flow
- **Recoverable**: Can resume from any stage on failure

---

## 5. Custom Tools Requirements

### Decision: Minimal Custom Tools, Maximize OMA Standard Tools

**Required Custom Tools**:

1. **GetStructuredSections** (if not in OMA standard)
   - Input: structured_content_overview_id, section_types (list)
   - Output: List of section content by type
   - Rationale: Need to retrieve parsed sections from pdf_parser output

2. **CreatePaperAnalysis** (if not in OMA standard)
   - Input: All analysis fields (topics, type, methods, etc.)
   - Output: paper_analysis_result_id
   - Rationale: Persist comprehensive analysis to database

**Standard OMA Tools to Use**:
- `GetPDFVersion` - Already used by pdf_parser
- `CreateStructuredOverview` - Already used by pdf_parser
- `CreateStructuredSection` - Already used by pdf_parser
- `CompleteStructuredOverview` - Already used by pdf_parser

**Registration Pattern** (from development guide):
```python
from oxsci_oma_core.tools.registry import tool_registry

# In agent __init__
tool_registry.register_custom_tool(GetStructuredSections)
tool_registry.register_custom_tool(CreatePaperAnalysis)
```

**Rationale**:
- **Minimize custom code**: Leverage OMA ecosystem
- **Maintain standards**: Follow tool inheritance patterns
- **Enable tracking**: All tool calls auto-logged

---

## 6. Error Handling Strategy

### Decision: Fail-Fast with Explicit Validation at Stage Boundaries

**Pattern**:
```python
# After each stage
result = await stage_crew.kickoff_async()
if not self._validate_stage_output(result, expected_fields):
    raise ValueError(f"Stage {N} failed: missing {expected_fields}")

# In execute() method
try:
    # Stage 1: pdf_parser
    overview_id = await self._execute_pdf_parser()
    if not overview_id:
        raise ValueError("pdf_parser failed to produce overview_id")

    # Stage 2-5: Analysis stages
    await self._execute_analysis_stages(overview_id)

    return {"status": "success", "result": {...}}
except Exception as e:
    logger.error(f"Analysis failed: {e}", exc_info=True)
    return {"status": "error", "result": str(e)}
```

**Rationale** (from Constitution Principle II):
- **No fallbacks**: If pdf_parser fails, entire agent fails (no fake data)
- **No retries**: Fail immediately, let orchestrator decide retry policy
- **Explicit errors**: Clear messages about what failed and why
- **No degradation**: Either complete analysis or error, no partial results

**Validation Checkpoints**:
1. After pdf_parser: verify structured_content_overview_id exists
2. After content analysis: verify primary_topics, methodologies, key_findings
3. After citation analysis: verify reference_journals (can be empty if no refs)
4. After classification: verify article_type and target_audience
5. Before persistence: verify all required fields populated

---

## 7. Testing Strategy

### Decision: OMAAgentTest-Based Mock Mode Testing

**Test Structure**:
```python
# tests/agents/test_paper_analysis_agent.py
from oxsci_oma_core.test_module.oma_agent_test import OMAAgentTest
from app.agents.paper_analysis_agent import PaperAnalysisAgent

class TestPaperAnalysisAgent(OMAAgentTest):
    executor_class = PaperAnalysisAgent

    def get_task_input(self) -> dict:
        return {
            "manuscript_id": "test-manuscript-123",
            "user_id": "test-user-456",
            "file_id": "test-file-789",
        }

    def get_expected_output_keys(self) -> list:
        return ["paper_analysis_result_id"]

    async def test_successful_analysis(self):
        result = await self.run_test()
        assert result["status"] == "success"

        output = self.task.get_output()
        assert "paper_analysis_result_id" in output

        # Validate structured data in context
        topics = self.context.get_shared_data("primary_topics")
        assert len(topics) > 0

        article_type = self.context.get_shared_data("article_type")
        assert article_type in ["original_research", "review", "case_report", "methods", "other"]
```

**Rationale**:
- **Mock mode**: Tests without external services (pdf_parser, data service)
- **Comprehensive**: Validates both output and intermediate context
- **Fast**: No real LLM calls or API dependencies
- **Repeatable**: Same inputs always produce same results

**Test Coverage**:
1. **Happy path**: Standard IMRAD manuscript → complete analysis
2. **Missing sections**: Manuscript without methods → partial analysis
3. **No references**: Manuscript without bibliography → empty citation list
4. **Edge cases**: Very short/long manuscripts, non-English, ambiguous type

---

## 8. Performance Optimization

### Decision: Batch Context Loading + Async Execution

**Optimizations**:

1. **Load sections once**: Retrieve all sections in single tool call, cache in memory
   ```python
   sections = await get_sections_tool.execute(
       overview_id=overview_id,
       section_types=["all"]  # Batch load
   )
   self._sections_cache = sections  # Cache for all agents
   ```

2. **Async crew kickoff**: Non-blocking execution
   ```python
   await crew.kickoff_async(inputs={})
   ```

3. **Minimal memory**: `memory=False` in Crew (don't need history)

4. **Focused prompts**: Only pass relevant section content to each agent
   - Content Analyzer: abstract, intro, methods, results, discussion
   - Citation Analyzer: references only
   - Classification Agent: abstract + conclusion (not full text)

5. **Temperature tuning**: `0.3` for consistent outputs without over-sampling

**Expected Performance**:
- PDF parsing (existing): ~30-60 seconds for 50 pages
- Content analysis: ~60 seconds (4 sections x 15s each)
- Citation analysis: ~30 seconds (single references section)
- Classification: ~20 seconds (abstract + conclusion only)
- Summary generation: ~20 seconds
- Database writes: ~10 seconds
- **Total: ~3-4 minutes** (well under 5-minute target)

---

## 9. Configuration Management

### Decision: YAML-based Agent/Task Configuration (CrewAI + OMA pattern)

**Files**:
```
app/config/
├── agents.yaml (agent role definitions)
└── tasks.yaml (task descriptions and outputs)
```

**Pattern** (from pdf_parser):
```python
from crewai.project import CrewBase
from pathlib import Path

@CrewBase
class PaperAnalysisAgent:
    _current_dir = Path(__file__).parent
    agents_config = str(_current_dir.parent / 'config/agents.yaml')
    tasks_config = str(_current_dir.parent / 'config/tasks.yaml')
```

**Benefits**:
- **Separation of concerns**: Prompts in YAML, logic in Python
- **Easy tuning**: Modify agent behaviors without code changes
- **Version control**: Track prompt evolution over time
- **Team collaboration**: Non-developers can refine prompts

**Alternative Considered**:
- **Inline prompts**: Harder to maintain, couples prompt to code
- **Rejected**: Violates separation of concerns

---

## 10. Integration Points

### Decision: Orchestrator-Managed Workflow

**Registration**:
```python
# app/core/main.py
from app.agents.paper_analysis_agent import PaperAnalysisAgent

agent_executors = [
    PdfParser,            # Existing
    PaperAnalysisAgent,   # NEW
    # Future agents...
]

for executor_class in agent_executors:
    agent_config = executor_class.get_agent_config()
    await registration.register_agent(agent_config)

    scheduler = TaskScheduler(
        executor_class=executor_class,
        adapter_class=CrewAIToolAdapter,
        interval=10
    )
    await scheduler.start()
```

**Agent Config**:
```python
@classmethod
def get_agent_config(cls) -> AgentConfig:
    return AgentConfig(
        agent_id="paper_analysis_agent",
        name="Paper Analysis Agent",
        description="Comprehensive manuscript content analysis with topic extraction, citation analysis, and article classification",
        timeout=600,  # 10 minutes max
        retry_count=3,
        input={"file_id": "string"},
        output={"paper_analysis_result_id": "string"},
        estimated_tools_cnt=8,  # pdf_parser tools + analysis tools
        estimated_total_time=300  # 5 minutes target
    )
```

**Workflow**:
1. Orchestrator creates task with file_id
2. TaskScheduler polls and picks up task
3. PaperAnalysisAgent.execute() runs
4. Results synced back to orchestrator
5. Downstream agents (Journal Research) pick up paper_analysis_result_id

---

## Summary of Decisions

| Decision Point | Choice | Key Reason |
|----------------|--------|------------|
| LLM Model | GPT-4o-mini | Cost-effective, proven in pdf_parser |
| Prompt Strategy | Explicit structured | Consistency, pdf_parser success pattern |
| Agent Architecture | Sequential 4-agent | Clear separation, debuggable |
| Data Flow | OMA shared context | Compliant, traceable, recoverable |
| Custom Tools | Minimal (2 tools) | Maximize standard OMA tools |
| Error Handling | Fail-fast | Constitution compliance, no fallbacks |
| Testing | OMAAgentTest mock mode | Fast, repeatable, comprehensive |
| Performance | Batch loading + async | Target: 3-4 min (< 5 min goal) |
| Configuration | YAML-based | Separation of concerns, maintainability |
| Integration | Orchestrator-managed | Standard OMA pattern, scalable |

---

## Open Questions & Future Enhancements

### Resolved
- ✅ LLM selection: GPT-4o-mini
- ✅ Agent count: 4 sub-agents
- ✅ Error strategy: Fail-fast per constitution
- ✅ Integration pattern: Standard OMA/orchestrator

### Future Enhancements (out of scope)
- **Parallel execution**: Stages 2-4 could run concurrently with task dependencies
- **Multi-language support**: Currently English-only per assumptions
- **Custom embedding models**: For semantic similarity in classification
- **Confidence scoring**: ML-based confidence estimation for classifications
- **Active learning**: Feedback loop to improve classification accuracy

---

## References

1. **OMA Architecture**: `docs/agent_design/oma_architecture.md`
2. **CrewAI Spec**: `docs/agent_design/crewai_framework_development_specification.md`
3. **PDF Parser Implementation**: `app/agents/pdf_parser.py`
4. **Development Guide**: `docs/agent_design/crew_agent_develop_guide.md`
5. **Constitution**: `.specify/memory/constitution.md`
6. **Feature Spec**: `specs/002-paper-analysis-agent/spec.md`
