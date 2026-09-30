# 🔎 Deep Research Agent

An end-to-end **multi-agent Deep Research Agent** that transforms complex user questions into structured, evidence-backed research reports using web search, evidence extraction, LLM synthesis, citation validation, and critical review.
---

## 📌 Overview

Traditional search systems often return a collection of links and snippets, leaving users to manually read, compare, and synthesize information.

This project automates that workflow through a multi-agent research pipeline.

A user provides a complex research question, and the system:

1. Breaks the question into four research tasks.
2. Searches the web for relevant information.
3. Extracts and analyzes evidence from retrieved sources.
4. Builds a structured research packet.
5. Generates a coherent research report.
6. Validates citations and evidence-source relationships.
7. Critically evaluates the generated report.
8. Revises the report when required.
9. Presents the final result through an interactive Streamlit interface.

---

# 🌐 Live Application

🚀 **Deep Research Agent:**  
https://deepresearchagent-obymdyc6zkrovqdz3hpmne.streamlit.app/

---

# 🧠 System Architecture

```text
                    ┌─────────────────────┐
                    │    User Question    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Planner Agent     │
                    │   Creates 4 Tasks   │
                    └──────────┬──────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │       Parallel Research        │
              └────────────────┬───────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
             Search         Search         Search
             Agent          Agent          Agent
                │              │              │
                └──────────────┼──────────────┘
                               ▼
                       ┌───────────────┐
                       │ Reader Agent  │
                       │ Evidence      │
                       │ Extraction    │
                       └───────┬───────┘
                               │
                               ▼
                       ┌───────────────┐
                       │ Research      │
                       │ Evidence      │
                       │ Packet        │
                       └───────┬───────┘
                               │
                               ▼
                       ┌───────────────┐
                       │ Writer Agent  │
                       │ Final Draft   │
                       └───────┬───────┘
                               │
                               ▼
                       ┌───────────────┐
                       │ Critic Agent  │
                       │ Review +      │
                       │ Validation    │
                       └───────┬───────┘
                               │
                     ┌─────────┴─────────┐
                     │                   │
                  APPROVED             REVISE
                     │                   │
                     ▼                   ▼
                  FINAL              Writer
                  REPORT            Revision
```

---

# 🤖 Multi-Agent Design

The system uses **four specialized research agents**, while the Planner acts as the orchestration layer.

## 1. 🧠 Planner Agent

The Planner receives the original user question and decomposes it into **four independent and researchable tasks**.

### Responsibilities

- Understand the research question.
- Identify major dimensions of the topic.
- Create four specific research tasks.
- Ensure the combined tasks address the original question.
- Avoid directly answering the question.

Example:

```text
User Question
     ↓
TASK 1
TASK 2
TASK 3
TASK 4
```

The internal research task structure is used for orchestration and is not exposed as the final report structure.

---

## 2. 🔎 Search Agent

Each research task is sent to the web search layer using **Tavily**.

### Responsibilities

- Generate task-specific search queries.
- Retrieve relevant web sources.
- Collect source metadata such as:
  - Source title
  - URL
  - Search snippet
  - Search score
  - Associated research task
- Support parallel research execution.

The current implementation uses a lightweight search configuration to maintain a balance between research coverage and execution time.

---

## 3. 📖 Reader Agent

The Reader Agent transforms retrieved web information into structured evidence.

### Responsibilities

- Retrieve webpage content using Tavily extraction.
- Use search-result snippets as a fallback when full webpage extraction is unavailable.
- Analyze retrieved material using the LLM.
- Extract:
  - Key factual findings
  - Important evidence
  - Numbers and statistics
  - Technical details
  - Limitations
  - Conflicting information
- Preserve the relationship between evidence and source URLs.

The Reader creates the evidence layer used by the Writer.

---

## 4. ✍️ Writer Agent

The Writer receives the original question, research tasks, and collected evidence.

Its purpose is to generate a **single coherent research report** rather than separate mini-reports for each internal task.

### Responsibilities

- Answer the original question directly.
- Synthesize findings across research areas.
- Create meaningful topic-based headings.
- Use only supplied research evidence.
- Add source identifiers such as:

```text
[S001]
[S002]
[S003]
```

- Avoid inventing:
  - Facts
  - Statistics
  - Dates
  - Sources
  - URLs
- Clearly communicate uncertainty and evidence gaps.

The final report does not expose the internal Planner, Search, Reader, or Critic workflow.

---

## 5. 🧐 Critic Agent

The Critic Agent evaluates the Writer's draft before finalization.

It combines **programmatic validation** with LLM-based evaluation.

### Programmatic validation

The system automatically checks:

- Citation IDs
- Invalid source references
- Missing task citations
- Evidence-to-source relationships
- Empty reports
- Source registry consistency

### LLM-based evaluation

The Critic checks whether:

- The original question is answered.
- Research areas are adequately covered.
- Important claims are supported.
- Citations are valid and relevant.
- Unsupported facts were introduced.
- The conclusion is consistent with the evidence.

The Critic returns:

```text
DECISION=APPROVED
```

or:

```text
DECISION=REVISE
```

When revision is required, Critic feedback is passed back to the Writer for another generation cycle.

---

# 📚 Evidence & Citation System

The system maintains a structured source registry.

Every retrieved source receives a deterministic identifier:

```text
S001
S002
S003
...
```

The Writer uses these identifiers directly in the report.

Example:

```text
Machine learning has been applied to reservoir characterization [S001].
```

The application automatically creates the References section from the source registry.

This provides source traceability without requiring the Writer to manually construct a reference list.

---

# 🔗 Evidence Validation

Evidence is linked back to source URLs before being passed to the Writer.

The validation flow is:

```text
Evidence
   ↓
Source ID
   ↓
Registered Source
   ↓
URL
```

Evidence with invalid or unmatched source references is separated from valid evidence rather than silently being treated as reliable.

---

# ⚡ Parallel Research

The research stage uses Python's `ThreadPoolExecutor` to process independent research tasks concurrently.

Conceptually:

```text
                 Research
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Task 1    Task 2    Task 3
          │         │         │
          └─────────┼─────────┘
                    ▼
                  Task 4
```

The current implementation limits worker concurrency to balance parallelism with local LLM resource usage.

---

# 🧩 LangGraph Orchestration

LangGraph manages the workflow state and agent transitions.

The core graph is:

```text
planner
   ↓
research
   ↓
writer
   ↓
critic
   ↓
writer / END
```

The shared state contains information such as:

```text
question
tasks
sources
evidence
research_results
research_packet
source_registry
invalid_evidence
draft
critique
approved
revision_count
final_report
```

This shared state allows every stage to build on information produced by previous stages.

---

# 🖥️ Streamlit Interface

The application is built using **Streamlit** and provides an interactive research interface.

The interface allows users to follow the research workflow rather than seeing only the final answer.

---

# 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Core application logic |
| **LangGraph** | Agent orchestration and state management |
| **LangChain** | LLM integration |
| **Ollama** | Local LLM execution |
| **Qwen3 4B** | Local development model |
| **Groq** | Cloud LLM deployment |
| **Tavily** | Web search and webpage extraction |
| **Streamlit** | Web application interface |
| **python-dotenv** | Environment configuration |
| **Pydantic** | Data validation and structured data support |

---

# 🧠 LLM Configuration

The project supports multiple LLM providers through environment-based configuration.

## Local Development

The local version uses Ollama with Qwen3:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:4b
TAVILY_API_KEY=your_tavily_api_key
```

Qwen3 is configured with reasoning disabled for faster structured agent execution.

---

## Cloud Deployment

For Streamlit Cloud, the application can use Groq:

```toml
LLM_PROVIDER = "groq"
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_API_KEY = "your_groq_api_key"
TAVILY_API_KEY = "your_tavily_api_key"
```

Cloud credentials should be stored using Streamlit Secrets rather than committed to GitHub.

---

# 🔐 Security

Sensitive credentials should never be committed to the repository.

Keep the following private:

```text
.env
.streamlit/secrets.toml
venv/
API keys
```

A `.env.example` file can document required configuration without exposing credentials.

Example:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:4b
TAVILY_API_KEY=your_tavily_api_key
```

---

# 📊 Current Prototype

The current version focuses on building a complete functional agentic research pipeline with:

- Multi-agent orchestration
- Parallel research
- Web search
- Webpage extraction
- Evidence extraction
- Source traceability
- Citation validation
- Automated critique
- Revision support
- Local LLM execution
- Cloud LLM support
- Streamlit deployment
- Downloadable research reports

The current prototype balances research depth and execution time, particularly when using local Ollama inference.

---

# ⚠️ Limitations

This project is a research prototype and should not be treated as a guaranteed fact-checking or authoritative decision-making system.

Current limitations include:

- Search quality depends on the sources returned by Tavily.
- Retrieved webpage content may be incomplete.
- Some websites may block webpage extraction.
- Local Ollama inference can introduce significant latency.
- The Critic does not independently verify every claim against the real world.
- The current search configuration uses a limited number of sources to control runtime.
- Conflicting or incomplete sources may require additional human review.

---

# 🔮 Future Improvements

Planned improvements include:

- Claim-level evidence verification
- Improved source quality ranking
- Adaptive search depth
- Better query generation
- Additional LLM provider support
- More advanced research quality evaluation

---


# 👨‍💻 Author

**Sayan Das**
---


