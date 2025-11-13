// content.js

const API_URL = "http://127.0.0.1:5000/predict";

let lastSelectionRange = null;

// Debug: confirm injection
console.log("Cornell Fact Checker content script loaded.");

// Track last selection so we can highlight it later
document.addEventListener("mouseup", () => {
  const sel = window.getSelection();
  if (sel && sel.rangeCount > 0 && !sel.isCollapsed) {
    lastSelectionRange = sel.getRangeAt(0).cloneRange();
  }
});

// Listen for CHECK_TEXT from background
chrome.runtime.onMessage.addListener(async (msg, sender, sendResponse) => {
  if (msg?.type !== "CHECK_TEXT") return;
  const text = (msg.text || "").trim();
  if (!text) return;

  let data;
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    data = await res.json();
  } catch (e) {
    console.error("❌ Backend request failed:", e);
    data = { error: String(e) };
  }

  const normalized = normalizeModelOutput(data, text);

  // Highlight selection
  if (lastSelectionRange) {
    try {
      const mark = document.createElement("mark");
      mark.className = "cornell-misinfo-mark";
      mark.style.backgroundColor =
        normalized.predicted_label === 1
          ? "rgba(255, 0, 0, 0.35)"   // likely false
          : "rgba(0, 128, 0, 0.25)";  // likely true
      mark.style.padding = "0 2px";
      lastSelectionRange.surroundContents(mark);
    } catch {
      const wrapper = document.createElement("mark");
      wrapper.className = "cornell-misinfo-mark";
      wrapper.style.backgroundColor =
        normalized.predicted_label === 1
          ? "rgba(255, 0, 0, 0.35)"
          : "rgba(0, 128, 0, 0.25)";
      const contents = lastSelectionRange.extractContents();
      wrapper.appendChild(contents);
      lastSelectionRange.insertNode(wrapper);
    }
  }

  // Store result for popup
  await chrome.storage.local.set({ lastResult: normalized });

  // Small toast
  showToast(normalized.verdict_text);

  // Notify popup + background
  chrome.runtime.sendMessage({ type: "RESULT_UPDATED", payload: normalized });
  chrome.runtime.sendMessage({ type: "RESULT_READY" });
});

/* ------------ Helpers ------------ */

function normalizeModelOutput(raw, inputText) {
  if (!raw || raw.error) {
    return {
      input: inputText,
      predicted_label: 1,
      verdict_text: "Error: Backend unavailable",
      primary_source: null,
      url: location.href,
      title: document.title,
      at: Date.now(),
      raw
    };
  }

  const probs = raw.probabilities || {};
  const pTrue = clamp01(Number(probs.true ?? 0));
  const pFalse = clamp01(Number(probs.false ?? (1 - pTrue)));
  const verdict = String(raw.verdict || "").toLowerCase();

  // Decide label based on backend verdict first
  let label;
  if (verdict === "likely_false") label = 1;
  else if (verdict === "likely_true") label = 0;
  else label = pFalse >= 0.5 ? 1 : 0;

  const primary = pickPrimarySource(raw, label);

  return {
    input: raw.input || inputText,
    predicted_label: label,
    confidence_true: pTrue,
    confidence_fake: pFalse,
    verdict_text: verdictText(label, raw.verdict),
    model_shape: "verification_system",
    primary_source: primary,
    url: location.href,
    title: document.title,
    at: Date.now(),
    raw
  };
}

function verdictText(label, verdictStr = "") {
  const v = String(verdictStr || "").toLowerCase();
  if (v === "likely_false") return "Likely False";
  if (v === "likely_true") return "Likely True";
  if (v === "cannot_verify") return "Cannot Verify";
  return label === 1 ? "Likely False" : "Likely True";
}

function pickPrimarySource(result, predLabel) {
  let pool = [];
  if (predLabel === 1 && Array.isArray(result.supporting_sources_false) && result.supporting_sources_false.length) {
    pool = result.supporting_sources_false;
  } else if (predLabel === 0 && Array.isArray(result.supporting_sources_true) && result.supporting_sources_true.length) {
    pool = result.supporting_sources_true;
  } else if (Array.isArray(result.nearest_sources_considered) && result.nearest_sources_considered.length) {
    pool = result.nearest_sources_considered;
  }

  if (!pool.length) return null;

  const scored = pool
    .map(x => ({
      source: x.source || "",
      score: Number(x.entailment ?? x.contradiction ?? x.similarity ?? 0),
      detail: x
    }))
    .filter(x => x.source);

  if (!scored.length) return null;

  scored.sort((a, b) => b.score - a.score);
  const best = scored[0];

  return { source: best.source, score: best.score, detail: best.detail };
}

function clamp01(x) {
  return Math.max(0, Math.min(1, Number(x) || 0));
}

function showToast(text) {
  const toast = document.createElement("div");
  toast.textContent = text;
  Object.assign(toast.style, {
    position: "fixed",
    left: "16px",
    bottom: "16px",
    zIndex: 2147483647,
    background: "#ffffff",
    border: "1px solid #ddd",
    borderRadius: "8px",
    padding: "10px 12px",
    boxShadow: "0 4px 14px rgba(0,0,0,0.12)",
    font: "14px/1.3 system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
  });
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}
