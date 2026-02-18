const Chat = {
    container: null,
    welcomeState: null,
    messages: [],

    init() {
        this.container = document.getElementById("chatContainer");
        this.welcomeState = document.getElementById("welcomeState");
    },

    clear() {
        this.messages = [];
        this.container.innerHTML = "";
        this.container.appendChild(this.welcomeState);
        this.welcomeState.classList.remove("hidden");
        Toast.show("Chat cleared", "info");
    },

    hideWelcome() {
        if (this.welcomeState && !this.welcomeState.classList.contains("hidden")) {
            this.welcomeState.classList.add("hidden");
        }
    },

    addUserMessage(text) {
        this.hideWelcome();
        this.messages.push({ role: "user", content: text });

        const el = document.createElement("div");
        el.className = "chat-msg chat-user";
        el.innerHTML = `
            <div class="chat-bubble">
                <p>${this.escapeHtml(text)}</p>
            </div>
        `;
        this.container.appendChild(el);
        this.scrollToBottom();
    },

    addBotMessage(data) {
        this.messages.push({ role: "assistant", ...data });

        const confidence = data.confidence || 0;
        const level = this.getConfidenceLevel(confidence);
        const badge = this.confidenceBadge(level, confidence);
        const timeStr = data.response_time_ms ? `${data.response_time_ms.toFixed(0)}ms` : "—";

        let sourcesHtml = "";
        if (data.sources && data.sources.length > 0) {
            sourcesHtml = `
                <details class="mt-3">
                    <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition-colors">📄 View Sources (${data.sources.length})</summary>
                    <div class="mt-2 flex flex-wrap">${data.sources.map(s => `<span class="source-chip">${this.escapeHtml(s)}</span>`).join("")}</div>
                </details>
            `;
        }

        const answerHtml = this.formatAnswer(data.answer || "No answer received.");

        const el = document.createElement("div");
        el.className = "chat-msg chat-bot";
        el.innerHTML = `
            <div class="chat-bubble">
                ${answerHtml}
                ${sourcesHtml}
                <div class="chat-meta">
                    ${badge}
                    <span>⏱️ ${timeStr}</span>
                </div>
            </div>
        `;
        this.container.appendChild(el);
        this.scrollToBottom();
    },

    addTypingIndicator() {
        this.hideWelcome();
        const el = document.createElement("div");
        el.className = "chat-msg chat-bot";
        el.id = "typingMsg";
        el.innerHTML = `
            <div class="chat-bubble flex items-center gap-2">
                <span class="text-sm text-gray-400">Searching knowledge base</span>
                <span class="flex gap-1">
                    <span class="w-1.5 h-1.5 bg-accent rounded-full animate-typing" style="animation-delay:0ms"></span>
                    <span class="w-1.5 h-1.5 bg-accent rounded-full animate-typing" style="animation-delay:200ms"></span>
                    <span class="w-1.5 h-1.5 bg-accent rounded-full animate-typing" style="animation-delay:400ms"></span>
                </span>
            </div>
        `;
        this.container.appendChild(el);
        this.scrollToBottom();
    },

    removeTypingIndicator() {
        const el = document.getElementById("typingMsg");
        if (el) el.remove();
    },

    addErrorMessage(text) {
        const el = document.createElement("div");
        el.className = "chat-msg chat-bot";
        el.innerHTML = `
            <div class="chat-bubble border-red-500/30">
                <p class="text-red-400">⚠️ ${this.escapeHtml(text)}</p>
            </div>
        `;
        this.container.appendChild(el);
        this.scrollToBottom();
    },

    formatAnswer(text) {
        return text
            .split("\n")
            .filter(line => line.trim() !== "")
            .map(line => {
                if (line.startsWith("•") || line.startsWith("-")) {
                    return `<p class="pl-4 border-l-2 border-accent/30 my-1">${this.escapeHtml(line)}</p>`;
                }
                if (line.startsWith("**") && line.endsWith("**")) {
                    return `<p class="font-semibold text-white">${this.escapeHtml(line.slice(2, -2))}</p>`;
                }
                return `<p>${this.escapeHtml(line)}</p>`;
            })
            .join("");
    },

    getConfidenceLevel(score) {
        if (score >= 0.55) return "high";
        if (score >= 0.35) return "medium";
        return "low";
    },

    confidenceBadge(level, score) {
        const icons = { high: "✅", medium: "⚠️", low: "🔶" };
        const classes = { high: "confidence-high", medium: "confidence-medium", low: "confidence-low" };
        const pct = (score * 100).toFixed(0);
        return `<span class="confidence-badge ${classes[level]}">${icons[level]} ${level.toUpperCase()} (${pct}%)</span>`;
    },

    scrollToBottom() {
        requestAnimationFrame(() => {
            this.container.scrollTop = this.container.scrollHeight;
        });
    },

    escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    },
};

const Toast = {
    container: null,

    init() {
        this.container = document.getElementById("toastContainer");
    },

    show(message, type = "info", duration = 3000) {
        const el = document.createElement("div");
        el.className = `toast toast-${type}`;
        const icons = { success: "✅", error: "❌", info: "ℹ️" };
        el.innerHTML = `<span>${icons[type] || "ℹ️"} ${message}</span>`;
        this.container.appendChild(el);

        setTimeout(() => {
            el.style.opacity = "0";
            el.style.transform = "translateY(12px)";
            el.style.transition = "all 0.3s ease";
            setTimeout(() => el.remove(), 300);
        }, duration);
    },
};
