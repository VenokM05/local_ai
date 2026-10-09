# RescueDesk AI — Phasing Plan

**Status legend:** ✅ done · 🔨 in progress · ⏳ pending · ⚠️ decision
**Reference:** PRD §14 (Recommended Build Order) is the source of truth for phase order. Core principle: *"Do not move to later features while the core flow is broken."*

---

## Guiding decisions (as of this plan)

| # | Decision | Status | Notes |
|---|---|---|---|
| D1 | Product scope = offline emergency **document assistant**, not a full EM platform | ✅ locked | PRD §18 |
| D2 | Target OS for the build/demo | ⚠️ **Windows** (was Mac) | Backend is cross-platform; Windows scripts added (`setup.ps1`/`run.ps1`) |
| D3 | Local runtime = **Ollama**, small instruction model | ✅ locked | `llama3.2:3b` default; override via `RESCUEDESK_MODEL` |
| D4 | Retrieval = **BM25 keyword** (pure Python, no vector DB) | ✅ locked | PRD §8; offline-provable |
| D5 | Citations come from **retrieval metadata**, never the model | ✅ locked | PRD §15 mitigation |
| D6 | Phone / mobile on-device inference | ⏳ deferred | Out of MVP (PRD line 98); optional demo "proof" only |
| D7 | Cloud API for core answers | 🚫 prohibited | PRD FR-04; would forfeit Local AI credit |

---

## Phase 0 — Environment & runtime  (PRD §14 step 1)
**Goal:** confirm hardware + a working local prompt before any UI.

- ✅ Backend scaffolded cross-platform; verified on macOS (Python 3.9, PyMuPDF arm64 wheel).
- 🔨 **Windows bring-up:** install Python 3.10+, Ollama (`winget install Ollama.Ollama`), `ollama pull llama3.2:3b`, run `.\setup.ps1` then `.\run.ps1`.
- ⏳ Confirm `/api/health` returns `model_available: true` on the Windows target.
- ⏳ Record baseline latency for one grounded answer on the actual demo machine (PRD §10: measure, don't promise).

**Gate to Phase 1:** a local model answers one prompt on the target machine.

---

## Phase 1 — Smallest end-to-end RAG proof  (PRD §14 step 2)
**Goal:** one trusted text doc → retrieve → local model → grounded answer.

- ✅ `POST /api/documents` ingest (PDF via PyMuPDF, TXT/MD) into `text_chunks`.
- ✅ BM25 retrieval with score threshold.
- ✅ `POST /api/ask` calls Ollama with context-constrained prompt + `INSUFFICIENT_INFORMATION` fallback.
- ✅ Verified on macOS: on-topic retrieval, off-topic → zero-hit fallback, model-unavailable → honest 503.
- 🔨 Re-run the same three curl checks on Windows (see D2).

**Gate to Phase 2:** a curl-verified grounded answer with a real source reference.

---

## Phase 2 — Real source references  (PRD §14 step 3, FR-05)
- ✅ Citation badges built from retrieval metadata (`document`, `page`, `section`, `snippet`, `relevance`).
- ⏳ Page/section mapping is weak for plain-text files; validate it against a **real TOC-bearing PDF**.
- ⏳ Add the 5 §8 evaluation questions and manually check each answer + citation against the source.

---

## Phase 3 — PDF extraction + document library  (PRD §14 step 4, FR-02/FR-03)
- ✅ Multi-document index, list endpoint, delete-with-cascade.
- ⏳ Replace synthetic sample with a **verified, attributed** public preparedness PDF (PRD §9) — currently a blocker for submission credibility.
- ⏳ Tune `CHUNK_MAX_CHARS` / section splitting once the real PDF is in.
- ⏳ Confirm scanned/image PDFs raise the clear OCR error (FR-03), not silence.

---

## Phase 4 — Checklist + local persistence  (PRD §14 step 5, FR-06/FR-07)
- ⏳ SQLite `checklist_items` table; check/uncheck; persists across restart.
- ⏳ Optional chat-history table + clear-history action (FR-07).
- ⏳ All must work with network disconnected.

---

## Phase 5 — UI build & polish  (PRD §14 step 6, §6 screens)
- ⏳ Home dashboard with accurate "model ready" vs "offline test passed" distinction (FR-01).
- ⏳ Ask-the-Guide, Documents, Checklist, Privacy/About screens.
- ⏳ Loading/latency feedback for slow inference (PRD §10).
- ⏳ Persistent safety disclaimer (FR-08).

---

## Phase 6 — Verified offline operation  (PRD §14 step 7, §11 offline test)
- ⏳ Download model+deps, disable Wi-Fi, restart app, ask a question, confirm local answer + citations + checklist save.
- ⏳ Capture evidence; do **not** pass an online recording as an offline test (PRD §12).

**Gate to Phase 7:** §11 Definition-of-Done checks all pass.

---

## Phase 7 — Demo recording  (PRD §14 step 8, §12)
- ⏳ 60-second storyboard; fallback recording prepared honestly.
- ⏳ Keep interface free of debug output.

---

## Phase 8 — Publish & disclosures  (PRD §14 step 9, §13)
- ⏳ Public GitHub repo, team details, final name (README currently says "Elohim Creator", PRD says "RescueDesk AI" — reconcile).
- ⏳ Disclose models/version, frameworks, "no cloud AI in core" statement, existing assets, AI dev tools.
- ⏳ Submission checklist complete before the **Oct 10, 2026 10:00 AM** deadline.

---

## Optional track — On-device phone "proof" (NOT a phase)
- ⏳ Android: Termux → llama.cpp → 1B/3B GGUF, one grounded prompt in airplane mode.
- ⏳ iOS 26: tiny SwiftUI + Apple Foundation Models call reusing the existing prompt.
- Framing for §13: *core product runs on-device (Windows); the same on-device approach is demonstrated on a phone.* Do not attempt a full app port before Phase 8 is done.

---

## De-scope rule
If time goes critically short, drop in this order (protect the top): **local inference → grounded answers → real citations → verified offline → basic checklist → UI polish → everything else.**
