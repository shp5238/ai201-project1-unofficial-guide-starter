"""
Milestone 5 — Query interface
University Career Assistant (RAG)

A Gradio UI over the grounded `ask()` pipeline in rag.py:
  question  ->  retrieve top-5 chunks  ->  Groq llama-3.3-70b (grounded)  ->  answer + sources

Run:
    python app.py
then open the local URL it prints (default http://127.0.0.1:7860).
"""

import gradio as gr

from rag import ask, DEFAULT_TOP_K

EXAMPLES = [
    "What are some common skills in Data Science student resumes?",
    "For a job interview, what are some tips for my thank you note?",
    "I want to network but don't know where to start. What are some USD-specific resources?",
    "Why should I use AI in my job preparation process?",
    "How do I find salary and job outlook information?",
]


def answer_question(question: str):
    """Run one question through the RAG pipeline and format the UI outputs."""
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", "", ""

    try:
        result = ask(question, k=DEFAULT_TOP_K)
    except Exception as exc:
        return f"⚠️ Error: {exc}", "", ""

    answer = result["answer"]

    # Sources — attached programmatically from the retrieved chunks' metadata.
    if result["sources"]:
        sources_md = "**Sources**\n" + "\n".join(
            f"- {s}" for s in result["sources"])
    else:
        sources_md = "_No sources — the question is outside the available documents._"

    # Recommended website links (only shown when the question matches their topics).
    if result["resources"]:
        resources_md = "**You may also find these helpful**\n" + "\n".join(
            f"- [{r['name']}]({r['url']}) — {r['description']}"
            for r in result["resources"])
    else:
        resources_md = ""

    return answer, sources_md, resources_md


with gr.Blocks(title="USD Career Assistant") as demo:
    gr.Markdown(
        "# 🎓 University of San Diego — Career Assistant\n"
        "Ask about resumes, interviews, networking, LinkedIn, internships, and "
        "using AI in your career search. Answers are grounded **only** in official "
        "USD career-center documents; if the documents don't cover your question, "
        "the assistant will say so."
    )

    with gr.Row():
        question = gr.Textbox(
            label="Your question",
            placeholder="e.g. What are some tips for my interview thank-you note?",
            lines=2,
            scale=4,
        )
    with gr.Row():
        submit = gr.Button("Ask", variant="primary")
        clear = gr.Button("Clear")

    answer = gr.Markdown(label="Answer")
    sources = gr.Markdown()
    resources = gr.Markdown()

    gr.Examples(examples=EXAMPLES, inputs=question)

    submit.click(answer_question, inputs=question,
                 outputs=[answer, sources, resources])
    question.submit(answer_question, inputs=question,
                    outputs=[answer, sources, resources])
    clear.click(lambda: ("", "", "", ""), outputs=[question, answer, sources, resources])


if __name__ == "__main__":
    demo.launch()
