document.addEventListener("DOMContentLoaded", () => {
  // Auto-adjust textarea height
  const textarea = document.getElementById("question");
  
  if (!textarea) {
    console.error("❌ Error: textarea element not found!");
    return;
  }

  textarea.addEventListener("input", () => {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 100) + "px";
  });

  // Handle Enter key (Shift+Enter for newline)
  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      document.getElementById("askBtn").click();
    }
  });

  document.getElementById("askBtn").addEventListener("click", async () => {
    const questionInput = document.getElementById("question");
    const chatbox = document.getElementById("chatbox");
    const loader = document.getElementById("loader");
    const askBtn = document.getElementById("askBtn");
    const status = document.getElementById("status");
    const responseMode = document.getElementById("responseMode");

    const question = questionInput.value.trim();
    if (!question) {return};

    // Check if page is ready
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab || typeof tab.id !== "number") {
      const errorMsg = document.createElement("div");
      errorMsg.className = "message";
      errorMsg.innerHTML = `<span class="message-label bot">Bot</span><span class="message-text">⏳ Still preparing the page... Please wait a moment.</span>`;
      chatbox.appendChild(errorMsg);
      chatbox.scrollTop = chatbox.scrollHeight;
      return;
    }

    // Add user message
    const userMsg = document.createElement("div");
    userMsg.className = "message user";
    userMsg.innerHTML = `<span class="message-label">You</span><span class="message-text">${escapeHtml(question)}</span>`;
    chatbox.appendChild(userMsg);
    chatbox.scrollTop = chatbox.scrollHeight;

    questionInput.value = "";
    textarea.style.height = "auto";
    loader.style.display = "flex";
    askBtn.disabled = true;
    const selectedMode = (responseMode?.value || "normal").toLowerCase();
    status.textContent = selectedMode === "research" ? "Researching..." : "Thinking...";

    try {
      const {url} = tab;

      const res = await fetch("http://localhost:5000/askIt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, question, tabId: tab.id, response_mode: selectedMode })
      });

      const data = await res.json();
      console.log(data);

      const botMsg = document.createElement("div");
      botMsg.className = "message bot";
      const answer = data.answer || "No response received";
      botMsg.innerHTML = `<span class="message-label">Bot</span><span class="message-text">${formatAnswer(answer)}${formatResponseMeta(data)}</span>`;
      chatbox.appendChild(botMsg);
      chatbox.scrollTop = chatbox.scrollHeight;
      status.textContent = "Ready";
    } catch (err) {
      const errorMsg = document.createElement("div");
      errorMsg.className = "message bot";
      errorMsg.innerHTML = `<span class="message-label">Bot</span><span class="message-text">❌ Error: ${err.message}</span>`;
      chatbox.appendChild(errorMsg);
      status.textContent = "Error";
    } finally {
      loader.style.display = "none";
      askBtn.disabled = false;
    }
  });

  // Help button
  document.getElementById("help").addEventListener("click", () => {
    document.getElementById("modal").style.display = "flex";
  });

  // Close modal
  document.getElementById("closePopup").addEventListener("click", () => {
    document.getElementById("modal").style.display = "none";
  });

  // Close modal when clicking overlay
  document.getElementById("modal").addEventListener("click", (e) => {
    if (e.target.id === "modal" || e.target.classList.contains("modal-overlay")) {
      document.getElementById("modal").style.display = "none";
    }
  });

  // Utility function to escape HTML
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function formatInline(text) {
    const safe = escapeHtml(text);
    return safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  }

  function formatCodeBlock(codeText, languageLabel) {
    const language = languageLabel ? escapeHtml(languageLabel) : "code";
    const code = escapeHtml(codeText);
    return [
      '<div class="answer-code-block">',
      `<div class="answer-code-header">${language}</div>`,
      `<pre><code>${code}</code></pre>`,
      "</div>"
    ].join("");
  }

  function formatTextBlock(textBlock) {
    const lines = textBlock
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    if (lines.length === 0) {
      return "";
    }

    const htmlParts = [];
    let inUl = false;
    let inOl = false;

    const closeLists = () => {
      if (inUl) {
        htmlParts.push("</ul>");
        inUl = false;
      }
      if (inOl) {
        htmlParts.push("</ol>");
        inOl = false;
      }
    };

    for (const line of lines) {
      const numbered = line.match(/^\d+\.\s+(.*)$/);
      const bulleted = line.match(/^[-*•]\s+(.*)$/);

      if (numbered) {
        if (inUl) {
          htmlParts.push("</ul>");
          inUl = false;
        }
        if (!inOl) {
          htmlParts.push('<ol class="answer-list answer-list-ordered">');
          inOl = true;
        }
        htmlParts.push(`<li>${formatInline(numbered[1])}</li>`);
        continue;
      }

      if (bulleted) {
        if (inOl) {
          htmlParts.push("</ol>");
          inOl = false;
        }
        if (!inUl) {
          htmlParts.push('<ul class="answer-list">');
          inUl = true;
        }
        htmlParts.push(`<li>${formatInline(bulleted[1])}</li>`);
        continue;
      }

      closeLists();

      if (line.endsWith(":")) {
        htmlParts.push(`<p class="answer-heading">${formatInline(line)}</p>`);
      } else {
        htmlParts.push(`<p>${formatInline(line)}</p>`);
      }
    }

    closeLists();
    return htmlParts.join("");
  }

  function formatAnswer(rawAnswer) {
    const raw = String(rawAnswer || "")
      .replace(/\r\n/g, "\n")
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<\/?b>/gi, "**");

    if (!raw.trim()) {
      return "No response received";
    }

    const parts = raw.split(/```/);
    const htmlParts = [];

    for (let i = 0; i < parts.length; i += 1) {
      const segment = parts[i];
      if (!segment || !segment.trim()) {
        continue;
      }

      if (i % 2 === 0) {
        const textHtml = formatTextBlock(segment);
        if (textHtml) {
          htmlParts.push(textHtml);
        }
      } else {
        const codeLines = segment.replace(/^\n+/, "").split("\n");
        let languageLabel = "";
        if (codeLines.length > 0 && /^[a-zA-Z0-9_+-]{1,20}$/.test(codeLines[0].trim())) {
          languageLabel = codeLines.shift().trim();
        }
        const codeText = codeLines.join("\n").trimEnd();
        htmlParts.push(formatCodeBlock(codeText, languageLabel));
      }
    }

    return htmlParts.length ? htmlParts.join("") : "No response received";
  }

  function formatResponseMeta(data) {
    const rating = data?.context_rating || {};
    const answerUrls = data?.answer_urls?.items || [];

    const score = Number(rating.relevance_score);
    const label = String(rating.relevance_label || "unknown").toLowerCase();
    const ratingClass = label === "high" || label === "medium" || label === "low" ? label : "medium";

    const hasRating = Number.isFinite(score);
    const hasUrls = Array.isArray(answerUrls) && answerUrls.length > 0;

    if (!hasRating && !hasUrls) {
      return "";
    }

    let html = '<div class="message-meta">';

    if (hasRating) {
      html += '<div class="rating-row">';
      html += '<span class="rating-label">Context relevance:</span>';
      html += `<span class="rating-chip ${ratingClass}">${score}% ${escapeHtml(label)}</span>`;
      html += '</div>';
    }

    if (hasUrls) {
      html += '<div class="source-list">';
      html += '<span class="source-title">Sources:</span>';
      answerUrls.forEach((item) => {
        const url = String(item.url || "").trim();
        if (!url) {
          return;
        }
        const title = String(item.title || "Open source").trim();
        const sourceType = String(item.source_type || "source").trim();
        html += `<a class="source-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>`;
        html += `<span class="source-type">${escapeHtml(sourceType)}</span>`;
      });
      html += '</div>';
    }

    html += '</div>';
    return html;
  }

  console.log("✅ popup1.js loaded successfully");
});




