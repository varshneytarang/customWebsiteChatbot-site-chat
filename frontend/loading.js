window.addEventListener("DOMContentLoaded", async () => {
  const loaderText = document.querySelector(".loader-text");

  const setStatus = (message) => {
    if (loaderText) {
      loaderText.textContent = message;
    }
  };

  const goToPopup = (delayMs) => {
    setTimeout(() => {
      window.location.href = "popup.html";
    }, delayMs);
  };

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || typeof tab.id !== "number") {
      setStatus("Unable to access current tab");
      goToPopup(1200);
      return;
    }

    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.body?.innerText || ""
    });

    if (!result || !result.trim()) {
      console.warn("[Loader] Empty content");
      await chrome.storage.session.set({ [`tab_${tab.id}_ready`]: false });
      setStatus("No readable page content");
      goToPopup(1200);
      return;
    }

    setStatus("Connecting to local backend...");

    let res;
    try {
      res = await fetch("http://localhost:5000/prepareIt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ result, tabId: tab.id })
      });
    } catch (networkError) {
      console.error("[Loader] Backend unreachable:", networkError);
      await chrome.storage.session.set({ [`tab_${tab.id}_ready`]: false });
      setStatus("Backend offline. Start Python server.");
      goToPopup(1800);
      return;
    }

    let data = {};
    try {
      data = await res.json();
    } catch (parseError) {
      console.error("[Loader] Invalid backend JSON:", parseError);
    }

    if (res.ok && data.msg === "Success") {
      await chrome.storage.session.set({ [`tab_${tab.id}_ready`]: true });
      setStatus("Ready");
      document.body.classList.add("slide-out");
      goToPopup(600);
      return;
    }

    console.error("[Loader] Preparation failed:", data.error || res.statusText);
    await chrome.storage.session.set({ [`tab_${tab.id}_ready`]: false });
    setStatus("Backend error while preparing page");
    goToPopup(1800);
  } catch (error) {
    console.error("[Loader] Error:", error);
    setStatus("Unexpected loader error");
    goToPopup(1800);
  }
});
