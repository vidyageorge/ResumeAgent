const chatContainer = document.getElementById("chatContainer");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

let ws = null;
let isConnected = false;

function connectWebSocket() {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  ws = new WebSocket(`${protocol}//${location.host}/ws`);

  ws.onopen = () => {
    isConnected = true;
    statusDot.classList.add("connected");
    statusText.textContent = "Connected";
  };

  ws.onclose = () => {
    isConnected = false;
    statusDot.classList.remove("connected");
    statusText.textContent = "Disconnected — retrying...";
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = () => {
    statusText.textContent = "Connection error";
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    removeTyping();
    appendMessage("assistant", data.reply);
    setLoading(false);
  };
}

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = formatMarkdown(text);
  div.appendChild(bubble);
  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function formatMarkdown(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

function showTyping() {
  const div = document.createElement("div");
  div.className = "message assistant typing";
  div.id = "typingIndicator";
  div.innerHTML = '<div class="bubble">Thinking</div>';
  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function setLoading(loading) {
  sendBtn.disabled = loading;
  messageInput.disabled = loading;
}

async function sendViaHttp(message) {
  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await response.json();
  return data.reply;
}

async function sendMessage(message) {
  appendMessage("user", message);
  showTyping();
  setLoading(true);

  try {
    if (isConnected && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ message }));
    } else {
      const reply = await sendViaHttp(message);
      removeTyping();
      appendMessage("assistant", reply);
      setLoading(false);
    }
  } catch (err) {
    removeTyping();
    appendMessage("assistant", `Error: ${err.message}`);
    setLoading(false);
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;
  messageInput.value = "";
  sendMessage(message);
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});

connectWebSocket();

fetch("/health")
  .then((r) => r.json())
  .then((data) => {
    if (data.browser_active) {
      statusText.textContent = data.logged_in
        ? "Connected · Logged in to Naukri"
        : "Connected · Browser running";
    }
  })
  .catch(() => {});
