
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
    if (!tab.url) return;
    const url = new URL(tab.url);
        await chrome.sidePanel.setOptions({
        tabId,
        path: 'intro.html',
        enabled: true,
    });  

});
