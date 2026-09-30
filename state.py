def create_initial_state(question):
    return {
        "question": question,

        "tasks": [],

        "sources": [],

        "evidence": [],

        "draft": "",

        "critique": "",

        "approved": False,

        "final_report": "",
        "answer_status":""
    }