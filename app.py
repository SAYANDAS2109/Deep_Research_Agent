import streamlit as st

from main import run_research_stream


st.set_page_config(
    page_title="Deep Research Agent",
    page_icon="🔎",
    layout="wide"
)

st.warning("This is not much optimized so final report can take upto 6-7 minutes to generate.\n In further updates the app will be more optimized!")
st.warning("To get a good and optimum answer write your query detailed")
st.info("Please wait for some time to get the results")


if "result" not in st.session_state:

    st.session_state.result = None


if "research_running" not in st.session_state:

    st.session_state.research_running = False




st.title(
    "🔎 Deep Research Agent"
)

st.write(
    "Ask a complex question and let the "
    "research system plan, search, read, "
    "write, and critique the answer."
)




with st.sidebar:

    st.header(
        "⚙️ Research System"
    )

    st.write(
        "Multi-agent deep research pipeline"
    )

    st.divider()

    st.write(
        "**Agents**"
    )

    st.write(
        "🧠 Planner"
    )

    st.write(
        "🔎 Search Agent"
    )

    st.write(
        "📖 Reader Agent"
    )

    st.write(
        "✍️ Writer Agent"
    )

    st.write(
        "🧐 Critic Agent"
    )

    st.divider()

    st.caption(
        "LLM: Local Ollama"
    )

    st.caption(
        "Web Search: Tavily"
    )




st.subheader(
    "Research Question"
)

question = st.text_area(

    "Enter your complex research question",

    placeholder=(
        "Example: How is artificial intelligence "
        "transforming petroleum drilling operations?"
    ),

    height=150,

    key="question_input"
)




col1, col2 = st.columns(2)


with col1:

    start_button = st.button(

        "🚀 Start Research",

        type="primary",

        use_container_width=True
    )


with col2:

    clear_button = st.button(

        "🗑️ Clear Research",

        use_container_width=True
    )




if clear_button:

    st.session_state.result = None

    st.session_state.research_running = False

    st.rerun()




if start_button:

    if not question.strip():

        st.warning(
            "Please enter a research question."
        )

    else:

        st.session_state.research_running = True

        st.subheader(
            "🔄 Research Progress"
        )

        progress_placeholder = st.empty()

        def update_progress(
            node_name,
            state
        ):

            if node_name == "planner":

                tasks = state.get(
                    "tasks",
                    []
                )

                progress_placeholder.markdown(
                    f"""
### 🔄 Planning

✅ Planner completed

**{len(tasks)} research tasks created**

---

⏳ Researching web sources...
"""
                )

            elif node_name == "research":

                tasks = state.get(
                    "tasks",
                    []
                )

                sources = state.get(
                    "sources",
                    []
                )

                evidence = state.get(
                    "evidence",
                    []
                )

                progress_placeholder.markdown(
                    f"""
### 🔄 Research

✅ Planner completed

✅ **{len(tasks)} research tasks**

✅ **{len(sources)} sources found**

✅ **{len(evidence)} evidence items created**

---

⏳ Writing research report...
"""
                )

            elif node_name == "writer":

                progress_placeholder.markdown(
                    """
### 🔄 Writing

✅ Planner completed

✅ Research completed

✅ Evidence collected

✅ **Writer generated the report**

---

⏳ Critic is evaluating the report...
"""
                )


            elif node_name == "critic":

                revision = state.get(
                    "revision_count",
                    0
                )

                approved = state.get(
                    "approved",
                    False
                )

                if approved:

                    critic_status = (
                        "✅ Report approved"
                    )

                else:

                    critic_status = (
                        "🔄 Report requires revision"
                    )

                progress_placeholder.markdown(
                    f"""
### 🧐 Critic Evaluation

✅ Planner completed

✅ Research completed

✅ Report written

{critic_status}

**Revision cycle:** {revision}
"""
                )


        # ----------------------------------
        # RUN LANGGRAPH
        # ----------------------------------

        try:

            with st.spinner(
                "Deep Research Agent is working..."
            ):

                result = run_research_stream(
                    question,
                    update_progress
                )


            # Save result
            st.session_state.result = result

            st.session_state.research_running = False


            progress_placeholder.success(
                "✅ Research completed successfully."
            )

        except Exception as e:

            st.session_state.research_running = False

            progress_placeholder.error(
                "❌ Research failed."
            )

            st.error(
                f"Error: {e}"
            )


if st.session_state.result:

    result = st.session_state.result

    

    answer_status = result.get(
        "answer_status",
        ""
    )

    if answer_status == "evidence_available":

        st.success(
            "🟢 Evidence-backed research completed."
        )

    elif answer_status == "limited_evidence":

        st.warning(
            "🟡 The answer was generated with "
            "limited retrieved evidence."
        )

    st.divider()


    st.header(
        "📄 Final Research Report"
    )

    final_report = result.get(
        "final_report",
        ""
    )


    if final_report:

        st.markdown(
            final_report
        )

    else:

        st.warning(
            "No final report was generated."
        )



    if final_report:

        st.subheader(
            "⬇️ Download Report"
        )

        download_col1, download_col2 = (
            st.columns(2)
        )


        with download_col1:

            st.download_button(

                label="⬇️ Download Markdown",

                data=final_report,

                file_name=(
                    "deep_research_report.md"
                ),

                mime="text/markdown",

                use_container_width=True
            )


        with download_col2:

            st.download_button(

                label="📝 Download TXT",

                data=final_report,

                file_name=(
                    "deep_research_report.txt"
                ),

                mime="text/plain",

                use_container_width=True
            )


    tasks = result.get(
        "tasks",
        []
    )

    if tasks:

        st.divider()

        with st.expander(
            "🔍 Research Tasks",
            expanded=False
        ):

            for index, task in enumerate(
                tasks,
                start=1
            ):

                st.markdown(
                    f"**Task {index}**"
                )

                st.write(
                    task
                )



    source_registry = result.get(
        "source_registry",
        {}
    )

    if source_registry:

        st.divider()

        with st.expander(
            f"📚 Sources ({len(source_registry)})",
            expanded=False
        ):

            for source_id, source in (
                source_registry.items()
            ):

                st.markdown(
                    f"### {source_id}"
                )

                st.write(
                    source.get(
                        "title",
                        "Untitled source"
                    )
                )

                # Source URL
                url = source.get(
                    "url",
                    ""
                )

                if url:

                    st.markdown(
                        f"[🔗 Open Source]({url})"
                    )

                # Metadata
                metadata_col1, metadata_col2 = (
                    st.columns(2)
                )


                with metadata_col1:

                    st.write(
                        "**Source Type:** "
                        + source.get(
                            "source_type",
                            "unknown"
                        )
                    )


                with metadata_col2:

                    st.write(
                        "**Quality:** "
                        + source.get(
                            "quality_band",
                            "unknown"
                        )
                    )


                domain = source.get(
                    "domain",
                    ""
                )

                if domain:

                    st.write(
                        f"**Domain:** {domain}"
                    )


                score = source.get(
                    "score",
                    0
                )

                if score:

                    st.write(
                        f"**Search Score:** "
                        f"{score:.3f}"
                    )


                reason = source.get(
                    "quality_reason",
                    ""
                )

                if reason:

                    st.caption(
                        reason
                    )


                st.divider()

    critique = result.get(
        "critique",
        ""
    )

    if critique:

        st.divider()

        with st.expander(
            "🧐 Critic Evaluation",
            expanded=False
        ):

            st.markdown(
                critique
            )


    st.divider()

    st.subheader(
        "📊 Research Statistics"
    )

    sources = result.get(
        "sources",
        []
    )

    evidence = result.get(
        "evidence",
        []
    )

    revision_count = result.get(
        "revision_count",
        0
    )

    stat1, stat2, stat3 = st.columns(3)


    with stat1:

        st.metric(
            "Research Tasks",
            len(tasks)
        )


    with stat2:

        st.metric(
            "Sources",
            len(sources)
        )


    with stat3:

        st.metric(
            "Evidence Items",
            len(evidence)
        )


    st.caption(
        f"Critic revision cycles: "
        f"{revision_count}"
    )

