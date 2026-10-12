// Google Antigravity Studio - Client Application

let socket = null;

document.addEventListener("DOMContentLoaded", () => {
    initWebSocket();
    loadStatus();
    loadConfig();
    loadSkills();
    loadProjects();
    loadAntigravityBridge();
    setupComposer();
});

function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        const statusEl = document.getElementById("runtimeStatus");
        if (statusEl) statusEl.innerText = "Antigravity Engine Online";
        const dot = document.querySelector(".status-dot");
        if (dot) dot.className = "status-dot online";
        const sendBtn = document.getElementById("sendBtn");
        if (sendBtn) sendBtn.disabled = false;
    };

    socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleAgentEvent(msg.type, msg.data);
        } catch (e) {
            console.error("Failed to parse websocket message:", e);
        }
    };

    socket.onclose = () => {
        const statusEl = document.getElementById("runtimeStatus");
        if (statusEl) statusEl.innerText = "Reconnecting to Antigravity...";
        const dot = document.querySelector(".status-dot");
        if (dot) dot.className = "status-dot offline";
        setTimeout(initWebSocket, 2000);
    };

    socket.onerror = (err) => {
        console.warn("WebSocket error:", err);
    };
}

function setupComposer() {
    const input = document.getElementById("promptInput");
    const slashMenu = document.getElementById("slashMenu");

    if (input) {
        input.addEventListener("input", () => {
            const val = input.value;
            if (val.startsWith("/") && val.length < 10 && !val.includes(" ")) {
                slashMenu.classList.remove("hidden");
            } else {
                slashMenu.classList.add("hidden");
            }
        });

        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                slashMenu.classList.add("hidden");
                submitPrompt();
            } else if (e.key === "Escape") {
                slashMenu.classList.add("hidden");
            }
        });
    }
}

function applySlash(cmd) {
    const input = document.getElementById("promptInput");
    const slashMenu = document.getElementById("slashMenu");
    if (input) {
        input.value = cmd;
        input.focus();
    }
    if (slashMenu) slashMenu.classList.add("hidden");
}

async function loadStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        const wsEl = document.getElementById("workspacePath");
        if (wsEl) wsEl.innerText = data.workspace_root;
    } catch (e) {
        console.error("Failed to fetch status:", e);
    }
}

async function loadSkills() {
    try {
        const res = await fetch("/api/skills");
        const skills = await res.json();
        const container = document.getElementById("skillsList");
        if (container && skills.length > 0) {
            container.innerHTML = skills.map(s => `<div class="skill-pill" title="${s.description}">${s.name}</div>`).join("");
        }
    } catch (e) {}
}

function handleAgentEvent(type, data) {
    const container = document.getElementById("messagesContainer");

    if (type === "thought") {
        // 1. Auxiliary Feed
        const thoughtStream = document.getElementById("thoughtStream");
        if (thoughtStream) {
            if (thoughtStream.querySelector(".empty-feed")) {
                thoughtStream.innerHTML = "";
            }
            const card = document.createElement("div");
            card.className = "thought-card";
            card.innerText = data.thought;
            thoughtStream.appendChild(card);
            thoughtStream.scrollTop = thoughtStream.scrollHeight;
        }

        // 2. Inline Accordion in Chat Canvas
        const thoughtCard = document.createElement("div");
        thoughtCard.className = "thought-accordion";
        thoughtCard.innerHTML = `
            <div class="thought-header">
                <span class="thought-pulse"></span>
                <span>Thinking</span>
            </div>
            <div class="thought-body" style="margin-top: 6px; font-size: 12px; color: #d8b4fe;">${escapeHtml(data.thought)}</div>
        `;
        container.appendChild(thoughtCard);
        container.scrollTop = container.scrollHeight;

    } else if (type === "tool_start") {
        const step = document.createElement("div");
        step.className = "tool-step-card";
        step.id = `tool-${data.call_id}`;
        step.innerHTML = `<span style="color: var(--agy-blue); font-weight: 600;">⚙ ${data.name}</span> <span style="color: var(--text-muted); font-size: 11px;">(executing...)</span>`;
        container.appendChild(step);
        container.scrollTop = container.scrollHeight;

    } else if (type === "tool_end") {
        const step = document.getElementById(`tool-${data.call_id}`);
        if (step) {
            const status = data.success ? "<span style='color: var(--agy-green);'>✔ Succeeded</span>" : "<span style='color: var(--agy-red);'>✖ Failed</span>";
            step.innerHTML = `<span style="color: var(--agy-blue); font-weight: 600;">⚙ ${data.name}</span> — ${status}`;

            // If file diff was produced, render visual diff card
            if (data.name === "replace_file_content" && data.output && data.output.includes("```diff")) {
                const diffBlock = document.createElement("div");
                diffBlock.className = "diff-view";
                diffBlock.innerHTML = formatDiff(data.output);
                step.appendChild(diffBlock);

                // Also populate Diffs Tab in Auxiliary Pane
                const diffsContainer = document.getElementById("diffsContainer");
                if (diffsContainer) {
                    if (diffsContainer.querySelector(".empty-feed")) diffsContainer.innerHTML = "";
                    const diffCard = document.createElement("div");
                    diffCard.className = "diff-view";
                    diffCard.innerHTML = formatDiff(data.output);
                    diffsContainer.appendChild(diffCard);
                }
            }
        }

        // Stream to Terminal Screen in Auxiliary Pane
        const term = document.getElementById("terminalLog");
        if (term) {
            term.innerText += `\n\n[$] ${data.name}\n${data.output}`;
            term.scrollTop = term.scrollHeight;
        }

    } else if (type === "chunk") {
        removeTypingIndicator();
        let streamingBubble = document.getElementById("streamingAssistantBubble");
        if (!streamingBubble) {
            streamingBubble = document.createElement("div");
            streamingBubble.id = "streamingAssistantBubble";
            streamingBubble.className = "message-bubble assistant streaming";
            streamingBubble.innerHTML = `<div class="bubble-body"></div>`;
            container.appendChild(streamingBubble);
        }
        const bodyEl = streamingBubble.querySelector(".bubble-body");
        if (bodyEl) {
            if (data.text) {
                streamingBubble.dataset.raw = data.text;
            } else if (data.delta) {
                streamingBubble.dataset.raw = (streamingBubble.dataset.raw || "") + data.delta;
            }
            bodyEl.innerHTML = renderMarkdown(streamingBubble.dataset.raw || "");
        }
        container.scrollTop = container.scrollHeight;

    } else if (type === "turn_complete") {
        removeTypingIndicator();
        const streamingBubble = document.getElementById("streamingAssistantBubble");
        if (streamingBubble) {
            streamingBubble.removeAttribute("id");
            streamingBubble.classList.remove("streaming");
            const bodyEl = streamingBubble.querySelector(".bubble-body");
            if (data.response && bodyEl) {
                bodyEl.innerHTML = renderMarkdown(data.response);
            }
        } else {
            appendAssistantMessage(data.response || "(Empty response)");
        }
        const sendBtn = document.getElementById("sendBtn");
        if (sendBtn) sendBtn.disabled = false;

        // Auto-detect project construction & activate Live Preview
        if (data.response && (data.response.includes(":5000") || data.response.includes("Constructed Project") || data.response.includes("running live"))) {
            setTimeout(() => {
                switchTab('preview');
                reloadPreview();
                loadProjects();
            }, 700);
        }

    } else if (type === "agent_error") {
        removeTypingIndicator();
        appendAssistantMessage(`⚠️ **Antigravity Error**: ${data.error}`);
        const sendBtn = document.getElementById("sendBtn");
        if (sendBtn) sendBtn.disabled = false;
    }
}

function submitPrompt() {
    const input = document.getElementById("promptInput");
    const text = input.value.trim();
    if (!text) return;

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert("Connecting to Antigravity engine... Please wait a second and retry.");
        initWebSocket();
        return;
    }

    appendUserMessage(text);
    showTypingIndicator();
    input.value = "";
    const sendBtn = document.getElementById("sendBtn");
    if (sendBtn) sendBtn.disabled = true;

    socket.send(JSON.stringify({ action: "prompt", prompt: text }));
}

function sendPrompt(text) {
    const input = document.getElementById("promptInput");
    if (input) {
        input.value = text;
        submitPrompt();
    }
}

function appendUserMessage(text) {
    const container = document.getElementById("messagesContainer");
    const hero = container.querySelector(".antigravity-hero");
    if (hero) hero.remove();

    const bubble = document.createElement("div");
    bubble.className = "message-bubble user";
    bubble.innerHTML = `<div class="bubble-body">${escapeHtml(text)}</div>`;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

function appendAssistantMessage(markdownText) {
    const container = document.getElementById("messagesContainer");
    const bubble = document.createElement("div");
    bubble.className = "message-bubble assistant";
    bubble.innerHTML = `<div class="bubble-body">${renderMarkdown(markdownText)}</div>`;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
    removeTypingIndicator();
    const container = document.getElementById("messagesContainer");
    const indicator = document.createElement("div");
    indicator.id = "typingIndicator";
    indicator.className = "message-bubble assistant";
    indicator.innerHTML = `
        <div class="bubble-body" style="display: flex; align-items: center; gap: 8px; color: var(--agy-blue);">
            <span class="thought-pulse"></span>
            <span>Antigravity agent is reasoning & executing tools...</span>
        </div>
    `;
    container.appendChild(indicator);
    container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
    const ind = document.getElementById("typingIndicator");
    if (ind) ind.remove();
}

function formatDiff(text) {
    const lines = text.split("\n");
    return lines.map(line => {
        if (line.startsWith("+")) {
            return `<div class="diff-add">${escapeHtml(line)}</div>`;
        } else if (line.startsWith("-")) {
            return `<div class="diff-del">${escapeHtml(line)}</div>`;
        }
        return `<div>${escapeHtml(line)}</div>`;
    }).join("");
}

function renderMarkdown(text) {
    if (!text) return "";
    try {
        if (typeof marked !== "undefined" && marked.parse) {
            return marked.parse(text);
        }
    } catch (e) {
        console.warn("marked.parse failed:", e);
    }

    let escaped = escapeHtml(text);
    escaped = escaped.replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    escaped = escaped.replace(/`([^`]+)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 2px 4px; border-radius: 4px;">$1</code>');
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    escaped = escaped.replace(/\n/g, '<br>');
    return escaped;
}

function clearMessages() {
    document.getElementById("messagesContainer").innerHTML = `
        <div class="antigravity-hero">
            <div class="hero-logo-glow">✦</div>
            <h1>Session Cleared</h1>
            <p>Antigravity orchestrator is ready for your next instruction.</p>
        </div>
    `;
    const stream = document.getElementById("thoughtStream");
    if (stream) stream.innerHTML = `<div class="empty-feed"><p>Real-time reasoning stream</p></div>`;
    const term = document.getElementById("terminalLog");
    if (term) term.innerText = "PS C:\\Users\\aryan\\.gemini\\antigravity\\scratch\\ashiee> _";

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: "clear" }));
    }
}

function switchTab(tabName) {
    document.querySelectorAll(".aux-tab").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-view").forEach(p => p.classList.remove("active"));

    const tabMap = {
        "thoughts": "thoughtsPane",
        "terminal": "terminalPane",
        "artifacts": "artifactsPane",
        "diffs": "diffsPane",
        "preview": "previewPane",
        "bridge": "bridgePane"
    };

    const target = document.getElementById(tabMap[tabName]);
    if (target) target.classList.add("active");

    const tabBtn = document.getElementById("tabBtn" + tabName.charAt(0).toUpperCase() + tabName.slice(1));
    if (tabBtn) {
        tabBtn.classList.add("active");
    } else if (typeof event !== "undefined" && event && event.currentTarget && event.currentTarget.classList.contains("aux-tab")) {
        event.currentTarget.classList.add("active");
    }
}

function reloadPreview() {
    const iframe = document.getElementById("previewIframe");
    if (iframe) {
        iframe.src = "http://127.0.0.1:5000";
    }
}

async function loadProjects() {
    try {
        const res = await fetch("/api/projects");
        const data = await res.json();
        const badge = document.getElementById("projectBadgeCard");
        if (badge && data.projects && data.projects.length > 0) {
            const p = data.projects[0];
            const dot = badge.querySelector(".project-indicator");
            const sub = badge.querySelector(".project-status-text");
            if (p.status === "online") {
                if (dot) dot.className = "project-indicator online";
                if (sub) sub.innerText = "Live (Port 5000) • Click to Preview ↗";
            } else if (p.status === "constructed") {
                if (dot) dot.className = "project-indicator amber";
                if (sub) sub.innerText = "Built • Ready to Launch";
            }
        }
    } catch (e) {}
}

async function loadConfig() {
    try {
        const res = await fetch("/api/config");
        const data = await res.json();
        const modelEl = document.getElementById("sidebarModelName");
        const statusEl = document.getElementById("sidebarModelStatus");
        const modalStatus = document.getElementById("settingsStatusText");

        if (data.has_api_key) {
            if (modelEl) modelEl.innerText = data.model_name || "Gemini 2.5 Flash";
            if (statusEl) statusEl.innerText = "Antigravity Cloud Connected 🟢";
            if (modalStatus) modalStatus.innerHTML = `<span style="color:var(--agy-green);">✔ Connected to Google Cloud Gemini (${data.masked_key})</span>`;
        } else {
            if (modelEl) modelEl.innerText = "Autonomous Synthesizer";
            if (statusEl) statusEl.innerText = "Antigravity Offline Engine ⚙";
            if (modalStatus) modalStatus.innerHTML = `<span style="color:var(--text-secondary);">Offline Synthesizer Active (Add API key for cloud models)</span>`;
        }

        const modelSelect = document.getElementById("modelSelect");
        if (modelSelect && data.model_name) modelSelect.value = data.model_name;
    } catch (e) {}
}

function openSettings() {
    const modal = document.getElementById("settingsModal");
    if (modal) {
        modal.classList.remove("hidden");
        loadConfig();
    }
}

function closeSettings() {
    const modal = document.getElementById("settingsModal");
    if (modal) modal.classList.add("hidden");
}

async function saveSettings() {
    const apiKey = document.getElementById("apiKeyInput").value.trim();
    const model = document.getElementById("modelSelect").value;
    const statusText = document.getElementById("settingsStatusText");

    if (statusText) statusText.innerText = "Connecting to Google Antigravity...";

    try {
        const res = await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: apiKey, model_name: model, provider: "gemini" })
        });
        const data = await res.json();
        if (data.success) {
            alert("Settings saved! Ashiee is connected to Google Antigravity & Gemini.");
            closeSettings();
            loadConfig();
            loadStatus();
        }
    } catch (e) {
        alert("Failed to save settings: " + e);
    }
}

function setNavView(view) {
    document.querySelectorAll(".rail-btn").forEach(b => b.classList.remove("active"));
    if (typeof event !== "undefined" && event && event.currentTarget) event.currentTarget.classList.add("active");
    if (view === "settings") {
        openSettings();
    }
}

async function loadAntigravityBridge() {
    try {
        const res = await fetch("/api/antigravity/bridge");
        const data = await res.json();
        const bridgeContent = document.getElementById("bridgeTelemetryContent");
        if (bridgeContent) {
            bridgeContent.innerHTML = `
                <div class="telemetry-grid">
                    <div class="telemetry-item">
                        <span class="telemetry-label">COLLABORATION LINK</span>
                        <span class="telemetry-val" style="color:var(--agy-green);">Active 🟢 (${data.bridge_mode})</span>
                    </div>
                    <div class="telemetry-item">
                        <span class="telemetry-label">IN-MEMORY LATENCY</span>
                        <span class="telemetry-val" style="color:var(--agy-blue);">${data.average_latency_ms} ms (Instant)</span>
                    </div>
                    <div class="telemetry-item">
                        <span class="telemetry-label">SHARED SKILLS</span>
                        <span class="telemetry-val">${data.shared_skills_count} Progressive Skills</span>
                    </div>
                    <div class="telemetry-item">
                        <span class="telemetry-label">ACCURACY RATING</span>
                        <span class="telemetry-val" style="color:var(--agy-green);">${data.accuracy_rating}</span>
                    </div>
                </div>
                <div class="domains-list">
                    <span class="group-title" style="margin-top:14px; display:block;">SYNCHRONIZED KNOWLEDGE DOMAINS</span>
                    ${data.shared_knowledge_domains.map(d => `<div class="domain-pill">✦ ${escapeHtml(d)}</div>`).join("")}
                </div>
            `;
        }
    } catch (e) {}
}

async function syncBridge() {
    try {
        const res = await fetch("/api/antigravity/sync", { method: "POST" });
        const data = await res.json();
        if (data.success) {
            loadAntigravityBridge();
            loadSkills();
            alert(`Antigravity Bridge Synced! ${data.shared_skills_count} shared skills refreshed.`);
        }
    } catch (e) {
        alert("Failed to sync bridge: " + e);
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
