const SUGGESTED_QUESTIONS = [
    "What is the attendance policy?",
    "How do I apply for hostel accommodation?",
    "What are the exam regulations?",
    "Is ragging allowed on campus?",
    "What programs does Karunya offer?",
    "What is the library book issue period?",
    "How to contact university support?",
    "What is the dress code policy?",
];

const SESSION_ID = "karunya_main";

let queryCount = 0;
let totalConfidence = 0;
let totalResponseTime = 0;

document.addEventListener("DOMContentLoaded", () => {
    Chat.init();
    Toast.init();
    renderSuggestedQuestions();
    bindEvents();
    checkHealth();
});

function renderSuggestedQuestions() {
    const container = document.getElementById("suggestedQuestions");
    container.innerHTML = SUGGESTED_QUESTIONS.map(
        q => `<button class="suggested-btn" data-question="${q}">${q}</button>`
    ).join("");

    container.addEventListener("click", (e) => {
        const btn = e.target.closest(".suggested-btn");
        if (btn) {
            const question = btn.dataset.question;
            document.getElementById("chatInput").value = question;
            handleSubmit(question);
        }
    });
}

function bindEvents() {
    document.getElementById("chatForm").addEventListener("submit", (e) => {
        e.preventDefault();
        const input = document.getElementById("chatInput");
        const question = input.value.trim();
        if (question.length >= 3) {
            handleSubmit(question);
            input.value = "";
        }
    });

    document.getElementById("clearChatBtn").addEventListener("click", () => {
        Chat.clear();
        queryCount = 0;
        totalConfidence = 0;
        totalResponseTime = 0;
        updateSidebarAnalytics();
        updateMetrics({});
    });

    document.getElementById("themeToggle").addEventListener("click", toggleTheme);

    document.getElementById("sidebarToggle").addEventListener("click", () => {
        const sidebar = document.getElementById("sidebar");
        sidebar.classList.toggle("hidden");
    });
}

async function handleSubmit(question) {
    Chat.addUserMessage(question);
    Chat.addTypingIndicator();
    setInputState(true);

    try {
        const data = await Api.askQuestion(SESSION_ID, question);
        Chat.removeTypingIndicator();
        Chat.addBotMessage(data);

        queryCount++;
        totalConfidence += data.confidence || 0;
        totalResponseTime += data.response_time_ms || 0;

        updateMetrics(data);
        updateSidebarAnalytics();
        Toast.show(`Answered in ${(data.response_time_ms || 0).toFixed(0)}ms`, "success");
    } catch (err) {
        Chat.removeTypingIndicator();
        Chat.addErrorMessage(err.message || "Failed to get answer. Is the backend running?");
        Toast.show("Request failed", "error");
    } finally {
        setInputState(false);
    }
}

function setInputState(loading) {
    const input = document.getElementById("chatInput");
    const btn = document.getElementById("sendBtn");
    input.disabled = loading;
    btn.disabled = loading;
    if (loading) {
        input.placeholder = "Searching...";
    } else {
        input.placeholder = "Ask anything about Karunya University...";
        input.focus();
    }
}

function updateMetrics(data) {
    if (data.confidence !== undefined) {
        const pct = (data.confidence * 100).toFixed(0);
        document.getElementById("metricConfidence").textContent = `${pct}%`;
    }
    if (data.response_time_ms !== undefined) {
        document.getElementById("metricTime").textContent = `${data.response_time_ms.toFixed(0)}ms`;
    }
}

function updateSidebarAnalytics() {
    document.getElementById("statQueries").textContent = queryCount;

    if (queryCount > 0) {
        const avgConf = ((totalConfidence / queryCount) * 100).toFixed(0);
        const avgTime = (totalResponseTime / queryCount).toFixed(0);
        document.getElementById("statConfidence").textContent = `${avgConf}%`;
        document.getElementById("statResponseTime").textContent = `${avgTime}ms`;
    } else {
        document.getElementById("statConfidence").textContent = "—";
        document.getElementById("statResponseTime").textContent = "—";
    }
}

async function checkHealth() {
    const badge = document.getElementById("statusBadge");
    try {
        const data = await Api.healthCheck();
        badge.textContent = "Online";
        badge.className = "text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-400";

        const session = await Api.getDefaultSession();
        if (session.chunk_count) {
            document.getElementById("metricChunks").textContent = session.chunk_count;
        }
        if (session.compression_ratio) {
            document.getElementById("metricCompression").textContent = `${session.compression_ratio.toFixed(1)}%`;
        }
    } catch {
        badge.textContent = "Offline";
        badge.className = "text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-400";
        Toast.show("Backend is offline. Start the server first.", "error", 5000);
    }
}

function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById("themeIcon");
    const label = document.getElementById("themeLabel");

    if (html.classList.contains("dark")) {
        html.classList.remove("dark");
        html.classList.add("light");
        icon.textContent = "☀️";
        label.textContent = "Light Mode";
    } else {
        html.classList.remove("light");
        html.classList.add("dark");
        icon.textContent = "🌙";
        label.textContent = "Dark Mode";
    }
}
