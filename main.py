from langgraph.graph import StateGraph, END

from agents import (
    planner_agent,
    parallel_research_agent,
    writer_agent,
    critic_agent
)


# ==========================================
# BUILD REFERENCES
# ==========================================

def build_references(source_registry):

    references = []

    for source_id, source in source_registry.items():

        references.append(
            f"[{source_id}] "
            f"{source['title']} "
            f"— {source['url']}"
        )

    return "\n".join(references)


# ==========================================
# CRITIC ROUTER
# ==========================================

def critic_router(state):

    approved = state.get(
        "approved",
        False
    )

    revision_count = state.get(
        "revision_count",
        0
    )

    if approved:
        return "end"

    if revision_count < 1:
        return "writer"

    return "end"


# ==========================================
# CREATE GRAPH
# ==========================================

graph = StateGraph(dict)


# ==========================================
# ADD NODES
# ==========================================

graph.add_node(
    "planner",
    planner_agent
)

graph.add_node(
    "research",
    parallel_research_agent
)

graph.add_node(
    "writer",
    writer_agent
)

graph.add_node(
    "critic",
    critic_agent
)


# ==========================================
# GRAPH FLOW
# ==========================================

graph.set_entry_point(
    "planner"
)

graph.add_edge(
    "planner",
    "research"
)

graph.add_edge(
    "research",
    "writer"
)

graph.add_edge(
    "writer",
    "critic"
)


# ==========================================
# CRITIC ROUTING
# ==========================================

graph.add_conditional_edges(

    "critic",

    critic_router,

    {
        "end": END,
        "writer": "writer"
    }
)


# ==========================================
# COMPILE
# ==========================================

app = graph.compile()


# ==========================================
# RUN RESEARCH
# ==========================================

def run_research(question):

    initial_state = {

        "question":
            question,

        "tasks":
            [],

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

        "draft":
            "",

        "critique":
            "",

        "approved":
            False,

        "revision_count":
            0,

        "final_report":
            ""
    }

    result = app.invoke(
        initial_state
    )


    # ======================================
    # GET REPORT
    # ======================================

    draft = result.get(
        "draft",
        "No report generated."
    )


    # ======================================
    # GET SOURCES
    # ======================================

    source_registry = result.get(
        "source_registry",
        {}
    )


    references = build_references(
        source_registry
    )


    # ======================================
    # FINAL REPORT
    # ======================================

    final_report = (

        draft

        + "\n\n"

        + "=" * 60

        + "\nREFERENCES\n"

        + "=" * 60

        + "\n"

        + references
    )


    result["final_report"] = (
        final_report
    )


    return result

def run_research_stream(
    question,
    progress_callback=None
):

    initial_state = {

        "question":
            question,

        "tasks":
            [],

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

        "draft":
            "",

        "critique":
            "",

        "approved":
            False,

        "revision_count":
            0,

        "final_report":
            ""
    }

    final_state = initial_state.copy()


    # ======================================
    # STREAM GRAPH UPDATES
    # ======================================

    for update in app.stream(
        initial_state,
        stream_mode="updates"
    ):

        for node_name, node_output in (
            update.items()
        ):

            # ------------------------------
            # Merge state
            # ------------------------------

            if isinstance(
                node_output,
                dict
            ):

                final_state.update(
                    node_output
                )


            # ------------------------------
            # Notify Streamlit
            # ------------------------------

            if progress_callback:

                progress_callback(
                    node_name,
                    final_state
                )


    # ======================================
    # BUILD FINAL REPORT
    # ======================================

    draft = final_state.get(
        "draft",
        "No report generated."
    )

    source_registry = final_state.get(
        "source_registry",
        {}
    )

    references = build_references(
        source_registry
    )

    final_report = (

        draft

        + "\n\n"

        + "=" * 60

        + "\nREFERENCES\n"

        + "=" * 60

        + "\n"

        + references
    )

    final_state["final_report"] = (
        final_report
    )

    return final_state
# ==========================================
# CLI MODE
# ==========================================

if __name__ == "__main__":

    question = input(
        "\nEnter your complex research question:\n> "
    )

    result = run_research(
        question
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "FINAL RESEARCH REPORT"
    )

    print(
        "=" * 60
    )

    print(
        result["final_report"]
    )


    print(
        "\n"
        + "=" * 60
    )

    print(
        "CRITIC"
    )

    print(
        "=" * 60
    )

    print(
        result.get(
            "critique",
            ""
        )
    )