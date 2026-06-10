"""
Milestone 5 — Query interface (custom web UI)
University Career Assistant (RAG)

A small Flask server over the grounded `ask()` pipeline in rag.py:
  question  ->  retrieve top-5 chunks  ->  Groq llama-3.3-70b (grounded)  ->  answer + sources

It serves a single-page chat UI (templates/index.html + static/) and one JSON
endpoint, POST /api/ask, that the page calls with fetch().

Run:
    python app.py
then open http://127.0.0.1:7860 in your browser.
"""

from flask import Flask, jsonify, render_template, request

from rag import ask, DEFAULT_TOP_K, EVAL_QUESTIONS

app = Flask(__name__)


@app.route("/")
def index():
    # The example questions come straight from rag.EVAL_QUESTIONS so the chips
    # in the UI stay in sync with the planning.md evaluation plan.
    return render_template("index.html", examples=EVAL_QUESTIONS)


@app.route("/api/ask", methods=["POST"])
def api_ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    try:
        result = ask(question, k=DEFAULT_TOP_K)
    except Exception as exc:  # surface config/runtime errors to the UI
        return jsonify({"error": str(exc)}), 500

    # Only return what the UI renders. Sources are computed programmatically in
    # ask() from chunk metadata (never authored by the model).
    return jsonify({
        "answer": result["answer"],
        "sources": result["sources"],
        "resources": result["resources"],
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7860, debug=False)
