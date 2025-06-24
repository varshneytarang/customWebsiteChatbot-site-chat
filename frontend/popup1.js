document.getElementById("askBtn").addEventListener("click", async () => {
  const questionInput = document.getElementById("question");
  const chatbox = document.getElementById("chatbox");
  const loader = document.getElementById("loader");

  const question = questionInput.value.trim();
  if (!question) {return};

  const userMsg = document.createElement("div");
  userMsg.className = "message";
  userMsg.innerHTML = `<span class="user">You:</span> <span class="bot">${question}</span>`;
  chatbox.appendChild(userMsg);
  chatbox.scrollTop = chatbox.scrollHeight;

  questionInput.value = "";
  loader.style.display = "block";

  try {
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const {url} = tab;

    const res = await fetch("http://localhost:5000/askIt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, question })
    });

    const data = await res.json();
    console.log(data)

    const botMsg = document.createElement("div");
    botMsg.className = "message";
    botMsg.innerHTML = `<span class="user">Bot:</span> <span class="bot">${data.answer || "No response"}</span>`;
    chatbox.appendChild(botMsg);
    chatbox.scrollTop = chatbox.scrollHeight;
  } catch (err) {
    const errorMsg = document.createElement("div");
    errorMsg.className = "message";
    errorMsg.innerHTML = `<span class="user">Bot:</span> <span class="bot">Error fetching answer</span>`;
    chatbox.appendChild(errorMsg);
  } finally {
    loader.style.display = "none";
  }
});


document.getElementById("help").addEventListener("click", () => {
  document.getElementById("modal").style.display = "flex";
});

document.getElementById("closePopup").addEventListener("click", () => {
  document.getElementById("modal").style.display = "none";
});
