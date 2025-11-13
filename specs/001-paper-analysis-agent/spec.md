# Feature Specification: Paper Analysis Agent

**Feature Branch**: `002-paper-analysis-agent`
**Created**: 2025-11-05
**Status**: Draft
**Input**: User description: "Develop Paper Analysis Agent integrating pdf_parser for comprehensive manuscript content analysis as the first agent in the journal recommendation system workflow"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Structured Manuscript Analysis (Priority: P1)

The system analyzes a submitted manuscript PDF and extracts comprehensive structured information including research domain, methodology, findings, article type, and citation patterns. This structured analysis feeds into the journal recommendation workflow.

**Why this priority**: This is the foundational capability for the entire journal recommendation system. Without accurate manuscript analysis, downstream agents (Journal Research, Matching Analyst, Report Writer) cannot function. This agent must produce reliable structured output that captures all dimensions relevant to journal matching.

**Independent Test**: Can be fully tested by providing a manuscript file_id and receiving a structured analysis output containing all required fields (primary research domain, article type, methodologies, key findings, target audience, frequently cited journals). The output structure enables immediate validation without depending on downstream agents.

**Acceptance Scenarios**:

1. **Given** a manuscript file_id for a research paper in the database, **When** the Paper Analysis Agent processes it, **Then** the system extracts and stores structured content including all paper sections
2. **Given** a structured manuscript with identified sections, **When** content analysis is performed, **Then** the system identifies primary research topics, keywords, and discipline classification
3. **Given** a manuscript with methodology section, **When** analysis is performed, **Then** the system extracts research methods, experimental designs, and technical approaches used
4. **Given** a manuscript with results and discussion sections, **When** analysis is performed, **Then** the system identifies key findings, their significance, and application domains
5. **Given** a manuscript with references section, **When** citation analysis is performed, **Then** the system identifies the top 3-5 most frequently cited journals
6. **Given** a completed analysis, **When** results are stored, **Then** all extracted information is persisted with a unique paper_analysis_result_id for downstream agent consumption

---

### User Story 2 - Classify Article Type and Target Audience (Priority: P2)

The agent determines the manuscript's article type (original research, review, case report, methods paper) and identifies the intended target audience (specialist vs interdisciplinary, regional focus) to support journal matching decisions.

**Why this priority**: Article type and audience scope are critical filters for journal selection. Many journals only accept specific article types, and audience breadth determines whether specialized or broad-scope journals are appropriate. This classification must happen after content extraction (P1) but is essential for effective recommendations.

**Independent Test**: Can be tested by providing analyzed manuscript content and receiving article type classification (with confidence score) and audience characterization (specialist/interdisciplinary, application domains, regional scope). This classification can be validated independently against the manuscript content.

**Acceptance Scenarios**:

1. **Given** a manuscript with traditional IMRAD structure and original data, **When** article type classification is performed, **Then** the system identifies it as "original research" with high confidence
2. **Given** a manuscript that synthesizes existing literature without new data, **When** article type classification is performed, **Then** the system identifies it as "review article"
3. **Given** a manuscript describing a novel methodological approach, **When** article type classification is performed, **Then** the system identifies it as "methods paper"
4. **Given** a highly specialized manuscript with narrow technical focus, **When** audience analysis is performed, **Then** the system classifies target audience as "specialist" with specific sub-discipline identification
5. **Given** a manuscript bridging multiple disciplines, **When** audience analysis is performed, **Then** the system classifies it as "interdisciplinary" with multiple relevant fields listed

---

### User Story 3 - Generate Comprehensive Analysis Summary (Priority: P3)

The agent produces a human-readable summary of the analysis results, highlighting the most relevant features for journal matching and providing confidence indicators for extracted information.

**Why this priority**: While structured data is essential for automated matching, a summary enables human review and debugging of the analysis quality. This is valuable for system validation and user transparency but not critical for the core matching workflow.

**Independent Test**: Can be tested by reviewing the generated summary against the structured analysis data to verify it accurately represents key findings, provides appropriate confidence indicators, and highlights journal-matching-relevant features. The summary format can be validated independently.

**Acceptance Scenarios**:

1. **Given** a completed analysis with all structured data, **When** summary generation is requested, **Then** the system produces a concise summary covering primary topics, article type, key methods, and citation patterns
2. **Given** analysis results with varying confidence levels, **When** summary is generated, **Then** the system includes confidence indicators for uncertain classifications
3. **Given** a multidisciplinary manuscript, **When** summary is generated, **Then** the system highlights the cross-disciplinary nature and lists relevant fields
4. **Given** a manuscript with frequently cited journals, **When** summary is generated, **Then** the system lists the top cited journals as reference points for journal matching

---

### Edge Cases

- What happens when the manuscript PDF is corrupted and pdf_parser fails to extract sections?
- How does the system handle manuscripts without a clear IMRAD structure (e.g., purely theoretical papers)?
- What happens when the references section is missing or incomplete?
- How does the system respond when methodology descriptions are vague or non-standard?
- What happens when the manuscript is in a language other than English?
- How does the system handle interdisciplinary papers that span 3+ distinct research domains?
- What happens when the article type is ambiguous (e.g., a case study with methodological innovations)?
- How does the system classify manuscripts with no clear application domain (pure theory)?
- What happens when frequently cited journals are from unrelated disciplines?

## Requirements *(mandatory)*

### Functional Requirements

#### Core Agent Integration

- **FR-001**: System MUST integrate the existing pdf_parser agent as the first stage of the Paper Analysis Agent workflow
- **FR-002**: System MUST accept file_id as input and pass it to pdf_parser to extract structured sections
- **FR-003**: System MUST retrieve the structured_content_overview_id output from pdf_parser for subsequent analysis stages
- **FR-004**: System MUST implement the CrewAI multi-agent framework as defined in the development guide
- **FR-005**: System MUST use OMA tools for all data reading and persistence operations
- **FR-006**: System MUST follow the ITaskExecutor interface pattern from oma_architecture.md

#### Content Analysis

- **FR-007**: System MUST analyze the manuscript title and abstract to extract primary research topics and keywords
- **FR-008**: System MUST identify the research discipline and sub-disciplines based on title, abstract, and introduction content
- **FR-009**: System MUST extract research background, problem motivation, and theoretical framework from the introduction section
- **FR-010**: System MUST analyze the methods section to identify research methodologies, experimental designs, data types, technologies, algorithms, and tools used
- **FR-011**: System MUST extract key findings from results and discussion sections, including nature of outcomes (quantitative/qualitative, theoretical/applied)
- **FR-012**: System MUST identify application domains and impact scope from results, discussion, and conclusion sections
- **FR-013**: System MUST extract author's stated contributions and target readership from the conclusion section

#### Citation Analysis

- **FR-014**: System MUST parse the references section to count journal citations
- **FR-015**: System MUST identify the top 3-5 most frequently cited journals in the references
- **FR-016**: System MUST analyze the fields covered by referenced works to infer the manuscript's academic network
- **FR-017**: System MUST handle cases where references are incomplete or improperly formatted

#### Classification

- **FR-018**: System MUST classify article type as one of: original research, review, case report, methods paper, or other
- **FR-019**: System MUST use manuscript structure (presence of methods, results, novel data) to inform article type classification
- **FR-020**: System MUST provide confidence scores for article type classification
- **FR-021**: System MUST identify target audience breadth (specialist vs interdisciplinary)
- **FR-022**: System MUST identify application domains or impact areas emphasized in the paper
- **FR-023**: System MUST detect regional focus if present (e.g., studies specific to geographic areas)

#### Data Output

- **FR-024**: System MUST produce structured output containing all extracted analysis dimensions in a machine-readable format
- **FR-025**: System MUST include the following fields in structured output: primary_topics (list), article_type (enum), methods (list), key_findings (list), target_audience (structured), reference_journals (list with counts)
- **FR-026**: System MUST generate a unique paper_analysis_result_id for the analysis output
- **FR-027**: System MUST persist all analysis results to the database using OMA write tools
- **FR-028**: System MUST ensure the output paper_analysis_result_id is distinct from the input structured_content_overview_id from pdf_parser

#### Quality and Error Handling

- **FR-029**: System MUST validate that pdf_parser successfully extracted sections before attempting content analysis
- **FR-030**: System MUST handle manuscripts with non-standard section organization by adapting analysis strategies
- **FR-031**: System MUST provide meaningful error messages when critical sections (abstract, methods, results) are missing
- **FR-032**: System MUST complete analysis and return partial results even if some sections are incomplete or unclear
- **FR-033**: System MUST log all analysis stages and tool calls for debugging as per OMA framework standards

### Key Entities

- **Manuscript File**: Input PDF document; identified by file_id from database; contains research paper content requiring analysis
- **Structured Content Overview**: Output from pdf_parser agent; contains section-by-section parsed content (abstract, introduction, methods, results, discussion, conclusion, references); identified by structured_content_overview_id
- **Paper Analysis Result**: Comprehensive analysis output; contains extracted features (primary_topics, article_type, methodologies, key_findings, target_audience, reference_journals, discipline classification, application_domains); identified by paper_analysis_result_id; consumed by downstream agents (Journal Research Agent)
- **Section Content**: Individual manuscript section; contains section_type (abstract, introduction, methods, etc.), title, and full text content; extracted by pdf_parser
- **Research Topic**: Identified subject area or keyword; includes primary discipline, sub-disciplines, technical terms; supports journal matching
- **Methodology Profile**: Extracted research methods; includes experimental design type, data collection approach, analytical techniques, tools/instruments; informs journal scope matching
- **Citation Profile**: Analysis of referenced journals; includes journal names with citation counts, fields covered by references; indicates manuscript's academic network
- **Article Classification**: Determined article type and audience; includes type (original research, review, methods, case report), confidence score, target audience breadth (specialist/interdisciplinary), application scope

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agent successfully processes manuscripts and produces structured analysis output containing all required dimensions (topics, type, methods, findings, audience, citations)
- **SC-002**: 95% of manuscripts with standard IMRAD structure result in complete analysis with all required fields populated
- **SC-003**: Article type classification achieves 90% accuracy compared to author-declared article types
- **SC-004**: For manuscripts with references sections, system identifies top 3-5 cited journals in 95% of cases
- **SC-005**: Research methodology extraction captures at least 80% of methodological keywords present in the methods section
- **SC-006**: Primary research topic identification aligns with manuscript keywords and abstract in 90% of cases
- **SC-007**: Analysis workflow completes within 5 minutes for manuscripts up to 50 pages
- **SC-008**: Agent successfully integrates with pdf_parser and retrieves structured sections in 100% of successful pdf_parser runs
- **SC-009**: Output analysis results are successfully persisted to database with unique identifiers in 100% of completed analyses
- **SC-010**: Downstream agents (Journal Research Agent) can successfully consume the paper_analysis_result_id and retrieve all analysis dimensions

## Assumptions

- The pdf_parser agent is already implemented and functional in app/agents/pdf_parser.py
- The pdf_parser produces structured_content_overview_id as output which references stored section content
- OMA tools for reading structured content and creating analysis records are available and functional
- Manuscripts are primarily in English (consistent with system design documents)
- The agent will be registered with the orchestrator and receive tasks via the OMA framework
- Real database IDs will be used in task context (manuscript_id, user_id, file_id) as per development guide
- The data service APIs (localhost:8008/api/database/v1) are available for tool operations
- Analysis results will be stored following the same pattern as pdf_parser (using Create/Complete workflow)
- Agent configuration will specify file_id as input and paper_analysis_result_id as output
- The agent will be placed in app/agents/ directory following project structure principles
- CrewAI agents will use English prompts as specified in development guide
- Token management strategies (simplified backstories, focused task descriptions) will be applied
