# RescueDesk AI — Architecture Design

**Scope:** the MVP local RAG backend in [`backend/`](file:///Applications/XAMPP/xamppfiles/htdocs/local_ai/backend). No UI yet — the system is a loopback HTTP/JSON service you can curl.
**Cross-cutting principle:** every core step (extraction, retrieval, inference, storage) runs **on-device with no cloud AI dependency** (PRD FR-04, §7, §15).

---

## 1. System overview

```
                         ┌──────────────────────── On-device (Windows / macOS) ───────────────────────┐
  curl / client          │                                                                              │
  ───────POST /api/ask──►│  Flask app (app.py)                                                        │
                         │    │                                                                        │
                         │    ├─1─► retrieval.py  (BM25 over corpus) ──┐                              │
                         │    │                                        │ top-K passages + scores      │
                         │    │                                        ▼                              │
                         │    ├─2─► llm.py ──HTTP──► Ollama (127.0.0.1:11434)  local LLM              │
                         │    │        grounded prompt ◄── retrieved passages                         │
                         │    │                                                                       │
                         │    ├─3─► builds citation badges from RETRIEVAL metadata (not the model)   │
                         │    └─4─► returns JSON {answer, supported, citations[], disclaimer}         │
                         │                                                                            │
                         │  SQLite (db.py)  ◄── ingest.py (PyMuPDF/TXT) writes text_chunks           │
                         └────────────────────────────────────────────────────────────────────────────┘
```

Everything below the client arrow stays local. The only external HTTP call is Flask → **Ollama on the same machine's loopback**, which is not the internet and works offline.

---

## 2. Component responsibilities

| Module | File | Responsibility | PRD |
|---|---|---|---|
| Config | `config.py` | Single source of tunables + env overrides; loopback defaults | §7, §10 |
| Persistence | `db.py` | SQLite schema + CRUD; `documents`, `text_chunks`; FK cascade | FR-02/03/07 |
| Ingestion | `ingest.py` | PyMuPDF PDF text + TOC→section mapping; TXT/MD; chunking; scanned-PDF error | FR-03 |
| Retrieval | `retrieval.py` | Pure-Python Okapi **BM25**, tokenize/stop-words, score threshold | §8 |
| LLM client | `llm.py` | Ollama `/api/generate`, context-constrained prompt, `INSUFFICIENT_INFORMATION` marker, health probe | FR-04/08 |
| API | `app.py` | Flask routes, citation-badge assembly, fallback + error handling | FR-05/08 |

**Design note:** `retrieval.py` is pure Python (no `rank_bm25`/sklearn dependency) so the retrieval step is trivially provable as offline and portable.

---

## 3. Data model

```
documents(id PK, name, source_path, media_type, created_at)

text_chunks(id PK, document_id FK→documents ON DELETE CASCADE,
            page INTEGER NULL, section TEXT NULL, content TEXT)
  index: idx_chunks_document(document_id)
```

- Chunking: `CHUNK_MAX_CHARS` (default 700) with `CHUNK_OVERLAP_CHARS` (120) overlap; each chunk retains `page` + `section` metadata so citations are checkable against the source (FR-05).
- Removing a document cascades and clears its indexed content (FR-02 acceptance criterion).

---

## 4. Request flows

### 4.1 Ingest — `POST /api/documents`
1. Accept `{"path": "..."}` for a bundled file **or** a multipart `file` upload.
2. Validate extension against `ALLOWED_EXTENSIONS` (`.pdf/.txt/.md`); enforce `MAX_CONTENT_LENGTH` (PRD §7 file-handling note).
3. `ingest.extract()` → chunks (PyMuPDF text + TOC-derived section).
4. `db.insert_document()` writes document + chunks atomically.
5. Scanned/image PDF with no text → `ExtractionError` → HTTP **422** with a clear message (FR-03: no silent failure).

### 4.2 Ask — `POST /api/ask`
1. Load full corpus, `retrieval.retrieve(question, corpus)` → passages scoring ≥ `SCORE_THRESHOLD`.
2. **If no passages:** return `supported: false` + "not enough information" + empty citations, **without calling the model** (FR-04/§15).
3. **If model unavailable** (`llm.model_available()` false): return **503** with the already-retrieved citation badges — honest, no cloud fallback (FR-08).
4. Else `llm.answer_question()` runs the grounded prompt; if the reply contains `INSUFFICIENT_INFORMATION`, treat as unsupported and drop citations.
5. Response carries a persistent safety `disclaimer` (FR-08).

### 4.3 Health — `GET /api/health`
Probes Ollama `/api/tags` and checks the configured model is present → `model_available` (FR-01: distinguish "model ready" from "offline test passed").

---

## 5. Retrieval strategy (MVP = local RAG, keyword)

- **BM25 (Okapi)** with `k1=1.5`, `b=0.75`; lower-cased `[a-z0-9]+` tokens; small stop-word list; BM25+ IDF form `log(1 + (N - df + 0.5)/(df + 0.5))`.
- Index is cached in-process and **rebuilt only when the chunk-id signature changes** (`get_index`).
- A score floor (`SCORE_THRESHOLD`, default 0.5) gates the "no relevant passage → don't answer" fallback.
- **Future (PRD P2, not MVP):** local embeddings + vector search. Deliberately deferred to keep the demo validatable under time pressure (§8).

---

## 6. Local AI grounding (how hallucination is contained)

1. Retrieval decides *whether* an answer is possible (score threshold) — the app, not the model, controls the "I don't know" path.
2. The model is instructed to answer **only** from numbered context blocks, with `temperature=0`.
3. **Citation badges are assembled in `app.py` from retrieval metadata**, never from model output — directly mitigating PRD §15 "model invents citations."
4. Safety-critical / unsupported questions fall back instead of improvising (FR-08).

---

## 7. API surface

| Method | Path | Purpose | Status codes |
|---|---|---|---|
| GET | `/api/health` | model availability | 200 / 503 |
| POST | `/api/documents` | ingest PDF/TXT/MD | 201 / 400 / 422 |
| GET | `/api/documents` | list indexed docs | 200 |
| DELETE | `/api/documents/<id>` | remove doc + chunks | 200 |
| POST | `/api/ask` | retrieve → grounded answer + citations | 200 / 400 / 503 |

Server binds `127.0.0.1:5057` only (not `0.0.0.0`), so it is not exposed to the LAN and needs no firewall opening (PRD §7 implementation note).

---

## 8. Technology stack & portability

| Layer | Choice | Windows | macOS | Linux |
|---|---|---|---|---|
| UI | (none yet; HTML/CSS/JS later) | ✔ | ✔ | ✔ |
| Backend | Python 3 + Flask | ✔ | ✔ | ✔ |
| Runtime | Ollama | `winget install Ollama.Ollama` | installer/brew | install script |
| Model | `llama3.2:3b` (default) | ✔ | ✔ | ✔ |
| PDF | PyMuPDF (prebuilt wheels) | ✔ | ✔ | ✔ |
| Search | pure-Python BM25 | ✔ | ✔ | ✔ |
| Storage | SQLite (stdlib) | ✔ | ✔ | ✔ |

Setup/run entry points per OS: `setup.ps1`/`run.ps1` (Windows), `setup.sh`/`run.sh` (macOS/Linux). All env overrides (`RESCUEDESK_MODEL`, `RESCUEDESK_PORT`, `RESCUEDESK_SCORE_THRESHOLD`, …) are in `config.py`.

---

## 9. Local vs internet-dependent (for submission disclosures, PRD §7/§13)

**Runs locally after setup:** UI/backend, extraction, indexing, BM25 search, LLM inference, checklist/chat storage, citation display.
**Needs internet once, before setup:** dependency install, model download, repo clone, fetching reference docs if not bundled.
**Never used in core:** any cloud AI API, cloud DB, telemetry, live alert/weather APIs.

---

## 10. Known limitations (honest, to close before demo)

- Plain-text files have no page/section structure, so their citations show `page:1, section:null`; validate section mapping on a real TOC-bearing PDF.
- Keyword BM25 may miss paraphrased questions; tune chunk size/threshold once the real reference doc is loaded.
- No chat-history or checklist tables exist yet (PRD Phase 4).
- No latency timeout/streaming in the API yet (PRD §10) — the model call blocks up to `RESCUEDESK_LLM_TIMEOUT`.
- Loopback-only: fine for a single-device demo; not a multi-user or networked service by design.
