# Data Model: Paper Analysis Agent

**Phase**: 1 - Design & Contracts
**Date**: 2025-11-05
**Status**: Complete

## Overview

This document defines the data entities, schemas, and validation rules for the Paper Analysis Agent. All models use Pydantic for type safety and validation.

---

## Core Entities

### 1. PaperAnalysisInput

**Purpose**: Input parameters for Paper Analysis Agent

**Fields**:
```python
from pydantic import BaseModel, Field

class PaperAnalysisInput(BaseModel):
    """Input for Paper Analysis Agent execution"""
    file_id: str = Field(..., description="UUID of manuscript file in database")
    manuscript_id: str | None = Field(None, description="Optional manuscript UUID for context")
    user_id: str | None = Field(None, description="Optional user UUID for context")
```

**Validation Rules**:
- `file_id`: MUST be valid UUID format
- `file_id`: MUST exist in database (validated by pdf_parser)

**Usage**:
```python
input_data = PaperAnalysisInput(
    file_id="14c302e6-9cf9-4cbe-8d11-393ef02ee228",
    manuscript_id="9a94c7f4-e4d0-4586-88cb-5412872a7be8",
    user_id="2ae0adad-bb76-4a78-a8e8-19db5ebbf4a9"
)
```

---

### 2. ResearchTopic

**Purpose**: Identified research topics and keywords

**Fields**:
```python
class ResearchTopic(BaseModel):
    """Extracted research topic information"""
    primary_discipline: str = Field(..., description="Main research discipline (e.g., 'Computer Science', 'Medicine')")
    sub_disciplines: list[str] = Field(default_factory=list, description="Specific sub-fields")
    keywords: list[str] = Field(default_factory=list, description="Key technical terms and concepts")
    technical_terms: list[str] = Field(default_factory=list, description="Domain-specific terminology")
```

**Validation Rules**:
- `primary_discipline`: MUST NOT be empty
- `keywords`: MUST contain at least 3 items for valid analysis
- All string fields: Stripped whitespace, title case for disciplines

**Example**:
```python
topic = ResearchTopic(
    primary_discipline="Biomedical Engineering",
    sub_disciplines=["Medical Imaging", "Deep Learning", "Diagnostic Systems"],
    keywords=["Alzheimer's disease", "MRI", "convolutional neural networks", "early diagnosis"],
    technical_terms=["neural network architecture", "image segmentation", "classification accuracy"]
)
```

---

### 3. MethodologyProfile

**Purpose**: Extracted research methods and approaches

**Fields**:
```python
class MethodologyProfile(BaseModel):
    """Research methodology information"""
    experimental_design: str | None = Field(None, description="Type of study design")
    data_collection: list[str] = Field(default_factory=list, description="Data gathering approaches")
    analytical_techniques: list[str] = Field(default_factory=list, description="Analysis methods used")
    tools_and_instruments: list[str] = Field(default_factory=list, description="Specific tools, software, or equipment")
    methodology_keywords: list[str] = Field(default_factory=list, description="Key methodological terms")
```

**Validation Rules**:
- At least ONE of the list fields MUST contain items for valid methodology
- `experimental_design`: Can be null for purely theoretical papers

**Example**:
```python
methods = MethodologyProfile(
    experimental_design="Retrospective cohort study",
    data_collection=["MRI scans", "Clinical records", "Patient demographics"],
    analytical_techniques=["Deep learning classification", "Cross-validation", "ROC analysis"],
    tools_and_instruments=["PyTorch", "TensorFlow", "NVIDIA GPUs", "3T MRI scanner"],
    methodology_keywords=["supervised learning", "transfer learning", "data augmentation"]
)
```

---

### 4. KeyFinding

**Purpose**: Individual research finding or result

**Fields**:
```python
class KeyFinding(BaseModel):
    """Single research finding"""
    finding_text: str = Field(..., description="Description of the finding")
    significance: str | None = Field(None, description="Why this finding matters")
    outcome_type: str = Field(..., description="quantitative|qualitative|theoretical|applied")
```

**Validation Rules**:
- `finding_text`: MUST NOT be empty, max 500 characters
- `outcome_type`: MUST be one of 4 enumerated values
- `significance`: Optional but recommended for key findings

**Example**:
```python
finding = KeyFinding(
    finding_text="Proposed CNN model achieved 94.2% accuracy in early Alzheimer's detection",
    significance="Demonstrates viability of automated screening, potentially reducing diagnostic delays",
    outcome_type="quantitative"
)
```

---

### 5. CitedJournal

**Purpose**: Journal citation frequency from references

**Fields**:
```python
class CitedJournal(BaseModel):
    """Journal citation information"""
    journal_name: str = Field(..., description="Full name of the journal")
    citation_count: int = Field(..., ge=1, description="Number of times cited in references")
    fields_covered: list[str] = Field(default_factory=list, description="Research fields of cited articles")
```

**Validation Rules**:
- `journal_name`: MUST NOT be empty, normalized (title case, no extra spaces)
- `citation_count`: MUST be >= 1
- `fields_covered`: Can be empty if not determinable from references

**Example**:
```python
journal = CitedJournal(
    journal_name="Nature Medicine",
    citation_count=8,
    fields_covered=["Medical Imaging", "Neurology", "Diagnostic Technologies"]
)
```

---

### 6. CitationProfile

**Purpose**: Aggregated citation analysis

**Fields**:
```python
class CitationProfile(BaseModel):
    """Citation analysis results"""
    total_references: int = Field(0, ge=0, description="Total number of references")
    cited_journals: list[CitedJournal] = Field(default_factory=list, description="Top 3-5 most cited journals")
    citation_fields: list[str] = Field(default_factory=list, description="Research fields represented in references")
```

**Validation Rules**:
- `total_references`: Can be 0 if no references section
- `cited_journals`: Sorted by citation_count descending, max 5 items
- `citation_fields`: Deduplicated list of unique fields

**Example**:
```python
profile = CitationProfile(
    total_references=42,
    cited_journals=[
        CitedJournal(journal_name="Nature Medicine", citation_count=8),
        CitedJournal(journal_name="IEEE Transactions on Medical Imaging", citation_count=6),
        CitedJournal(journal_name="NeuroImage", citation_count=5)
    ],
    citation_fields=["Medical Imaging", "Neurology", "Machine Learning", "Diagnostics"]
)
```

---

### 7. ArticleClassification

**Purpose**: Article type and audience classification

**Fields**:
```python
class ArticleClassification(BaseModel):
    """Article classification results"""
    article_type: str = Field(..., description="original_research|review|case_report|methods|other")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Classification confidence (0-1)")
    target_audience_breadth: str = Field(..., description="specialist|interdisciplinary|general")
    application_domains: list[str] = Field(default_factory=list, description="Practical application areas")
    regional_focus: str | None = Field(None, description="Geographic focus if applicable")
```

**Validation Rules**:
- `article_type`: MUST be one of 5 enumerated values
- `confidence_score`: MUST be between 0.0 and 1.0
- `target_audience_breadth`: MUST be specialist|interdisciplinary|general
- `application_domains`: Can be empty for pure theory papers

**Example**:
```python
classification = ArticleClassification(
    article_type="original_research",
    confidence_score=0.92,
    target_audience_breadth="interdisciplinary",
    application_domains=["Clinical Diagnosis", "Healthcare AI", "Medical Screening"],
    regional_focus=None
)
```

---

### 8. PaperAnalysisResult

**Purpose**: Complete analysis output (persisted to database)

**Fields**:
```python
class PaperAnalysisResult(BaseModel):
    """Complete paper analysis output"""
    # Core analysis
    research_topics: ResearchTopic
    methodology_profile: MethodologyProfile
    key_findings: list[KeyFinding] = Field(default_factory=list)
    citation_profile: CitationProfile
    article_classification: ArticleClassification

    # Summary
    analysis_summary: str | None = Field(None, description="Human-readable analysis summary")

    # Metadata
    structured_content_overview_id: str = Field(..., description="Input from pdf_parser")
    analysis_timestamp: str = Field(..., description="ISO 8601 timestamp")
```

**Validation Rules**:
- ALL nested models MUST pass their own validation
- `key_findings`: MUST contain at least 1 item for complete analysis
- `structured_content_overview_id`: MUST be valid UUID
- `analysis_timestamp`: MUST be ISO 8601 format

**Example**:
```python
result = PaperAnalysisResult(
    research_topics=ResearchTopic(...),
    methodology_profile=MethodologyProfile(...),
    key_findings=[KeyFinding(...), KeyFinding(...)],
    citation_profile=CitationProfile(...),
    article_classification=ArticleClassification(...),
    analysis_summary="This interdisciplinary study presents...",
    structured_content_overview_id="feae5c67-19ed-4e1d-b274-b87051d12389",
    analysis_timestamp="2025-11-05T15:30:00Z"
)
```

---

### 9. PaperAnalysisOutput

**Purpose**: Agent execution output (ITaskExecutor interface)

**Fields**:
```python
class PaperAnalysisOutput(BaseModel):
    """Output from PaperAnalysisAgent.execute()"""
    status: str = Field(..., description="success|error")
    result: dict = Field(..., description="On success: {paper_analysis_result_id: str}, On error: {error: str, error_type: str}")
```

**Validation Rules**:
- `status`: MUST be "success" or "error"
- On success: `result` MUST contain "paper_analysis_result_id" key with UUID value
- On error: `result` MUST contain "error" and "error_type" keys

**Example (Success)**:
```python
output = PaperAnalysisOutput(
    status="success",
    result={"paper_analysis_result_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
)
```

**Example (Error)**:
```python
output = PaperAnalysisOutput(
    status="error",
    result={
        "error": "pdf_parser failed to extract sections from corrupted PDF",
        "error_type": "PDFParsingError"
    }
)
```

---

## Intermediate Agent Outputs

### 10. ContentAnalysisOutput

**Purpose**: Output from Content Analyzer sub-agent

**Fields**:
```python
class ContentAnalysisOutput(BaseModel):
    """Output from content analysis stage"""
    research_topics: ResearchTopic
    methodology_profile: MethodologyProfile
    key_findings: list[KeyFinding]
```

---

### 11. CitationAnalysisOutput

**Purpose**: Output from Citation Analyzer sub-agent

**Fields**:
```python
class CitationAnalysisOutput(BaseModel):
    """Output from citation analysis stage"""
    citation_profile: CitationProfile
```

---

### 12. ClassificationOutput

**Purpose**: Output from Classification sub-agent

**Fields**:
```python
class ClassificationOutput(BaseModel):
    """Output from classification stage"""
    article_classification: ArticleClassification
```

---

### 13. SummaryOutput

**Purpose**: Output from Summary Generator sub-agent

**Fields**:
```python
class SummaryOutput(BaseModel):
    """Output from summary generation stage"""
    analysis_summary: str = Field(..., min_length=100, description="Comprehensive analysis summary")
```

**Validation Rules**:
- `analysis_summary`: MUST be at least 100 characters (meaningful summary)

---

## State Transitions

### Agent Execution States

```
INITIALIZATION
    ↓
PDF_PARSING (calls pdf_parser)
    ↓ [success]
CONTENT_ANALYSIS (analyzes sections)
    ↓ [success]
CITATION_ANALYSIS (analyzes references)
    ↓ [success]
CLASSIFICATION (determines type/audience)
    ↓ [success]
SUMMARY_GENERATION (creates summary)
    ↓ [success]
PERSISTENCE (saves to database)
    ↓ [success]
COMPLETE (returns paper_analysis_result_id)

    ↓ [error at any stage]
ERROR (returns error details)
```

**State Tracking** (in shared context):
```python
context.set_shared_data("current_stage", "content_analysis")
context.set_shared_data("stages_completed", ["pdf_parsing"])
```

---

## Database Schema (Reference)

### paper_analyses Table (in Data Service)

**Note**: Actual database schema managed by data service. This is reference only.

```sql
CREATE TABLE paper_analyses (
    id UUID PRIMARY KEY,
    structured_content_overview_id UUID REFERENCES structured_content_overviews(id),
    manuscript_id UUID REFERENCES manuscripts(id),

    -- Research Topics
    primary_discipline VARCHAR(255),
    sub_disciplines JSONB,
    keywords JSONB,
    technical_terms JSONB,

    -- Methodology
    experimental_design VARCHAR(255),
    data_collection JSONB,
    analytical_techniques JSONB,
    tools_and_instruments JSONB,
    methodology_keywords JSONB,

    -- Findings
    key_findings JSONB,

    -- Citations
    total_references INT,
    cited_journals JSONB,
    citation_fields JSONB,

    -- Classification
    article_type VARCHAR(50),
    confidence_score FLOAT,
    target_audience_breadth VARCHAR(50),
    application_domains JSONB,
    regional_focus VARCHAR(255),

    -- Summary
    analysis_summary TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Validation Summary

### Critical Validations

1. **UUID Format**: All ID fields (file_id, overview_id, result_id) must be valid UUIDs
2. **Non-Empty Core Fields**: primary_discipline, article_type, key_findings must not be empty
3. **Enum Values**: article_type, outcome_type, target_audience_breadth must match allowed values
4. **Confidence Bounds**: confidence_score must be 0.0-1.0
5. **Citation Counts**: citation_count must be >= 1
6. **Timestamp Format**: ISO 8601 format for all timestamps

### Optional Fields

- `significance` in KeyFinding
- `regional_focus` in ArticleClassification
- `experimental_design` in MethodologyProfile
- `analysis_summary` (P3 user story, can be null initially)

### Error Handling

- **ValidationError**: Pydantic raises on invalid data types or constraint violations
- **ValueError**: Raised for business logic violations (e.g., empty required lists)
- **KeyError**: Raised when accessing missing shared context data

---

## Usage in Code

### Creating Models

```python
# Content analysis output
content_output = ContentAnalysisOutput(
    research_topics=ResearchTopic(
        primary_discipline="Medical Imaging",
        sub_disciplines=["Radiology", "AI in Healthcare"],
        keywords=["MRI", "deep learning", "diagnosis"]
    ),
    methodology_profile=MethodologyProfile(
        experimental_design="Retrospective study",
        analytical_techniques=["CNN", "Transfer learning"]
    ),
    key_findings=[
        KeyFinding(
            finding_text="94% diagnostic accuracy",
            significance="Exceeds human radiologist baseline",
            outcome_type="quantitative"
        )
    ]
)

# Save to shared context
context.set_shared_data("content_analysis", content_output.model_dump())
```

### Reading Models

```python
# Retrieve from shared context
content_data = context.get_shared_data("content_analysis")
content_output = ContentAnalysisOutput(**content_data)

# Access nested fields
primary_field = content_output.research_topics.primary_discipline
```

### Validation

```python
try:
    result = PaperAnalysisResult(**data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise ValueError(f"Invalid analysis result: {e}")
```

---

## References

1. **Pydantic Documentation**: https://docs.pydantic.dev/latest/
2. **OMA Data Models**: `oxsci_oma_core/models/`
3. **Feature Spec**: `specs/002-paper-analysis-agent/spec.md` (Key Entities section)
4. **Data Service API**: `localhost:8008/openapi.json`
