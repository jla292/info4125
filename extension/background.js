// background.js (MV3 service worker)

// Create context menu on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "checkMisinformation",
    title: "Check with Cornell Fact Checker",
    contexts: ["selection"]
  });
});

// When user clicks the menu, send CHECK_TEXT to content script
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (
    info.menuItemId === "checkMisinformation" &&
    info.selectionText &&
    info.selectionText.trim() !== "" &&
    tab?.id
  ) {
    chrome.tabs.sendMessage(
      tab.id,
      {
        type: "CHECK_TEXT",
        text: info.selectionText.trim()
      },
      () => {
        // Swallow "no receiver" errors (e.g. restricted pages)
        if (chrome.runtime.lastError) {
          console.warn("No content script in this tab:", chrome.runtime.lastError.message);
        }
      }
    );
  }
});

// Optional: when a result is ready, try to open popup (best-effort)
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === "RESULT_READY") {
    if (chrome.action && chrome.action.openPopup) {
      chrome.action.openPopup().catch(() => {
        // Ignore if popup can't be opened automatically
      });
    }
  }
});
