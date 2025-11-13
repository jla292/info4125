// popup.js
document.addEventListener("DOMContentLoaded", async () => {
  const { lastResult } = await chrome.storage.local.get(["lastResult"]);

  if (lastResult) {
    renderResult(lastResult);
  } else {
    showMessage("Highlight text and choose 'Check with Cornell Fact Checker' from the right-click menu.");
  }

  // Live updates while popup is open
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg?.type === "RESULT_UPDATED" && msg.payload) {
      renderResult(msg.payload);
    }
  });
});

function renderResult(r) {
  const indicator = document.getElementById("indicator");
  const verdictEl = document.getElementById("verdict");
  const snippetEl = document.getElementById("snippet");
  const pageTitle = document.getElementById("pageTitle");
  const sourceEl = document.getElementById("source");

  // Snippet text
  if (snippetEl) {
    const txt = (r?.input || "").trim();
    snippetEl.textContent =
      txt.length > 200 ? txt.slice(0, 200) + "…" : txt || "No text selected.";
  }

  // Page title
  if (pageTitle) {
    pageTitle.textContent = r?.title ? `On: ${r.title}` : "";
  }

  // Backend verdict (from raw JSON)
  const backendVerdict = String(r?.raw?.verdict || r?.verdict || "").toLowerCase();

  if (verdictEl) {
    verdictEl.textContent = readableVerdict(backendVerdict);
    verdictEl.style.color = verdictColor(backendVerdict);
  }

  if (indicator) {
    indicator.style.width = barWidth(backendVerdict);
    indicator.style.backgroundColor = verdictColor(backendVerdict);
    indicator.style.transition = "width 0.4s ease";
  }

  // Clickable primary source
  if (sourceEl) {
    const p = r?.primary_source;

    if (p?.source) {
      sourceEl.textContent = p.source;
      sourceEl.href = p.source;
      sourceEl.target = "_blank";
      sourceEl.style.color = "#b31b1b";
      sourceEl.style.textDecoration = "underline";
      sourceEl.title = p.detail?.short_text || "";
    } else {
      sourceEl.textContent = "No primary source found";
      sourceEl.removeAttribute("href");
      sourceEl.style.color = "#777";
      sourceEl.style.textDecoration = "none";
      sourceEl.title = "";
    }
  }
}

function readableVerdict(v) {
  if (v === "likely_true") return "Likely True";
  if (v === "likely_false") return "Likely False";
  return "Cannot Verify";
}

function barWidth(v) {
  if (v === "likely_true") return "100%";
  if (v === "likely_false") return "100%";
  return "50%"; // neutral
}

function verdictColor(v) {
  if (v === "likely_true") return "#27ae60";  // green
  if (v === "likely_false") return "#e74c3c"; // red
  return "#cccc33";                           // yellow
}

function showMessage(msg) {
  const el = document.getElementById("message");
  if (!el) return;
  el.style.display = "block";
  el.textContent = msg;
  setTimeout(() => {
    el.style.display = "none";
  }, 4000);
}
