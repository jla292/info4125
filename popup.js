// popup.js
document.addEventListener("DOMContentLoaded", async () => {
  // Load the most recent check result
  const { lastResult } = await chrome.storage.local.get(["lastResult"]);
  if (lastResult) {
    renderResult(lastResult);
  } else {
    showMessage("Highlight text on a page and choose 'Check claim' from the right-click menu.");
  }

  // Live update while popup is open
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg?.type === "RESULT_UPDATED" && msg.payload) {
      renderResult(msg.payload);
    }
  });

  // Allow manual recheck from popup (optional button)
  const btn = document.getElementById("checkCurrentSelection");
  if (btn) {
    btn.addEventListener("click", async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id) return;

      const [{ result: selectedText } = {}] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => (window.getSelection && window.getSelection().toString()) || ""
      });

      if (selectedText && selectedText.trim()) {
        chrome.tabs.sendMessage(tab.id, { type: "CHECK_TEXT", text: selectedText.trim() });
        showMessage("Checking selected text...");
      } else {
        showMessage("Select some text on the page first.");
      }
    });
  }
});

/**
 * Render verification result in the popup UI
 */
function renderResult(r) {
  // DOM elements
  const indicator = document.getElementById("indicator");
  const verdictEl = document.getElementById("verdict");
  const snippetEl = document.getElementById("snippet");
  const pageTitle = document.getElementById("pageTitle");
  const pageUrl = document.getElementById("pageUrl");
  const sourceEl = document.getElementById("source");

  // Confidence values
  const percentFalse = clamp01(Number(r?.percent_false ?? (r?.confidence_fake ?? 0) * 100));

  // Color and bar animation
  if (indicator) {
    indicator.style.width = `${percentFalse}%`;
    indicator.style.transition = "width 0.4s ease";
    indicator.style.backgroundColor =
      r?.verdict_text?.toLowerCase().includes("cannot verify")
        ? "#cccc33" // yellow/neutral
        : percentFalse >= 50
          ? "#e74c3c" // red false
          : "#27ae60"; // green true
  }

  // Verdict text
  if (verdictEl) {
    verdictEl.textContent = r?.verdict_text || verdictFromPercent(percentFalse);
    verdictEl.style.color =
      r?.verdict_text?.toLowerCase().includes("cannot verify")
        ? "#b38b00"
        : percentFalse >= 50
          ? "#b00020"
          : "#006b2d";
  }

  // Display the claim snippet
  if (snippetEl) {
    const txt = (r?.input || "").trim();
    snippetEl.textContent = txt
      ? txt.length > 200
        ? txt.slice(0, 200) + "…"
        : txt
      : "No text selected.";
  }

  // Page metadata
  if (pageTitle) pageTitle.textContent = r?.title ? `On: ${r.title}` : "";
  if (pageUrl) {
    pageUrl.textContent = r?.url || "";
    pageUrl.title = r?.url || "";
  }

  // Primary source
  if (sourceEl) {
    if (r?.primary_source?.source) {
      const src = r.primary_source;
      sourceEl.textContent = src.source;
      if (src.detail?.topic) {
        sourceEl.title = `Topic: ${src.detail.topic}\nSimilarity: ${src.detail.similarity}`;
      } else if (src.detail?.short_text) {
        sourceEl.title = src.detail.short_text;
      }
      sourceEl.style.color = "#333";
    } else {
      sourceEl.textContent = "No primary source found";
      sourceEl.title = "";
      sourceEl.style.color = "#777";
    }
  }
}

/**
 * Fallback verdict text if backend string missing
 */
function verdictFromPercent(pFalse) {
  if (pFalse >= 70) return "Likely False";
  if (pFalse <= 30) return "Likely True";
  return "Cannot Verify";
}

/**
 * Clamp value between 0–100
 */
function clamp01(x) {
  if (Number.isNaN(x)) return 0;
  return Math.max(0, Math.min(100, Number(x)));
}

/**
 * Display temporary popup message
 */
function showMessage(msg) {
  const el = document.getElementById("message");
  if (!el) return;
  el.style.display = "block";
  el.textContent = msg;
  setTimeout(() => {
    el.style.display = "none";
  }, 4000);
}
