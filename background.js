// background.js (MV3 service worker)

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "checkMisinformation",
    title: "Check with Cornell Misinformation Checker",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "checkMisinformation" && info.selectionText && tab?.id) {
    // Tell the content script on that tab to verify the selected text
    chrome.tabs.sendMessage(tab.id, {
      type: "CHECK_TEXT",
      text: info.selectionText
    });
  }
});

// Open the popup when the content script notifies that the result is ready.
// Note: chrome.action.openPopup() is supported in MV3; if it fails, the user can click the icon.
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === "RESULT_READY") {
    if (chrome.action && chrome.action.openPopup) {
      chrome.action.openPopup().catch(() => {/* ignore if not pinnned or fails */});
    }
  }
});
