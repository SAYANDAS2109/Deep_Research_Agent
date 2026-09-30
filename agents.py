import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from tavily import TavilyClient
import re
from llm import get_llm


load_dotenv()


llm = get_llm()



tavily_key = os.getenv(
    "TAVILY_API_KEY"
)

print(
    "[ENV] Tavily key loaded:",
    bool(tavily_key)
)

tavily_client = TavilyClient(
    api_key=tavily_key
)
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)



def planner_agent(state):

    print("\n[PLANNER] Creating research tasks...")

    question = state["question"]

    prompt = f"""
You are the Planner Agent in a deep research system.

User question:

{question}

Break this question into exactly 4 independent
research tasks.

Rules:

1. Each task must investigate a different aspect.
2. The four tasks together must answer the question.
3. Tasks must be specific and researchable.
4. Do not answer the question.
5. Return only the tasks.

OUTPUT FORMAT:

TASK 1: <one research task>
TASK 2: <one research task>
TASK 3: <one research task>
TASK 4: <one research task>

Do not use Markdown.
Do not use bullets.
Do not add explanations.
Do not add <think> content.
Return exactly four TASK lines.
"""

    response = llm.invoke(prompt)

    text = response.content

    print("\n[PLANNER DEBUG] Raw LLM response:")
    print(text)



    tasks = []

# Remove Qwen reasoning block if present
    text = re.sub(
    r"<think>.*?</think>",
    "",
    text,
    flags=re.DOTALL | re.IGNORECASE
).strip()


# --------------------------------------
# EXTRACT TASKS ROBUSTLY
# --------------------------------------

    task_pattern = re.compile(
    r"(?is)"
    r"(?:^|\n)"
    r"\s*"
    r"(?:[#>*\-\d\.\)]\s*)*"
    r"(?:\*\*)?"
    r"TASK\s*([1-4])"
    r"\s*[:\-]"
    r"\s*"
    r"(.*?)"
    r"(?="
    r"\n\s*(?:[#>*\-\d\.\)]\s*)*"
    r"(?:\*\*)?"
    r"TASK\s*[1-4]\s*[:\-]"
    r"|$"
    r")"
)


    matches = task_pattern.findall(text)


    for task_number, task_text in matches:

        task_text = task_text.strip()

        task_text = task_text.replace(
        "**",
        ""
    ).strip()

        if task_text:

            tasks.append(
            f"TASK {task_number}: "
            f"{task_text}"
        )


# Sort by task number
    tasks.sort(
    key=lambda x: int(
        re.search(
            r"TASK\s*(\d)",
            x
        ).group(1)
    )
)

    
    if len(tasks) > 4:
        tasks = tasks[:4]

    print("\n[PLANNER] Tasks created:")

    for task in tasks:
        print("-", task)

    return {
        **state,
        "tasks": tasks
    }



def search_single_task(task, original_question=""):

    print(
        f"\n[SEARCH] Starting:\n{task}"
    )

    queries = [

        task,

        task.replace(
            "TASK 1:",
            ""
        ).replace(
            "TASK 2:",
            ""
        ).replace(
            "TASK 3:",
            ""
        ).replace(
            "TASK 4:",
            ""
        ).strip(),

        f"{original_question} {task}"
    ]

    # Remove duplicate queries
    unique_queries = []

    for query in queries:

        query = query.strip()

        if query and query not in unique_queries:

            unique_queries.append(query)


    for query_number, query in enumerate(
        unique_queries,
        start=1
    ):

        print(
            f"[SEARCH] Attempt {query_number}: "
            f"{query}"
        )

        try:

            response = tavily_client.search(
                query=query,
                search_depth="basic",
                max_results=1
            )

            results = response.get(
                "results",
                []
            )

            sources = []

            for result in results:

                url = result.get(
                    "url",
                    ""
                ).strip()

                if not url:
                    continue

                sources.append({

                    "task":
                        task,

                    "title":
                        result.get(
                            "title",
                            ""
                        ),

                    "url":
                        url,

                    "snippet":
                        result.get(
                            "content",
                            ""
                        ),

                    "score":
                        result.get(
                            "score",
                            0
                        )
                })

            if sources:

                print(
                    f"[SEARCH] Found "
                    f"{len(sources)} sources."
                )

                return sources

        except Exception as e:

            print(
                f"[SEARCH ERROR] {e}"
            )
            print(
        f"Task: {task}"
    )

            print(
        f"Query: {query}"
    )

            print(
        f"Error type: {type(e).__name__}"
    )

            print(
        f"Error: {e}"
    )


    print(
        "[SEARCH] All search attempts failed."
    )

    return []

def read_single_task(task, sources):

    print(
        f"\n[READER] Processing task:\n{task}"
    )

    if not sources:

        print(
            "[READER] No search sources available."
        )

        return []
    



    urls = [

        source["url"]

        for source in sources

        if source.get("url")
    ]


    extracted_results = []


    if urls:

        try:

            print(
                f"[READER] Extracting "
                f"{len(urls)} webpages..."
            )

            extracted = tavily_client.extract(
                urls=urls
            )

            extracted_results = extracted.get(
                "results",
                []
            )

        except Exception as e:

            print(
                f"[READER] Extraction failed: {e}"
            )


    # CREATE SOURCE LOOKUP
    source_lookup = {}

    for source in sources:

        source_lookup[
            source["url"]
        ] = source

    # BUILD CONTENT

    combined_content = ""

    # FULL PAGE CONTENT


    for result in extracted_results:

        url = result.get(
            "url",
            ""
        )

        raw_content = result.get(
            "raw_content",
            ""
        )

        source = source_lookup.get(
            url
        )

        if not source:
            continue

        if not raw_content:
            continue

        raw_content = raw_content[:9000]

        combined_content += f"""
--- FULL SOURCE ---
TITLE: {source["title"]}
URL: {url}

CONTENT:
{raw_content}

"""


    if not combined_content.strip():

        print(
            "[READER] Full webpage extraction "
            "unavailable."
        )

        print(
            "[READER] Using search-result "
            "content as fallback."
        )

        for source in sources:

            snippet = source.get(
                "snippet",
                ""
            )

            if not snippet:
                continue

            combined_content += f"""
--- SEARCH RESULT FALLBACK ---
TITLE: {source["title"]}
URL: {source["url"]}

CONTENT:
{snippet}

"""

    if not combined_content.strip():

        print(
            "[READER] No readable content found."
        )

        return []


    # Limit total content
    combined_content = (
        combined_content[:14000]
    )


    prompt = f"""
You are the Reader Agent.

Research task:

{task}


Available research material:

{combined_content}


Extract the useful information relevant to
the research task.

Return:

1. Key factual findings
2. Important evidence
3. Important numbers/statistics
4. Technical details
5. Limitations
6. Conflicting information


For every important finding, identify the
supporting source URL.


Rules:

- Use only the supplied research material.
- Do not invent facts.
- Do not use outside knowledge.
- Do not assume missing information.
- If information is incomplete, say so.
- Search-result content may be used when
  full webpage extraction is unavailable.
"""


    try:

        response = llm.invoke(
            prompt
        )

        return [{

            "task":
                task,

            "source":
                "Multiple sources",

            "url":
                "; ".join(
                    source["url"]
                    for source in sources
                ),

            "analysis":
                response.content
        }]

    except Exception as e:

        print(
            f"[READER ERROR] {e}"
        )

        return []


def research_one_task(task,original_question):

    print(
        f"\n========================================"
    )

    print(
        f"STARTING TASK:\n{task}"
    )

    print(
        f"========================================"
    )


    sources = search_single_task(
        task,original_question
    )

    print(
        f"[SEARCH] Found {len(sources)} "
        f"sources for this task."
    )


    evidence = read_single_task(
        task,
        sources
    )
    # ======================================
# FALLBACK EVIDENCE
# ======================================

    if not evidence and sources:

        print(
        "[RESEARCH] Reader returned no evidence."
    )

        print(
        "[RESEARCH] Using search snippets as fallback evidence."
    )

        evidence = []

        for source in sources:

            snippet = source.get(
            "snippet",
            ""
        )

            if not snippet:
                continue

            evidence.append({

            "task":
                task,

            "source":
                source.get(
                    "title",
                    ""
                ),

            "url":
                source.get(
                    "url",
                    ""
                ),

            "analysis":
                snippet
        })

    print(
        f"[READER] Generated "
        f"{len(evidence)} evidence items."
    )

    return {

        "task": task,

        "sources": sources,

        "evidence": evidence
    }


def parallel_research_agent(state):

    tasks = state.get(
        "tasks",
        []
    )

    question = state.get(
        "question",
        ""
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "[RESEARCH] Starting parallel research"
    )

    print(
        f"[RESEARCH] Number of tasks: "
        f"{len(tasks)}"
    )

    print(
        "=" * 60
    )


    if not tasks:

        print(
            "[RESEARCH] No tasks available."
        )

        return {

            **state,

            "sources":
                [],

            "evidence":
                [],

            "research_results":
                [],

            "research_packet":
                "",

            "source_registry":
                {},

            "invalid_evidence":
                [],

            "answer_status":
                "limited_evidence"
        }

    research_results = []

    max_workers = min(
        4,
        len(tasks)
    )

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        future_to_task = {}

        for task in tasks:

            future = executor.submit(
                research_one_task,
                task,
                question
            )

            future_to_task[
                future
            ] = task


        for future in as_completed(
            future_to_task
        ):

            task = future_to_task[
                future
            ]

            try:

                result = future.result()
                print(
    f"\n[RESEARCH DEBUG] Completed task: {task}"
)

                print(
    f"[RESEARCH DEBUG] Sources: "
    f"{len(result.get('sources', []))}"
)

                print(
    f"[RESEARCH DEBUG] Evidence: "
    f"{len(result.get('evidence', []))}"
)

                research_results.append(
                    result
                )

            except Exception as e:

                print(
                    f"[RESEARCH ERROR] "
                    f"{task}: {e}"
                )

                research_results.append({

                    "task":
                        task,

                    "sources":
                        [],

                    "evidence":
                        []
                })


    task_order = {

        task: index

        for index, task in enumerate(
            tasks
        )
    }

    research_results.sort(

        key=lambda result:
        task_order.get(
            result.get(
                "task",
                ""
            ),
            999
        )
    )


    all_sources = []

    all_evidence = []

    for result in research_results:

        all_sources.extend(
            result.get(
                "sources",
                []
            )
        )

        all_evidence.extend(
            result.get(
                "evidence",
                []
            )
        )


    unique_sources = []

    seen_urls = set()

    for source in all_sources:

        url = source.get(
            "url",
            ""
        ).strip()

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(
            url
        )

        unique_sources.append(
            source
        )

    all_sources = unique_sources

    for index, source in enumerate(
        all_sources,
        start=1
    ):

        source["source_id"] = (
            f"S{index:03d}"
        )

    source_id_by_url = {}

    for source in all_sources:

        source_id_by_url[
            source["url"]
        ] = source["source_id"]

    for evidence_item in all_evidence:

        evidence_url = evidence_item.get(
            "url",
            ""
        ).strip()


        if evidence_url in source_id_by_url:

            evidence_item["source_id"] = (
                source_id_by_url[
                    evidence_url
                ]
            )

            continue


        # ----------------------------------
        # Multiple URLs
        # ----------------------------------
        # Handles Reader fallback /
        # combined-source implementation
        # where URLs may be joined by ";"
        # ----------------------------------

        possible_urls = [

            url.strip()

            for url in evidence_url.split(";")

            if url.strip()
        ]


        matched_ids = []

        for url in possible_urls:

            source_id = (
                source_id_by_url.get(
                    url
                )
            )

            if source_id:

                matched_ids.append(
                    source_id
                )


        if matched_ids:

            # Keep the first one as the primary
            # citation source for compatibility

            evidence_item["source_id"] = (
                matched_ids[0]
            )

            evidence_item["source_ids"] = (
                matched_ids
            )

        else:

            evidence_item["source_id"] = (
                "UNKNOWN"
            )

            evidence_item["source_ids"] = []

    source_registry = {}

    for source in all_sources:

        source_id = source[
            "source_id"
        ]

        source_registry[
            source_id
        ] = {

            "title":
                source.get(
                    "title",
                    ""
                ),

            "url":
                source.get(
                    "url",
                    ""
                ),

            "task":
                source.get(
                    "task",
                    ""
                ),

            "domain":
                source.get(
                    "domain",
                    ""
                ),

            "score":
                source.get(
                    "score",
                    0
                ),

            "source_type":
                source.get(
                    "source_type",
                    "unknown"
                ),

            "quality_band":
                source.get(
                    "quality_band",
                    "unknown"
                ),

            "quality_reason":
                source.get(
                    "quality_reason",
                    ""
                )
        }
    valid_source_ids = set(
        source_registry.keys()
    )

    valid_evidence = []

    invalid_evidence = []


    for evidence_item in all_evidence:

        source_id = evidence_item.get(
            "source_id",
            "UNKNOWN"
        )

        if source_id in valid_source_ids:

            valid_evidence.append(
                evidence_item
            )

            continue


        invalid_evidence.append({

            "task":
                evidence_item.get(
                    "task",
                    ""
                ),

            "source_id":
                source_id,

            "url":
                evidence_item.get(
                    "url",
                    ""
                ),

            "reason":
                "No matching source found"
        })


    all_evidence = valid_evidence


    research_packet = ""


    for task_number, task in enumerate(
        tasks,
        start=1
    ):

        research_packet += (

            "\n\n"
            + "=" * 60
            + "\n"
            + f"TASK {task_number}\n"
            + "=" * 60
            + "\n"
            + task
            + "\n"
        )


        task_evidence = [

            item

            for item in all_evidence

            if item.get(
                "task",
                ""
            ) == task
        ]




        if not task_evidence:

            research_packet += (
                "\n"
                "No directly extracted evidence "
                "was available for this task.\n"
            )

            continue


        # ----------------------------------
        # Add evidence
        # ----------------------------------

        for item in task_evidence:

            source_id = item.get(
                "source_id",
                "UNKNOWN"
            )

            source_title = item.get(
                "source",
                ""
            )

            source_url = item.get(
                "url",
                ""
            )

            analysis = item.get(
                "analysis",
                ""
            )

            research_packet += (

                "\n"
                + f"SOURCE ID: {source_id}\n"

                + f"TITLE: {source_title}\n"

                + f"URL: {source_url}\n"

                + "EVIDENCE:\n"

                + analysis
                + "\n"
            )


    if all_evidence:

        answer_status = (
            "evidence_available"
        )

    else:

        answer_status = (
            "limited_evidence"
        )


    print(
        "\n[SOURCE QUALITY SUMMARY]"
    )

    for source_id, source in (
        source_registry.items()
    ):

        print(

            f"{source_id} | "

            f"{source.get('quality_band', 'unknown')} | "

            f"{source.get('source_type', 'unknown')} | "

            f"{source.get('domain', '')}"
        )


    print(
        "\n"
        + "=" * 60
    )

    print(
        "[RESEARCH] COMPLETE"
    )

    print(
        f"Unique sources: "
        f"{len(all_sources)}"
    )

    print(
        f"Valid evidence items: "
        f"{len(all_evidence)}"
    )

    print(
        f"Invalid evidence items: "
        f"{len(invalid_evidence)}"
    )

    print(
        f"Answer status: "
        f"{answer_status}"
    )

    print(
        "=" * 60
    )


    # ======================================
    # RETURN UPDATED STATE
    # ======================================

    return {

        **state,

        "sources":
            all_sources,

        "evidence":
            all_evidence,

        "research_results":
            research_results,

        "research_packet":
            research_packet,

        "source_registry":
            source_registry,

        "invalid_evidence":
            invalid_evidence,

        "answer_status":
            answer_status
    }
# WRITER AGENT


def writer_agent(state):

    print(
        "\n[WRITER] Writing complete research report..."
    )

    question = state.get(
        "question",
        ""
    )

    tasks = state.get(
        "tasks",
        []
    )

    research_packet = state.get(
        "research_packet",
        ""
    )

    previous_critique = state.get(
        "critique",
        ""
    )


    # ======================================
    # INTERNAL TASK CHECKLIST
    # ======================================

    task_checklist = ""

    for task in tasks:

        # Remove internal TASK labels
        clean_task = task

        for prefix in [
            "TASK 1:",
            "TASK 2:",
            "TASK 3:",
            "TASK 4:"
        ]:

            clean_task = clean_task.replace(
                prefix,
                ""
            )

        task_checklist += (
            "- "
            + clean_task.strip()
            + "\n"
        )




    prompt = f"""
You must produce the final report in this response.

Do not think aloud.
Do not return an empty response.
Do not describe what you would write.
Start directly with the report title.+

ORIGINAL USER QUESTION:

{question}


INTERNAL RESEARCH AREAS:

{task_checklist}


RESEARCH EVIDENCE:

{research_packet}


PREVIOUS CRITIC FEEDBACK:

{previous_critique}


Your task is to write ONE coherent, professional
research report answering the ORIGINAL USER QUESTION.

The internal research areas are only a checklist
to make sure that all important aspects are covered.

VERY IMPORTANT:

The internal research task structure MUST NOT
appear in the final report.

Do NOT write:

"Task 1"
"Task 2"
"Task 3"
"Task 4"

Do NOT write headings such as:

"Task 3: ..."
"Task 4: ..."

Do NOT say:

"This report focuses on Task 3 and Task 4."

Do NOT mention the research-planning process.

The reader should see a normal professional
research report, not the internal agent workflow.


========================================
REPORT STRUCTURE
========================================

Use a natural structure based on the topic.

For example:

# Title

## Introduction

## Main Findings

Use meaningful topic-based headings here.

For example:

## Real-Time Data Integration

## Predictive Failure Detection

## Drilling Parameter Optimization

## Environmental and Safety Applications

## Cross-Domain Analysis

## Limitations and Uncertainty

## Conclusion


Do NOT blindly use these example headings.
Create headings that actually match the
research evidence and original question.


========================================
CONTENT REQUIREMENTS
========================================

1. Answer the original user question directly.

2. Incorporate information from ALL relevant
   research areas.

3. Synthesize related findings instead of writing
   separate mini-reports.

4. Connect findings across different areas where
   the evidence supports the relationship.

5. Use only the supplied evidence.

6. Do not invent facts.

7. Do not invent statistics.

8. Do not invent dates.

9. Do not invent sources.

10. Do not invent URLs.

11. Do not introduce outside knowledge.

12. Clearly identify uncertainty and evidence gaps.

13. Do not force an answer where evidence is weak.


========================================
CITATIONS
========================================

Use only the supplied SOURCE IDs.

Examples:

[S001]
[S003]
[S006]

Never invent a SOURCE ID.

Every important factual claim should have a
relevant citation.

Do not create a References section.

The Python application will generate the
References section automatically.


========================================
TITLE
========================================

Create a concise professional title based on
the ORIGINAL USER QUESTION and the actual
research findings.

Do not mention:

- Task numbers
- Research task labels
- Internal agent workflow
- Planner
- Search Agent
- Reader Agent
- Critic Agent


========================================
INTRODUCTION
========================================

The introduction should explain:

- What the user asked
- Why the topic matters
- What major areas the report examines

Do not mention internal task numbers.

For example:

"This report examines the application of machine
learning across wellbore stability, production
forecasting, and drilling optimization, based on
the retrieved research evidence."

Do NOT say:

"This report covers Task 3 and Task 4."


========================================
FINAL CHECK
========================================

Before returning the report, verify internally:

[ ] The original question is answered.

[ ] All relevant research areas are represented.

[ ] Internal task numbers do not appear.

[ ] The words "Task 1", "Task 2", "Task 3",
    and "Task 4" do not appear as report headings.

[ ] The report reads like a professional
    standalone research report.

[ ] Major factual claims have SOURCE IDs.

[ ] No unsupported facts were added.
"""


    # ======================================
    # CALL LLM
    # ======================================

    try:

        response = llm.invoke(
            prompt
        )

        draft = response.content.strip()
        print(
    f"[WRITER DEBUG] Draft length: {len(draft)}"
)

        print(
    f"[WRITER DEBUG] Draft preview:\n"
    f"{draft[:1000]}"
)
        if not draft:

            draft = (
        "The research pipeline did not generate "
        "a usable draft. Please retry the research query."
    )
        return {

            **state,

            "draft":
                draft
        }

    except Exception as e:

        print(
            f"[WRITER ERROR] {e}"
        )

        return {

            **state,

            "draft":
        "The writer encountered an error while generating the report.",

    "answer_status":
        "writer_error"
        }

# CRITIC AGENT


def critic_agent(state):


    print(
        "\n[CRITIC] Checking report..."
    )

    # ======================================
    # GET STATE
    # ======================================

    question = state.get(
        "question",
        ""
    )

    tasks = state.get(
        "tasks",
        []
    )

    research_packet = state.get(
        "research_packet",
        ""
    )

    evidence = state.get(
        "evidence",
        []
    )

    source_registry = state.get(
        "source_registry",
        {}
    )

    draft = state.get(
        "draft",
        ""
    )

    revision_count = state.get(
        "revision_count",
        0
    )

    print(
    f"[CRITIC DEBUG] Draft length: {len(draft)}"
)

    print(
    f"[CRITIC DEBUG] Evidence count: {len(evidence)}"
)

    print(
    f"[CRITIC DEBUG] Research packet length: "
    f"{len(research_packet)}"
)

    def compact_text(text,max_chars):
        if not text:
            return ""

        if len(text) <= max_chars:
            return text

        half = max_chars // 2

        return (
        text[:half]
        + "\n\n...[CONTENT TRUNCATED FOR SPEED]...\n\n"
        + text[-half:]
    )
    research_packet_for_critic = compact_text(
    research_packet,
    7000
)

    draft_for_critic = compact_text(
    draft,
    6000
)
    
    # ======================================
    # FIND CITATIONS IN DRAFT
    # ======================================

    cited_ids = set(
        re.findall(
            r"\[S\d{3}\]",
            draft
        )
    )

    # Convert [S001] -> S001
    cited_ids = {
        citation.strip("[]")
        for citation in cited_ids
    }


    # ======================================
    # VALID SOURCE IDS
    # ======================================

    valid_source_ids = set(
        source_registry.keys()
    )


    invalid_citations = []

    for source_id in cited_ids:

        if source_id not in valid_source_ids:

            invalid_citations.append(
                source_id
            )



    task_source_ids = {}

    for task in tasks:

        task_source_ids[task] = set()


    for item in evidence:

        task = item.get(
            "task",
            ""
        )

        source_id = item.get(
            "source_id",
            ""
        )

        if task in task_source_ids:

            if source_id:

                task_source_ids[
                    task
                ].add(
                    source_id
                )


    missing_task_citations = []

    for task in tasks:

        available_ids = task_source_ids.get(
            task,
            set()
        )

        matching_ids = (
            available_ids.intersection(
                cited_ids
            )
        )

        if not matching_ids:

            missing_task_citations.append(
                task
            )

    automatic_problems = []


    # Invalid source IDs

    if invalid_citations:

        automatic_problems.append(
            "Invalid citation IDs: "
            + ", ".join(
                sorted(invalid_citations)
            )
        )


    # Missing citations for tasks

    if missing_task_citations:

        for task in missing_task_citations:

            automatic_problems.append(
                "No valid citation found "
                "for research task: "
                + task
            )


    # Empty report

    if not draft.strip():

        automatic_problems.append(
            "Writer produced an empty report."
        )


    print(
        "\n[CRITIC] Programmatic validation"
    )

    print(
        f"Valid source IDs: "
        f"{len(valid_source_ids)}"
    )

    print(
        f"Citations found: "
        f"{sorted(cited_ids)}"
    )

    print(
        f"Invalid citations: "
        f"{sorted(invalid_citations)}"
    )

    print(
        f"Tasks missing citations: "
        f"{len(missing_task_citations)}"
    )

    task_checklist = ""

    for index, task in enumerate(
        tasks,
        start=1
    ):

        task_checklist += (
            f"TASK {index}: {task}\n"
        )


    # ======================================
    # LLM CRITIC PROMPT
    # ======================================

    prompt = f"""
You are the Critic Agent in a deep research system.

Evaluate the Writer's report using ONLY the supplied evidence.

QUESTION:
{question}

RESEARCH TASKS:
{task_checklist}

EVIDENCE:
{research_packet_for_critic}

DRAFT:
{draft_for_critic}

CITATION CHECK:
Valid source IDs: {sorted(valid_source_ids)}
Citations found: {sorted(cited_ids)}
Invalid citations: {sorted(invalid_citations)}
Tasks without valid citations: {missing_task_citations}

CHECK ONLY:

1. Does the report answer the original question?
2. Are all four research tasks reasonably covered?
3. Are important factual claims supported by the evidence?
4. Are citations valid and relevant?
5. Are there unsupported facts, statistics, dates, sources, or URLs?
6. Is the conclusion supported by the evidence?

Do NOT perform additional research.
Do NOT introduce outside knowledge.
Do NOT invent facts.

OUTPUT ONLY:

DECISION=APPROVED

or

DECISION=REVISE

After DECISION=REVISE, give only a few concise problems.
"""


    # ======================================
    # CALL LLM
    # ======================================
    # if automatic_problems:
    #     problems_text = "\n".join(
    #     "- " + problem
    #     for problem in automatic_problems
    # )

    # critique = (
    #     "DECISION=REVISE\n\n"
    #     "AUTOMATIC VALIDATION ERRORS:\n"
    #     + problems_text
    # )

    # approved = False

    # new_revision_count = revision_count + 1

    # print(
    #     "\n[CRITIC] Automatic validation failed."
    # )

    # print(
    #     "[CRITIC] Skipping LLM call."
    # )

    # return {
    #     **state,
    #     "critique": critique,
    #     "approved": approved,
    #     "revision_count": new_revision_count
    # }
    try:

        response = llm.invoke(
            prompt
        )

        critique = (
            response.content
            .strip()
        )

    except Exception as e:

        print(
            f"[CRITIC ERROR] {e}"
        )

        critique = (
            "DECISION=REVISE\n"
            "Critic failed to evaluate the report."
        )


    

    first_line = ""

    for line in critique.splitlines():

        line = line.strip()

        # Remove markdown code fences
        line = line.replace(
            "```",
            ""
        ).strip()

        if line:

            first_line = line.upper()

            break


    approved = (
        first_line
        == "DECISION=APPROVED"
    )


    # ======================================
    # AUTOMATIC CHECK OVERRIDES APPROVAL
    # ======================================

    if automatic_problems:

        approved = False

        problems_text = "\n".join(
            "- " + problem
            for problem in automatic_problems
        )

        critique = (
            "DECISION=REVISE\n\n"
            "AUTOMATIC VALIDATION ERRORS:\n"
            + problems_text
            + "\n\n"
            + critique
        )


    # ======================================
    # REVISION COUNT
    # ======================================
    new_revision_count = revision_count
    if not approved:
        new_revision_count +=1


    # ======================================
    # STATUS
    # ======================================

    if approved:

        print(
            "\n[CRITIC] APPROVED"
        )

    else:

        print(
            "\n[CRITIC] REVISE"
        )

        print(
            f"[CRITIC] Revision count: "
            f"{new_revision_count}"
        )


    # ======================================
    # RETURN UPDATED STATE
    # ======================================

    return {

        **state,

        "critique":
            critique,

        "approved":
            approved,

        "revision_count":
            new_revision_count
    }
def validate_citations(
    draft,
    source_registry
):

    # Find citations like [S001]
    cited_ids = set(
        re.findall(
            r"\[S\d{3}\]",
            draft
        )
    )

    valid_ids = set(
        source_registry.keys()
    )

    invalid_ids = []

    for citation in cited_ids:

        source_id = citation.strip(
            "[]"
        )

        if source_id not in valid_ids:

            invalid_ids.append(
                source_id
            )

    return {
        "cited_ids":
            sorted(cited_ids),

        "invalid_ids":
            sorted(invalid_ids),

        "valid":
            len(invalid_ids) == 0
    }

def validate_evidence_links(
    evidence,
    source_registry
):

    valid_source_ids = set(
        source_registry.keys()
    )

    valid_evidence = []

    invalid_evidence = []

    for item in evidence:

        source_id = item.get(
            "source_id",
            ""
        )

        url = item.get(
            "url",
            ""
        )

        # ----------------------------------
        # Check source ID
        # ----------------------------------

        if source_id not in valid_source_ids:

            invalid_evidence.append({

                "reason":
                    "Unknown source ID",

                "source_id":
                    source_id,

                "url":
                    url
            })

            continue


        # ----------------------------------
        # Check URL
        # ----------------------------------

        registered_url = (
            source_registry[
                source_id
            ]["url"]
        )

        if url != registered_url:

            invalid_evidence.append({

                "reason":
                    "Evidence URL does not match "
                    "registered source URL",

                "source_id":
                    source_id,

                "url":
                    url
            })

            continue


        valid_evidence.append(
            item
        )


    return {
        "valid_evidence":
            valid_evidence,

        "invalid_evidence":
            invalid_evidence
    }




