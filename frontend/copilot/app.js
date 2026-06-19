const chatContainer = document.getElementById("chatContainer");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const agentNav = document.getElementById("agentNav");
const indexBtn = document.getElementById("indexBtn");

let sessionId = localStorage.getItem("vidya_session") || null;
let selectedAgent = "";
let ws = null;
let connected = false;

const API_KEY = localStorage.getItem("vidya_api_key") || "dev-local-key";

function connectWs() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  ws = new WebSocket(`${proto}//${location.host}/ws`);

  ws.onopen = () => {
    connected = true;
    statusDot.classList.add("ok");
    statusText.textContent = "Connected";
  };

  ws.onclose = () => {
    connected = false;
    statusDot.classList.remove("ok");
    statusText.textContent = "Reconnecting...";
    setTimeout(connectWs, 3000);
  };

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    removeTyping();
    if (data.session_id) {
      sessionId = data.session_id;
      localStorage.setItem("vidya_session", sessionId);
    }
    appendMessage("assistant", data.reply, data.agent);
    setLoading(false);
  };
}

agentNav.addEventListener("click", (e) => {
  const btn = e.target.closest(".agent-btn");
  if (!btn) return;
  agentNav.querySelectorAll(".agent-btn").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  selectedAgent = btn.dataset.agent;
});

indexBtn.addEventListener("click", async () => {
  indexBtn.disabled = true;
  indexBtn.textContent = "Indexing...";
  try {
    const res = await fetch("/api/codebase/index", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
      body: JSON.stringify({}),
    });
    const data = await res.json();
    appendMessage("assistant", `Indexed ${data.files_scanned || 0} files (${data.chunks_indexed || 0} chunks).`);
  } catch (err) {
    appendMessage("assistant", `Index error: ${err.message}`);
  }
  indexBtn.disabled = false;
  indexBtn.textContent = "Index Workspace";
});

function appendMessage(role, text, agent) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (agent && role === "assistant") {
    const tag = document.createElement("div");
    tag.className = "agent-tag";
    tag.textContent = agent;
    bubble.appendChild(tag);
  }
  const content = document.createElement("div");
  content.innerHTML = formatText(text);
  bubble.appendChild(content);
  div.appendChild(bubble);
  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function formatText(text) {
  return text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}

function showTyping() {
  const div = document.createElement("div");
  div.className = "msg assistant typing";
  div.id = "typing";
  div.innerHTML = '<div class="bubble">Thinking</div>';
  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTyping() {
  document.getElementById("typing")?.remove();
}

function setLoading(on) {
  sendBtn.disabled = on;
  messageInput.disabled = on;
}

async function sendHttp(message) {
  const body = { message, session_id: sessionId };
  if (selectedAgent) body.agent = selectedAgent;
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function sendMessage(message) {
  appendMessage("user", message);
  showTyping();
  setLoading(true);

  try {
    if (connected && ws?.readyState === WebSocket.OPEN) {
      const payload = { message, session_id: sessionId };
      if (selectedAgent) payload.agent = selectedAgent;
      ws.send(JSON.stringify(payload));
    } else {
      const data = await sendHttp(message);
      removeTyping();
      if (data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem("vidya_session", sessionId);
      }
      appendMessage("assistant", data.reply, data.agent);
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
  const msg = messageInput.value.trim();
  if (!msg) return;
  messageInput.value = "";
  sendMessage(msg);
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});

connectWs();

fetch("/health").then((r) => r.json()).then((d) => {
  if (d.ollama?.model_available) {
    statusText.textContent = `Connected · ${d.ollama.configured_model}`;
  } else if (d.ollama?.status === "error") {
    statusText.textContent = "Ollama offline — start Ollama first";
  }
}).catch(() => {});
