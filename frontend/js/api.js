const API_BASE = window.location.origin;

const Api = {
    async healthCheck() {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
        return res.json();
    },

    async getDefaultSession() {
        const res = await fetch(`${API_BASE}/default-session`);
        if (!res.ok) throw new Error(`Default session failed: ${res.status}`);
        return res.json();
    },

    async getSessions() {
        const res = await fetch(`${API_BASE}/sessions`);
        if (!res.ok) throw new Error(`Sessions fetch failed: ${res.status}`);
        return res.json();
    },

    async askQuestion(sessionId, question) {
        const res = await fetch(`${API_BASE}/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, question }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Request failed: ${res.status}`);
        }
        return res.json();
    },
};
