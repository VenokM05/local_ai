/* RescueDesk AI front-end. Talks only to the local /api on this device.
 * Nothing here sends document content or questions anywhere off-device. */
"use strict";

const API = "/api";
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

async function req(path, opts = {}) {
  const res = await fetch(path, opts);
  let data = null;
  try { data = await res.json(); } catch (_) { /* non-JSON */ }
  return { ok: res.ok, status: res.status, data };
}

/* ---------- navigation ---------- */
function showView(name) {
  $$(".view").forEach((v) => {
    const match = v.id === `view-${name}`;
    v.classList.toggle("active", match);
    v.hidden = !match;
  });
  $$(".tab").forEach((t) => {
    const active = t.dataset.view === name;
    t.classList.toggle("active", active);
    if (active) t.setAttribute("aria-current", "true");
    else t.removeAttribute("aria-current");
  });
  const focusTarget = $(`#view-${name}`);
  if (focusTarget) focusTarget.focus({ preventScroll: true });
}

function initNav() {
  $$(".tab").forEach((t) => t.addEventListener("click", () => showView(t.dataset.view)));
  $$("[data-goto]").forEach((b) => b.addEventListener("click", () => showView(b.dataset.goto)));
}

/* ---------- model status (FR-01) ---------- */
async function refreshStatus() {
  const pill = $("#model-status");
  const { ok, data } = await req(`${API}/health`);
  const ready = !!(data && data.model_available);
  pill.textContent = ready
    ? `Local model ready · ${data.model}`
    : "Local model unavailable";
  pill.className = "status-pill " + (ready ? "ok" : "err");

  const dash = $("#dash-model");
  if (dash) {
    dash.textContent = ready ? "Ready" : (ok || data ? "Unavailable" : "Unknown");
    dash.className = "big " + (ready ? "ready" : "notready");
  }
  const about = $("#about-model");
  if (about) about.textContent = ready ? `${data.model} (${data.runtime})` : "not detected";
  refreshOfflineNote();
}

/* The dashboard must NOT imply offline success just because a model is
 * installed (FR-01). Offline "pass" is a manual, honest per-session mark. */
function refreshOfflineNote() {
  const el = $("#dash-offline");
  if (!el) return;
  const passed = sessionStorage.getItem("offline_passed") === "1";
  el.textContent = passed ? "Passed (this session)" : "Not yet run";
  el.className = "big " + (passed ? "ready" : "notready");
}

function initOfflineButton() {
  const btn = $("#mark-offline-passed");
  if (!btn) return;
  btn.addEventListener("click", () => {
    sessionStorage.setItem("offline_passed", "1");
    refreshOfflineNote();
  });
}

/* ---------- ask (FR-04/05) ---------- */
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function renderSources(citations) {
  if (!citations || !citations.length) return "";
  const items = citations.map((c, i) => {
    const where = [c.page ? `p.${c.page}` : null, c.section || null].filter(Boolean).join(" · ");
    return `<details class="source">
      <summary>
        <span class="cite-ref">[${i + 1}]</span>
        <span>${escapeHtml(c.document)}</span>
        <span class="cite-meta">${escapeHtml(where)}</span>
        <span class="relevance">rel ${c.relevance}</span>
      </summary>
      <div class="snippet">${escapeHtml(c.snippet)}</div>
    </details>`;
  }).join("");
  return `<div class="sources"><h4>Sources (from your documents)</h4>${items}</div>`;
}

function renderAnswer(payload) {
  const box = $("#answer");
  if (payload.error) {
    box.innerHTML = `<div class="body unsupported"><span class="badge error">Model unavailable</span>
      <p>${escapeHtml(payload.error)}</p>${renderSources(payload.citations)}</div>`;
    return;
  }
  const badge = payload.supported
    ? '<span class="badge supported">Grounded in your documents</span>'
    : '<span class="badge unsupported">Not enough information</span>';
  const cls = payload.supported ? "body" : "body unsupported";
  box.innerHTML = `<div class="${cls}">${badge}<p>${escapeHtml(payload.answer)}</p>
    ${renderSources(payload.citations)}</div>`;
}

async function submitAsk(question) {
  const box = $("#answer");
  box.innerHTML = `<div class="body"><span class="spinner"></span>Thinking locally…</div>`;
  $("#ask-input").value = question;
  const { data } = await req(`${API}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  renderAnswer(data || { error: "No response from the local service." });
  loadChat();
}

function initAsk() {
  $("#ask-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const q = $("#ask-input").value.trim();
    if (q) submitAsk(q);
  });
  $$("#suggest .chip").forEach((c) =>
    c.addEventListener("click", () => submitAsk(c.textContent.trim())));
  $("#clear-chat").addEventListener("click", async () => {
    await req(`${API}/chat`, { method: "DELETE" });
    loadChat();
  });
}

/* ---------- chat history (FR-07) ---------- */
async function loadChat() {
  const { data } = await req(`${API}/chat`);
  const ul = $("#chat-history");
  const msgs = (data && data.messages) || [];
  if (!msgs.length) { ul.innerHTML = '<li class="muted" style="cursor:default">No questions yet.</li>'; return; }
  ul.innerHTML = msgs.map((m, i) => `
    <li data-i="${i}">
      <span class="q">${escapeHtml(m.question)}</span>
      <span class="dot ${m.supported ? "ok" : "no"}">${m.supported ? "answered" : "no source"}</span>
    </li>`).join("");
  ul._msgs = msgs;
}

function initChatReopen() {
  $("#chat-history").addEventListener("click", (e) => {
    const li = e.target.closest("li[data-i]");
    if (!li || !li.parentElement._msgs) return;
    const m = li.parentElement._msgs[Number(li.dataset.i)];
    $("#answer").innerHTML = `<div class="body ${m.supported ? "" : "unsupported"}">
      <p><strong>${escapeHtml(m.question)}</strong></p><p>${escapeHtml(m.answer)}</p>
      ${renderSources(JSON.parse(m.citations || "[]"))}</div>`;
  });
}

/* ---------- documents (FR-02) ---------- */
async function loadDocs() {
  const { data } = await req(`${API}/documents`);
  const ul = $("#doc-list");
  const docs = (data && data.documents) || [];
  if (!docs.length) { ul.innerHTML = '<li class="muted">No documents indexed yet. Import one above.</li>'; return; }
  ul.innerHTML = docs.map((d) => `
    <li class="doc">
      <div>
        <div class="name">${escapeHtml(d.name)}</div>
        <div class="meta">${d.chunk_count} passages · ${escapeHtml(d.media_type)} · added ${escapeHtml(d.created_at)}</div>
      </div>
      <button class="remove" data-id="${d.id}" type="button">Remove</button>
    </li>`).join("");
}

function initDocs() {
  $("#upload-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = $("#upload-input");
    const file = input.files[0];
    const msg = $("#upload-msg");
    if (!file) { msg.textContent = "Choose a PDF, TXT, or MD file first."; return; }
    msg.innerHTML = '<span class="spinner"></span>Extracting on this device…';
    const form = new FormData();
    form.append("file", file);
    const { ok, data } = await req(`${API}/documents`, { method: "POST", body: form });
    if (ok) {
      msg.textContent = `Imported ${data.chunks} passages from ${data.name}.`;
      input.value = "";
      loadDocs();
    } else {
      msg.textContent = (data && data.error) || "Import failed.";
    }
  });
  $("#doc-list").addEventListener("click", async (e) => {
    const btn = e.target.closest(".remove");
    if (!btn) return;
    await req(`${API}/documents/${btn.dataset.id}`, { method: "DELETE" });
    loadDocs();
  });
}

/* ---------- checklist (FR-06) ---------- */
async function loadChecklist() {
  const { data } = await req(`${API}/checklist`);
  const items = (data && data.items) || [];
  const groups = {};
  items.forEach((it) => { (groups[it.category] ||= []).push(it); });
  const wrap = $("#checklist");
  wrap.innerHTML = Object.entries(groups).map(([cat, list]) => `
    <div class="check-group">
      <h3>${escapeHtml(cat)}</h3>
      ${list.map((it) => `
        <div class="check-item ${it.done ? "done" : ""}">
          <input type="checkbox" id="chk-${it.id}" data-id="${it.id}" ${it.done ? "checked" : ""} />
          <label for="chk-${it.id}">${escapeHtml(it.label)}</label>
          <button class="del" data-id="${it.id}" title="Remove item" aria-label="Remove item">&times;</button>
        </div>`).join("")}
    </div>`).join("");
  updateProgress(items);
}

function updateProgress(items) {
  const done = items.filter((i) => i.done).length;
  const total = items.length || 1;
  const pct = Math.round((done / total) * 100);
  $("#checklist-progress").innerHTML =
    `${done} of ${items.length} complete · saved on this device
     <div class="bar"><div class="fill" style="width:${pct}%"></div></div>`;
}

function initChecklist() {
  $("#checklist").addEventListener("change", async (e) => {
    const box = e.target.closest("input[type=checkbox]");
    if (!box) return;
    await req(`${API}/checklist/${box.dataset.id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ done: box.checked }),
    });
    loadChecklist();
  });
  $("#checklist").addEventListener("click", async (e) => {
    const del = e.target.closest(".del");
    if (!del) return;
    await req(`${API}/checklist/${del.dataset.id}`, { method: "DELETE" });
    loadChecklist();
  });
  $("#add-item").addEventListener("submit", async (e) => {
    e.preventDefault();
    const label = $("#add-label").value.trim();
    if (!label) return;
    await req(`${API}/checklist`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label, category: $("#add-category").value.trim() || "General" }),
    });
    $("#add-label").value = "";
    loadChecklist();
  });
}

/* ---------- boot ---------- */
document.addEventListener("DOMContentLoaded", async () => {
  initNav();
  initOfflineButton();
  initAsk();
  initChatReopen();
  initDocs();
  initChecklist();
  await refreshStatus();
  loadChat();
  loadDocs();
  loadChecklist();
});
