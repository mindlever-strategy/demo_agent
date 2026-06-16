const API_BASE = window.location.origin;

let user = null;
let queryCount = 0;

const PROVIDER_MODELS = {
    openai: ["gpt-4o-mini", "gpt-4o"],
    anthropic: ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
    gemini: ["gemini-2.5-flash", "gemini-2.5-pro"],
    grok: ["grok-3-mini", "grok-3"],
};

const PROVIDER_NAMES = { openai: "OpenAI", anthropic: "Claude", gemini: "Gemini", grok: "Grok" };

const WELCOME_HTML = `
    <div class="welcome-container">
        <div class="welcome-logo">
            <svg width="44" height="44" viewBox="0 0 40 40" fill="none">
                <rect width="40" height="40" rx="10" fill="#c4a24a"/>
                <path d="M12 28V18L17 22V28M17 28V14L23 18V28M23 28V12L29 16V28" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h1 class="welcome-title">What can I help with?</h1>
        <div class="welcome-suggestions">
            <button class="suggestion-btn" data-query="Which clients are most profitable this quarter?">
                <span class="suggestion-text">Which clients are most profitable?</span>
                <svg class="suggestion-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7.8H7.8"/></svg>
            </button>
            <button class="suggestion-btn" data-query="What are the latest market trends in AI?">
                <span class="suggestion-text">Latest market trends in AI?</span>
                <svg class="suggestion-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7.8H7.8"/></svg>
            </button>
            <button class="suggestion-btn" data-query="Generate an executive summary of Q4 performance.">
                <span class="suggestion-text">Generate executive summary</span>
                <svg class="suggestion-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7.8H7.8"/></svg>
            </button>
            <button class="suggestion-btn" data-query="Write a Python function to merge two sorted arrays.">
                <span class="suggestion-text">Write a merge function in Python</span>
                <svg class="suggestion-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17l9.2-9.2M17 17V7.8H7.8"/></svg>
            </button>
        </div>
    </div>
`;

document.addEventListener("DOMContentLoaded", () => {
    const stored = sessionStorage.getItem("user");
    if (!stored) {
        window.location.href = "login.html";
        return;
    }

    user = JSON.parse(stored);

    document.getElementById("userName").textContent = user.name;
    document.getElementById("userRole").textContent = user.role;
    document.getElementById("userId").textContent = user.user_id;
    document.getElementById("sessionId").textContent = user.session_id;

    const chatForm = document.getElementById("chatForm");
    const messageInput = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const providerSelect = document.getElementById("providerSelect");
    const modelSelect = document.getElementById("modelSelect");
    const historyBtn = document.getElementById("historyBtn");
    const headerHistoryBtn = document.getElementById("headerHistoryBtn");
    const closeTraceBtn = document.getElementById("closeTraceBtn");
    const tracePanel = document.getElementById("tracePanel");
    const sidebar = document.getElementById("sidebar");
    const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");
    const metricApiKeyInput = document.getElementById("metricApiKeyInput");
    const clearChatBtn = document.getElementById("clearChatBtn");
    const headerClearChatBtn = document.getElementById("headerClearChatBtn");
    const chatMessages = document.getElementById("chatMessages");

    // Both side panels start open
    tracePanel.classList.add("open");
    loadTraces();

    const savedProvider = sessionStorage.getItem("selectedProvider") || "openai";
    const savedModel = sessionStorage.getItem("selectedModel") || "gpt-4o-mini";
    providerSelect.value = savedProvider;
    updateModelOptions(savedProvider);
    modelSelect.value = savedModel;
    updateModelBadge();

    const savedApiKey = sessionStorage.getItem("metricAiApiKey") || "";
    metricApiKeyInput.value = savedApiKey;
    metricApiKeyInput.addEventListener("input", () => {
        const key = metricApiKeyInput.value.trim();
        if (key) {
            sessionStorage.setItem("metricAiApiKey", key);
        } else {
            sessionStorage.removeItem("metricAiApiKey");
        }
    });

    // Sidebar toggle
    sidebarToggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("hidden");
    });
    sidebarCloseBtn.addEventListener("click", () => {
        sidebar.classList.add("hidden");
    });

    // Provider/model changes
    providerSelect.addEventListener("change", () => {
        const provider = providerSelect.value;
        updateModelOptions(provider);
        sessionStorage.setItem("selectedProvider", provider);
        sessionStorage.setItem("selectedModel", modelSelect.value);
        updateModelBadge();
    });

    modelSelect.addEventListener("change", () => {
        sessionStorage.setItem("selectedModel", modelSelect.value);
        updateModelBadge();
    });

    // Trace panel
    historyBtn.addEventListener("click", () => {
        tracePanel.classList.toggle("open");
        if (tracePanel.classList.contains("open")) loadTraces();
    });
    headerHistoryBtn.addEventListener("click", () => {
        tracePanel.classList.toggle("open");
        if (tracePanel.classList.contains("open")) loadTraces();
    });
    closeTraceBtn.addEventListener("click", () => {
        tracePanel.classList.remove("open");
    });

    const handleClearChat = () => clearChat(chatForm, messageInput, sendBtn);
    clearChatBtn.addEventListener("click", handleClearChat);
    headerClearChatBtn.addEventListener("click", handleClearChat);

    chatMessages.addEventListener("click", (e) => {
        const btn = e.target.closest(".suggestion-btn");
        if (!btn) return;
        messageInput.value = btn.dataset.query;
        autoResize(messageInput);
        sendBtn.disabled = false;
        chatForm.dispatchEvent(new Event("submit"));
    });

    // Logout
    logoutBtn.addEventListener("click", () => {
        sessionStorage.removeItem("user");
        sessionStorage.removeItem("selectedProvider");
        sessionStorage.removeItem("selectedModel");
        sessionStorage.removeItem("metricAiApiKey");
        window.location.href = "login.html";
    });

    // Textarea auto-resize
    messageInput.addEventListener("input", () => {
        autoResize(messageInput);
        sendBtn.disabled = messageInput.value.trim() === "";
    });

    // Enter to send, Shift+Enter for newline
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (messageInput.value.trim()) {
                chatForm.dispatchEvent(new Event("submit"));
            }
        }
    });

    // Form submit
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = messageInput.value.trim();
        if (!query) return;

        removeWelcome();
        appendMessage("user", query);
        messageInput.value = "";
        autoResize(messageInput);
        sendBtn.disabled = true;

        setAgentState("thinking", "Routing...", "", "Analyzing query...");

        const provider = providerSelect.value;
        const model = modelSelect.value;
        const metricAiApiKey = metricApiKeyInput.value.trim();
        const streamBubble = appendStreamingMessage();

        try {
            const res = await fetch(`${API_BASE}/api/stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: user.user_id,
                    session_id: user.session_id,
                    query: query,
                    provider: provider,
                    model: model,
                    ...(metricAiApiKey ? { metric_ai_api_key: metricAiApiKey } : {}),
                }),
            });

            if (!res.ok) {
                finalizeStreamingMessage(streamBubble, "Something went wrong. Please try again.", null);
                setAgentState("idle", "Error", "", "");
                sendBtn.disabled = false;
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let fullContent = "";
            let metaData = null;
            let doneData = null;
            let streamError = null;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop();

                let currentEvent = null;
                for (const line of lines) {
                    if (line.startsWith("event: ")) {
                        currentEvent = line.slice(7).trim();
                    } else if (line.startsWith("data: ") && currentEvent) {
                        const data = JSON.parse(line.slice(6));
                        if (currentEvent === "meta") {
                            metaData = data;
                            setAgentState("active", data.agent, data.agent_id, "Streaming...");
                        } else if (currentEvent === "token") {
                            fullContent += data.token;
                            updateStreamingBubble(streamBubble, fullContent);
                        } else if (currentEvent === "done") {
                            doneData = data;
                        } else if (currentEvent === "error") {
                            streamError = data.error;
                        }
                        currentEvent = null;
                    }
                }
            }

            if (streamError) {
                finalizeStreamingMessage(streamBubble, streamError, null);
                setAgentState("idle", "Error", "", "");
                sendBtn.disabled = false;
                messageInput.focus();
                return;
            }

            queryCount++;
            document.getElementById("queryCount").textContent = queryCount;

            const traceData = metaData && doneData ? { ...metaData, ...doneData } : null;
            finalizeStreamingMessage(streamBubble, fullContent, traceData);
            if (metaData) {
                setAgentState("active", metaData.agent, metaData.agent_id, "Responded");
            }
            loadTraces();
        } catch (err) {
            finalizeStreamingMessage(streamBubble, "Connection error. Is the server running?", null);
            setAgentState("idle", "Error", "", "");
        }

        sendBtn.disabled = false;
        messageInput.focus();
    });
});

function autoResize(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
}

function typingDotsHtml() {
    return '<div class="typing-indicator" aria-label="Thinking"><span></span><span></span><span></span></div>';
}

const MIN_TYPING_MS = 500;

function updateModelOptions(provider) {
    const modelSelect = document.getElementById("modelSelect");
    const models = PROVIDER_MODELS[provider] || PROVIDER_MODELS.openai;
    modelSelect.innerHTML = models.map(m => `<option value="${m}">${m}</option>`).join("");
}

function updateModelBadge() {
    const provider = document.getElementById("providerSelect").value;
    const model = document.getElementById("modelSelect").value;
    const dot = document.getElementById("modelDot");
    const name = document.getElementById("modelName");

    dot.className = `model-dot ${provider}`;
    name.textContent = `${PROVIDER_NAMES[provider]} · ${model}`;
}

function removeWelcome() {
    const welcome = document.querySelector(".welcome-container");
    if (welcome) {
        welcome.style.transition = "opacity 0.2s ease";
        welcome.style.opacity = "0";
        setTimeout(() => welcome.remove(), 200);
    }
}

function showWelcome() {
    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = WELCOME_HTML;
}

async function clearChat(chatForm, messageInput, sendBtn) {
    if (!confirm("Clear this conversation and start a new session?")) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/clear-chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: user.user_id }),
        });

        if (!res.ok) {
            alert("Could not start a new session. Please try again.");
            return;
        }

        const data = await res.json();
        user.session_id = data.session_id;
        sessionStorage.setItem("user", JSON.stringify(user));

        queryCount = 0;
        document.getElementById("sessionId").textContent = user.session_id;
        document.getElementById("queryCount").textContent = "0";
        setAgentState("idle", "Awaiting query...", "", "");

        showWelcome();
        messageInput.value = "";
        autoResize(messageInput);
        sendBtn.disabled = true;
        loadTraces();
    } catch (err) {
        alert("Connection error. Is the server running?");
    }
}

function appendMessage(role, content, traceData) {
    const chatMessages = document.getElementById("chatMessages");
    const msg = document.createElement("div");
    msg.className = `message message-${role}`;

    let metaHtml = "";
    let traceHtml = "";

    if (role === "agent" && traceData) {
        metaHtml = `
            <div class="message-meta">
                <span class="message-agent-badge">
                    <span class="badge-dot ${traceData.provider || 'openai'} small"></span>
                    ${traceData.agent}
                </span>
                <span class="message-time">${traceData.execution_time}s</span>
            </div>
        `;
        traceHtml = buildTraceHtml(traceData);
    }

    msg.innerHTML = `
        ${metaHtml}
        <div class="message-bubble">${formatContent(content)}</div>
        ${traceHtml}
    `;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendStreamingMessage() {
    const chatMessages = document.getElementById("chatMessages");
    const msg = document.createElement("div");
    msg.className = "message message-agent message-streaming message-waiting";
    msg.dataset.typingStarted = String(Date.now());
    msg.innerHTML = `
        <div class="message-meta" style="display:none"></div>
        <div class="message-bubble">${typingDotsHtml()}</div>
        <div class="trace-accordion-container"></div>
    `;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    requestAnimationFrame(() => {
        msg.scrollIntoView({ behavior: "smooth", block: "end" });
    });
    return msg;
}

function updateStreamingBubble(msgEl, content) {
    const bubble = msgEl.querySelector(".message-bubble");
    if (!content) {
        bubble.innerHTML = typingDotsHtml();
        msgEl.classList.add("message-waiting");
        return;
    }

    msgEl.dataset.streamContent = content;

    const renderContent = () => {
        const latest = msgEl.dataset.streamContent || content;
        msgEl.classList.remove("message-waiting");
        delete msgEl.dataset.typingTimer;
        bubble.innerHTML = formatContent(latest) + '<span class="streaming-cursor"></span>';
        const chatMessages = document.getElementById("chatMessages");
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    if (!msgEl.classList.contains("message-waiting")) {
        renderContent();
        return;
    }

    if (msgEl.dataset.typingTimer) {
        return;
    }

    const startedAt = Number(msgEl.dataset.typingStarted || Date.now());
    const delay = Math.max(0, MIN_TYPING_MS - (Date.now() - startedAt));

    if (delay > 0) {
        msgEl.dataset.typingTimer = String(setTimeout(renderContent, delay));
    } else {
        renderContent();
    }
}

function finalizeStreamingMessage(msgEl, content, traceData) {
    if (msgEl.dataset.typingTimer) {
        clearTimeout(Number(msgEl.dataset.typingTimer));
        delete msgEl.dataset.typingTimer;
    }
    msgEl.classList.remove("message-streaming", "message-waiting");
    const bubble = msgEl.querySelector(".message-bubble");
    bubble.innerHTML = formatContent(msgEl.dataset.streamContent || content);

    if (traceData) {
        const metaEl = msgEl.querySelector(".message-meta");
        metaEl.style.display = "";
        metaEl.innerHTML = `
            <span class="message-agent-badge">
                <span class="badge-dot ${traceData.provider || 'openai'} small"></span>
                ${traceData.agent}
            </span>
            <span class="message-time">${traceData.execution_time}s</span>
        `;
        const traceContainer = msgEl.querySelector(".trace-accordion-container");
        traceContainer.innerHTML = buildTraceHtml(traceData);
    }
}

function buildTraceHtml(traceData) {
    return `
        <div class="trace-accordion">
            <button class="trace-toggle" onclick="this.parentElement.classList.toggle('open')">
                <span>Execution Details</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
            </button>
            <div class="trace-details">
                <div class="trace-row"><span>Trace ID</span><span class="mono">${traceData.trace_id}</span></div>
                <div class="trace-row"><span>Agent</span><span>${traceData.agent}</span></div>
                <div class="trace-row"><span>Agent ID</span><span class="mono">${traceData.agent_id}</span></div>
                <div class="trace-row"><span>Provider</span><span class="provider-tag ${traceData.provider}">${traceData.provider}</span></div>
                <div class="trace-row"><span>Model</span><span class="mono">${traceData.model}</span></div>
                <div class="trace-row"><span>Execution Time</span><span>${traceData.execution_time_ms}ms</span></div>
                <div class="trace-row"><span>Session</span><span class="mono">${user.session_id}</span></div>
                <div class="trace-row"><span>MetricAI</span><span class="status-tracked">✓ Tracked</span></div>
            </div>
        </div>
    `;
}

function setAgentState(state, name, id, status) {
    const display = document.getElementById("agentDisplay");
    const nameEl = document.getElementById("agentName");
    const idEl = document.getElementById("agentId");
    const statusEl = document.getElementById("agentStatus");

    nameEl.textContent = name;
    idEl.textContent = id || "—";
    statusEl.textContent = status || "";

    display.classList.remove("active", "thinking");
    if (state === "active") display.classList.add("active");
    else if (state === "thinking") display.classList.add("thinking");
}

function formatContent(text) {
    return text
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
        .replace(/\n/g, "<br>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>");
}

async function loadTraces() {
    const content = document.getElementById("tracePanelContent");
    try {
        const res = await fetch(`${API_BASE}/api/traces?session_id=${user.session_id}`);
        const traces = await res.json();

        if (traces.length === 0) {
            content.innerHTML = '<p class="trace-empty">No traces for this session yet</p>';
            return;
        }

        content.innerHTML = traces.reverse().map(t => `
            <div class="trace-item">
                <div class="trace-item-header">
                    <span class="trace-item-agent">${t.agent_name}</span>
                    <span class="trace-item-time">${t.execution_time_ms}ms</span>
                </div>
                <div class="trace-item-query">${t.query}</div>
                <div class="trace-item-meta">
                    <span class="provider-tag ${t.provider}">${t.provider}</span>
                    <span class="trace-item-model">${t.model}</span>
                </div>
            </div>
        `).join("");
    } catch (err) {
        content.innerHTML = '<p class="trace-empty">Failed to load traces</p>';
    }
}
