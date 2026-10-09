"""Central configuration for the RescueDesk AI local RAG backend.

All tunables live here so the rest of the code stays decision-free. Values
default to local, offline-friendly settings per PRD section 7 and 10.
"""

from __future__ import annotations

import os

# --- Storage ---------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.environ.get("RESCUEDESK_DB", os.path.join(DATA_DIR, "rescuedesk.db"))

# --- Local model runtime (Ollama) ------------------------------------------
# Bound to loopback on purpose: PRD section 7 says do not expose the model or
# uploaded documents to the local network.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
# Small instruction model suitable for an 8 GB Apple Silicon machine. Override
# with RESCUEDESK_MODEL once hardware/latency is checked (PRD section 17).
OLLAMA_MODEL = os.environ.get("RESCUEDESK_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT_SECONDS = int(os.environ.get("RESCUEDESK_LLM_TIMEOUT", "120"))

# --- Retrieval -------------------------------------------------------------
TOP_K = int(os.environ.get("RESCUEDESK_TOP_K", "4"))
# Minimum acceptable BM25 score. Below this we treat retrieval as "no relevant
# passage" and return the unsupported answer WITHOUT calling the model
# (PRD FR-04 / section 15: avoid inventing an answer).
SCORE_THRESHOLD = float(os.environ.get("RESCUEDESK_SCORE_THRESHOLD", "0.5"))
CHUNK_MAX_CHARS = int(os.environ.get("RESCUEDESK_CHUNK_MAX_CHARS", "700"))
CHUNK_OVERLAP_CHARS = int(os.environ.get("RESCUEDESK_CHUNK_OVERLAP_CHARS", "120"))

# --- Upload safety (PRD section 7 implementation note) ---------------------
MAX_UPLOAD_BYTES = int(os.environ.get("RESCUEDESK_MAX_UPLOAD_BYTES", str(15 * 1024 * 1024)))
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}

# --- Flask -----------------------------------------------------------------
HOST = os.environ.get("RESCUEDESK_HOST", "127.0.0.1")
PORT = int(os.environ.get("RESCUEDESK_PORT", "5057"))
