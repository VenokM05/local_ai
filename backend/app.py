"""Flask app exposing the smallest end-to-end local RAG proof (PRD section 14).

Endpoints (all JSON, curl-friendly, no UI yet):
  GET    /api/health              -> local model availability (FR-01/FR-08)
  POST   /api/documents           -> ingest a PDF/TXT into text_chunks (FR-02/FR-03)
  GET    /api/documents           -> list indexed documents (FR-02)
  DELETE /api/documents/<id>      -> remove a document + its chunks (FR-02)
  POST   /api/ask                 -> retrieve -> local model -> grounded answer
                                     + citation badges + 'not enough info' fallback
                                     (FR-04/FR-05/FR-08)
  GET    /api/checklist           -> preparedness items (FR-06)
  POST   /api/checklist           -> add a custom item (FR-06)
  PATCH  /api/checklist/<id>      -> mark done/undo (FR-06)
  DELETE /api/checklist/<id>      -> remove an item (FR-06)
  GET    /api/chat                -> recent local Q&A history (FR-07)
  DELETE /api/chat                -> clear chat history (FR-07)

The server binds to loopback only (PRD section 7 implementation note).
"""

from __future__ import annotations

import json
import os
import tempfile

from flask import Flask, jsonify, request, send_from_directory

import config
import db
import ingest
import llm
import retrieval

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_BYTES

DISCLAIMER = (
    "RescueDesk AI is a preparedness reference tool, not an emergency dispatch "
    "or live alert service. Follow current instructions from official authorities."
)


def _snippets(passages):
    """Build citation badges strictly from retrieval metadata (PRD section 15)."""
    badges = []
    for p in passages:
        chunk = p["chunk"]
        content = chunk["content"]
        badges.append({
            "document": chunk["doc_name"],
            "page": chunk.get("page"),
            "section": chunk.get("section"),
            "snippet": content[:280] + ("…" if len(content) > 280 else ""),
            "relevance": round(p["score"], 3),
        })
    return badges


@app.route("/")
def index():
    """Serve the single-page front-end (PRD section 6)."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    available = llm.model_available()
    return jsonify({
        "status": "ok",
        "model": config.OLLAMA_MODEL,
        "runtime": config.OLLAMA_BASE_URL,
        "model_available": available,
        "note": "Model availability detected; run an offline test before "
                "claiming verified offline operation (PRD FR-01)." if available
                else "Local model not reachable. Install Ollama and pull the "
                     "model, or set RESCUEDESK_MODEL.",
    }), (200 if available else 503)


@app.route("/api/documents", methods=["POST"])
def ingest_document():
    """Accept either {"path": "/abs/path.pdf"} or a multipart 'file' upload."""
    db.init_db()
    tmp_path = None
    try:
        if "file" in request.files:
            upload = request.files["file"]
            ext = os.path.splitext(upload.filename)[1].lower()
            if ext not in config.ALLOWED_EXTENSIONS:
                return jsonify({"error": f"Unsupported file type: {ext}"}), 400
            fd, tmp_path = tempfile.mkstemp(suffix=ext)
            os.close(fd)
            upload.save(tmp_path)
            name = upload.filename
            source = None
        else:
            data = request.get_json(silent=True) or {}
            path = data.get("path")
            if not path or not os.path.isfile(path):
                return jsonify({"error": "Provide 'path' to a local file or "
                                         "upload a 'file'."}), 400
            ext = os.path.splitext(path)[1].lower()
            if ext not in config.ALLOWED_EXTENSIONS:
                return jsonify({"error": f"Unsupported file type: {ext}"}), 400
            tmp_path = path  # read directly from disk (bundled reference docs)
            name = data.get("name") or os.path.basename(path)
            source = path if ext == ".pdf" or ext in (".txt", ".md") else None

        chunks = ingest.extract(tmp_path)
        if not chunks:
            return jsonify({"error": "No text could be extracted."}), 422
        doc_id = db.insert_document(name, os.path.splitext(tmp_path)[1].lstrip("."),
                                    source, chunks)
        return jsonify({
            "id": doc_id,
            "name": name,
            "chunks": len(chunks),
            "message": "Extracted and indexed locally.",
        }), 201
    except ingest.ExtractionError as exc:
        return jsonify({"error": str(exc)}), 422
    finally:
        # Only remove temp files we created for uploads, never a user's path.
        if "file" in request.files and tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route("/api/documents", methods=["GET"])
def list_documents():
    db.init_db()
    return jsonify({"documents": db.list_documents()})


@app.route("/api/documents/<int:doc_id>", methods=["DELETE"])
def delete_document(doc_id: int):
    db.init_db()
    removed = db.delete_document(doc_id)
    return jsonify({"removed": removed, "id": doc_id})


@app.route("/api/ask", methods=["POST"])
def ask():
    db.init_db()
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Field 'question' is required."}), 400

    corpus = db.get_all_chunks()
    passages = retrieval.retrieve(question, corpus)

    # Fallback path: no sufficiently relevant passage -> do NOT invent an answer
    # and do NOT call the model (PRD FR-04 / section 15). Still logged locally
    # so the exchange is part of the on-device history (PRD FR-07).
    if not passages:
        fallback = ("The available documents do not contain enough information "
                    "to answer this.")
        db.add_chat_message(question, fallback, False, "[]")
        return jsonify({
            "question": question,
            "answer": fallback,
            "supported": False,
            "citations": [],
            "disclaimer": DISCLAIMER,
        })

    # Retrieval succeeded but the local model is not reachable -> clear, honest
    # error rather than a silent or cloud fallback (PRD FR-08).
    if not llm.model_available():
        return jsonify({
            "question": question,
            "error": "Local model unavailable. Install Ollama and pull "
                     f"'{config.OLLAMA_MODEL}', then retry.",
            "retrieved_passages": len(passages),
            "citations": _snippets(passages),
        }), 503

    try:
        raw = llm.answer_question(question, [p["chunk"] for p in passages])
    except llm.ModelUnavailableError as exc:
        return jsonify({"question": question, "error": str(exc)}), 503

    insufficient = llm.INSUFFICIENT_MARKER in raw.upper()
    answer = ("The available documents do not contain enough information to "
              "answer this.") if insufficient else raw
    citations = [] if insufficient else _snippets(passages)

    # Persist the exchange locally (PRD FR-07). Answer + citations stay on-device.
    db.add_chat_message(question, answer, not insufficient,
                        json.dumps(citations))

    return jsonify({
        "question": question,
        "answer": answer,
        "supported": not insufficient,
        "citations": citations,
        "disclaimer": DISCLAIMER,
    })


# --- Checklist (PRD FR-06) -------------------------------------------------
@app.route("/api/checklist", methods=["GET"])
def get_checklist():
    db.init_db()
    return jsonify({"items": db.list_checklist(),
                    "note": "General preparedness starting point; adapt to "
                            "your household and follow official guidance."})


@app.route("/api/checklist", methods=["POST"])
def post_checklist():
    db.init_db()
    data = request.get_json(silent=True) or {}
    label = (data.get("label") or "").strip()
    category = (data.get("category") or "General").strip()
    if not label:
        return jsonify({"error": "Field 'label' is required."}), 400
    item_id = db.add_checklist_item(category, label)
    return jsonify({"id": item_id, "category": category, "label": label,
                    "done": False}), 201


@app.route("/api/checklist/<int:item_id>", methods=["PATCH"])
def patch_checklist(item_id: int):
    db.init_db()
    data = request.get_json(silent=True) or {}
    if "done" not in data:
        return jsonify({"error": "Field 'done' (true/false) is required."}), 400
    updated = db.set_checklist_done(item_id, bool(data["done"]))
    if not updated:
        return jsonify({"error": "No such checklist item."}), 404
    return jsonify({"id": item_id, "done": bool(data["done"])})


@app.route("/api/checklist/<int:item_id>", methods=["DELETE"])
def remove_checklist(item_id: int):
    db.init_db()
    removed = db.delete_checklist_item(item_id)
    return jsonify({"removed": removed, "id": item_id})


# --- Chat history (PRD FR-07) ---------------------------------------------
@app.route("/api/chat", methods=["GET"])
def get_chat():
    db.init_db()
    return jsonify({"messages": db.list_chat()})


@app.route("/api/chat", methods=["DELETE"])
def delete_chat():
    db.init_db()
    cleared = db.clear_chat()
    return jsonify({"cleared": cleared})


def main():
    db.init_db()
    # Loopback bind by default (PRD section 7). Do not set 0.0.0.0 for the demo.
    app.run(host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    main()
