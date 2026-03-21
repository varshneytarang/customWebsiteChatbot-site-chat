
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
    if (!tab.url) return;
    const url = new URL(tab.url);
    console.log(url)

    if (info.status === 'loading' && info.url) {
        await chrome.sidePanel.setOptions({
            tabId,
            path: 'intro.html',
            enabled: true,
        });
    }

    // Auto-extract and prepare page content when tab finishes loading
    if (info.status === 'complete') {
        try {
            console.log(`[Service Worker] Extracting content from tab ${tabId}: ${tab.url}`);
            
            const [{result}] = await chrome.scripting.executeScript({
                target: {tabId: tab.id},
                func: () => {
                    return document.body.innerText;
                }
            });
            
            if (!result || !result.trim()) {
                console.warn('[Service Worker] Extracted content is empty');
                await chrome.storage.session.set({[`tab_${tabId}_ready`]: false});
                return;
            }
            console.log(result)

            console.log(`[Service Worker] Sending ${result.length} chars to backend for tab ${tabId}`);
            
            const res = await fetch("http://localhost:5000/prepareIt", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({result, tabId})
            });
            
            const data = await res.json();
            
            if (data.msg === "Success") {
                console.log(`[Service Worker] ✅ Tab ${tabId} is ready for questions`);
                await chrome.storage.session.set({[`tab_${tabId}_ready`]: true});
            } else {
                console.warn(`[Service Worker] ❌ Preparation failed: ${data.error}`);
                await chrome.storage.session.set({[`tab_${tabId}_ready`]: false});
            }
        } catch (error) {
            console.error(`[Service Worker] Error preparing tab ${tabId}:`, error.message);
            await chrome.storage.session.set({[`tab_${tabId}_ready`]: false});
        }
    }
});


