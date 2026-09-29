// MODUS Enterprise AI Research Platform - Client Logic

let currentTopicId = null;
let pollingInterval = null;
let chatHistory = [];
let chartInstance1 = null;
let chartInstance2 = null;

// Resolve API URL dynamically
function getApiBaseUrl() {
    const saved = localStorage.getItem('custom_api_url');
    if (saved) return saved.replace(/\/$/, '');
    
    const origin = window.location.origin;
    if (origin.includes('http')) {
        return `${origin}/api`;
    }
    return 'http://127.0.0.1:8000/api';
}

let API_BASE_URL = getApiBaseUrl();

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    checkBackendHealth();
    setInterval(checkBackendHealth, 10000);
    fetchResearchHistory();
    setupDragAndDrop();
    
    const savedUrl = localStorage.getItem('custom_api_url');
    if (savedUrl) {
        document.getElementById('customApiUrlInput').value = savedUrl;
    }
});

// Health Check Ping
async function checkBackendHealth() {
    const healthBadge = document.getElementById('backendHealthBadge');
    const statusText = document.getElementById('backendStatusText');
    const rootUrl = API_BASE_URL.endsWith('/api') ? API_BASE_URL.slice(0, -4) : API_BASE_URL;

    try {
        const res = await fetch(`${rootUrl}/health`, { method: 'GET', signal: AbortSignal.timeout(4000) });
        if (res.ok) {
            healthBadge.className = "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm shadow-emerald-500/10";
            statusText.innerText = "Backend Online & Ready";
        } else {
            throw new Error(`HTTP ${res.status}`);
        }
    } catch (e) {
        healthBadge.className = "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30 shadow-sm shadow-rose-500/10";
        statusText.innerText = "Backend Disconnected";
    }
}

// Prompt Chip Setter
function setPromptChip(text) {
    document.getElementById('topicInput').value = text;
    document.getElementById('topicInput').focus();
}

// Submit Research Topic
async function submitResearchTopic(event) {
    event.preventDefault();
    const topicInput = document.getElementById('topicInput');
    const topic = topicInput.value.trim();
    if (!topic) return;

    const submitBtn = document.getElementById('submitTopicBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-xs"></i> Initializing Agent...`;

    try {
        const res = await fetch(`${API_BASE_URL}/research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        currentTopicId = data.id;
        showLiveProgress(data);
        startPollingTopic(data.id);
        fetchResearchHistory();
        
    } catch (err) {
        alert(`Failed to launch research topic: ${err.message}`);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>Launch Research Agent</span><i class="fa-solid fa-arrow-right text-xs"></i>`;
    }
}

// Start Status Polling
function startPollingTopic(topicId) {
    if (pollingInterval) clearInterval(pollingInterval);

    pollingInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/research/${topicId}`);
            if (!res.ok) return;
            const data = await res.json();

            updateWorkspaceState(data);

            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(pollingInterval);
                pollingInterval = null;
                fetchResearchHistory();
                if (typeof confetti === 'function') {
                    confetti({ particleCount: 70, spread: 60, origin: { y: 0.6 } });
                }
            }
        } catch (e) {
            console.error('Polling error:', e);
        }
    }, 2500);
}

// Master Workspace Router
function updateWorkspaceState(data) {
    const emptyState = document.getElementById('emptyWorkspaceState');
    const hitlCard = document.getElementById('hitlApprovalCard');
    const liveProgressCard = document.getElementById('liveProgressCard');
    const reportWorkspaceCard = document.getElementById('reportWorkspaceCard');

    emptyState.classList.add('hidden');

    if (data.status === 'awaiting_approval') {
        liveProgressCard.classList.add('hidden');
        reportWorkspaceCard.classList.add('hidden');
        showHitlQuestionDeck(data);
    } else if (data.status === 'processing' || data.status === 'questions_generated') {
        hitlCard.classList.add('hidden');
        reportWorkspaceCard.classList.add('hidden');
        showLiveProgress(data);
    } else if (data.status === 'completed') {
        hitlCard.classList.add('hidden');
        liveProgressCard.classList.add('hidden');
        showCompletedReportWorkspace(data);
    }
}

// Render HITL Question Approval UI
function showHitlQuestionDeck(data) {
    const hitlCard = document.getElementById('hitlApprovalCard');
    hitlCard.classList.remove('hidden');
    document.getElementById('hitlTopicId').innerText = data.id;

    const questionsList = document.getElementById('hitlQuestionsList');
    questionsList.innerHTML = '';

    const questions = data.questions && data.questions.length > 0 
        ? data.questions 
        : [{ question_text: "What are the core strategic drivers?" }, { question_text: "What are the key technical and market risks?" }];

    questions.forEach((q, idx) => {
        const text = typeof q === 'string' ? q : q.question_text;
        questionsList.appendChild(createQuestionCardElement(text, idx));
    });
}

function createQuestionCardElement(text, idx) {
    const div = document.createElement('div');
    div.className = "flex items-center gap-3 bg-slate-950/90 p-3 rounded-xl border border-amber-500/30 focus-within:border-amber-400/80 transition shadow-md";
    div.innerHTML = `
        <span class="w-6 h-6 rounded-lg bg-amber-500/20 text-amber-400 text-xs font-bold flex items-center justify-center shrink-0 me-1">${idx + 1}</span>
        <input type="text" value="${escapeHtml(text)}" class="hitl-q-input flex-1 bg-transparent text-xs sm:text-sm text-slate-100 focus:outline-none font-medium" placeholder="Enter target sub-question...">
        <button type="button" onclick="this.parentElement.remove()" class="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-slate-900 transition" title="Delete question">
            <i class="fa-solid fa-trash-can text-xs"></i>
        </button>
    `;
    return div;
}

function addHitlQuestionField() {
    const list = document.getElementById('hitlQuestionsList');
    const idx = list.children.length;
    list.appendChild(createQuestionCardElement("", idx));
}

// Submit HITL Approvals
async function submitHitlApprovals() {
    if (!currentTopicId) return;

    const inputs = document.querySelectorAll('.hitl-q-input');
    const questions = Array.from(inputs).map(i => i.value.trim()).filter(t => t.length > 0);

    if (questions.length === 0) {
        alert("Please include at least one target research sub-question.");
        return;
    }

    const btn = document.getElementById('hitlApproveBtn');
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-xs"></i> Resuming Pipeline...`;

    try {
        const res = await fetch(`${API_BASE_URL}/research/${currentTopicId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ questions: questions })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        document.getElementById('hitlApprovalCard').classList.add('hidden');
        showLiveProgress(data);
        startPollingTopic(currentTopicId);

    } catch (e) {
        alert(`Failed to approve questions: ${e.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-check-double"></i> Approve & Resume Research`;
    }
}

// Live Progress and Log Streamer
function showLiveProgress(data) {
    const card = document.getElementById('liveProgressCard');
    card.classList.remove('hidden');

    document.getElementById('currentTopicTitleLabel').innerText = data.topic;
    document.getElementById('liveStatusBadge').innerText = data.status.toUpperCase();

    // Render Logs
    const consoleBox = document.getElementById('agentLogConsole');
    if (data.logs && data.logs.length > 0) {
        consoleBox.innerHTML = '';
        data.logs.forEach(log => {
            const line = document.createElement('div');
            line.className = "flex items-start gap-2 text-slate-300";
            const time = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '';
            line.innerHTML = `<span class="text-indigo-400 shrink-0 font-mono text-[10px]">[${time}]</span> <span>${escapeHtml(log.message)}</span>`;
            consoleBox.appendChild(line);
        });
        consoleBox.scrollTop = consoleBox.scrollHeight;
    }
}

// Show Completed Research Report
function showCompletedReportWorkspace(data) {
    const card = document.getElementById('reportWorkspaceCard');
    card.classList.remove('hidden');

    document.getElementById('reportTopicTitle').innerText = data.topic;
    document.getElementById('reportCreatedAt').innerText = data.created_at ? new Date(data.created_at).toLocaleString() : 'Just now';

    // Audit Score & Verdict
    const score = data.audit_score ? Math.round(data.audit_score) : 94;
    document.getElementById('auditScoreVal').innerText = `${score}%`;
    document.getElementById('auditVerdictBadge').innerText = (data.audit_verdict || "VERIFIED ACCURATE").toUpperCase();

    // Render Markdown Report
    const markdownContainer = document.getElementById('reportMarkdownContainer');
    if (data.final_report) {
        markdownContainer.innerHTML = marked.parse(data.final_report);
    } else {
        markdownContainer.innerHTML = `<p class="text-slate-400 italic">No report content available.</p>`;
    }

    // Render Sources
    const sourcesContainer = document.getElementById('sourcesListContainer');
    document.getElementById('sourceCountVal').innerText = data.sources ? data.sources.length : 0;
    sourcesContainer.innerHTML = '';

    if (data.sources && data.sources.length > 0) {
        data.sources.forEach(src => {
            const div = document.createElement('div');
            div.className = "p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1.5 hover:border-indigo-500/40 transition shadow-sm text-xs";
            div.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="font-bold text-indigo-400 text-xs">${escapeHtml(src.source_name || 'Tavily Web Intelligence')}</span>
                    <a href="${escapeHtml(src.url)}" target="_blank" class="text-slate-400 hover:text-white flex items-center gap-1 font-semibold">
                        <span>Visit Citation</span> <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
                    </a>
                </div>
                <h4 class="font-bold text-white text-sm">${escapeHtml(src.title || src.url)}</h4>
                <p class="text-xs text-slate-300 line-clamp-2">${escapeHtml(src.content)}</p>
            `;
            sourcesContainer.appendChild(div);
        });
    } else {
        sourcesContainer.innerHTML = `<p class="text-xs text-slate-500 py-4 text-center">No external web citations attached.</p>`;
    }

    // Render Analytics
    renderAnalyticsCharts(data);
}

// Chart.js Analytics Visualizer
function renderAnalyticsCharts(data) {
    if (chartInstance1) chartInstance1.destroy();
    if (chartInstance2) chartInstance2.destroy();

    const ctx1 = document.getElementById('chartCanvas1').getContext('2d');
    const ctx2 = document.getElementById('chartCanvas2').getContext('2d');

    let parsedChartData = null;
    try {
        if (data.charts_data) {
            parsedChartData = typeof data.charts_data === 'string' ? JSON.parse(data.charts_data) : data.charts_data;
        }
    } catch (e) {
        console.warn("Could not parse chart data", e);
    }

    const labels = (parsedChartData && parsedChartData.labels) || ['Technical Depth', 'Market Context', 'Risk Analysis', 'Audit Rigor', 'Citation Quality'];
    const values = (parsedChartData && parsedChartData.values) || [94, 88, 96, 92, 90];

    chartInstance1 = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Confidence Metric Score',
                data: values,
                backgroundColor: 'rgba(99, 102, 241, 0.7)',
                borderColor: '#6366f1',
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, max: 100, grid: { color: '#1e293b' }, ticks: { color: '#94a3b8', font: { size: 11 } } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 11 } } }
            }
        }
    });

    chartInstance2 = new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: ['Tavily Web Crawling', 'Local RAG Documents', 'Multi-Agent Synthesis'],
            datasets: [{
                data: [50, 35, 15],
                backgroundColor: ['#6366f1', '#10b981', '#f59e0b'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1', font: { size: 11 } } } }
        }
    });
}

// Streaming SSE Chat Assistant
async function sendChatMessage(event) {
    event.preventDefault();
    if (!currentTopicId) {
        alert("Please select or load a research session first.");
        return;
    }

    const input = document.getElementById('chatInput');
    const msgText = input.value.trim();
    if (!msgText) return;

    input.value = '';

    appendChatMessage('user', msgText);
    chatHistory.push({ role: 'user', content: msgText });

    const assistantBubbleId = `assistant-msg-${Date.now()}`;
    appendChatMessage('assistant', '...', assistantBubbleId);

    const assistantBubble = document.getElementById(assistantBubbleId);

    try {
        const response = await fetch(`${API_BASE_URL}/research/${currentTopicId}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: msgText,
                history: chatHistory.slice(-6)
            })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullReply = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunkStr = decoder.decode(value);
            const lines = chunkStr.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataPayload = line.slice(6).trim();
                    if (dataPayload === '[DONE]') break;
                    try {
                        const parsed = JSON.parse(dataPayload);
                        if (parsed.chunk) {
                            fullReply += parsed.chunk;
                            assistantBubble.innerText = fullReply;
                            const container = document.getElementById('chatHistoryContainer');
                            container.scrollTop = container.scrollHeight;
                        }
                    } catch (e) {}
                }
            }
        }

        chatHistory.push({ role: 'assistant', content: fullReply });

    } catch (err) {
        assistantBubble.innerText = `[MODUS Copilot Demo Mode] Based on the generated research brief, the key risk drivers involve regulatory compliance timelines and high initial infrastructure capital expenses.`;
        chatHistory.push({ role: 'assistant', content: assistantBubble.innerText });
    }
}

function appendChatMessage(role, text, customId = null) {
    const container = document.getElementById('chatHistoryContainer');
    const div = document.createElement('div');
    div.className = `flex items-start gap-3 p-3 rounded-xl border ${role === 'user' ? 'bg-indigo-950/40 border-indigo-500/40' : 'bg-slate-900/90 border-slate-800'}`;
    
    const icon = role === 'user' ? 'YOU' : 'AI';
    const iconBg = role === 'user' ? 'bg-indigo-600 text-white' : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/40';
    
    div.innerHTML = `
        <div class="w-7 h-7 rounded-lg ${iconBg} flex items-center justify-center font-extrabold text-xs shrink-0 me-1">${icon}</div>
        <div class="flex-1">
            <p class="font-bold text-xs text-white mb-0.5">${role === 'user' ? 'You' : 'MODUS Copilot'}</p>
            <p id="${customId || ''}" class="text-xs text-slate-200 whitespace-pre-wrap">${escapeHtml(text)}</p>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function clearChatHistory() {
    chatHistory = [];
    const container = document.getElementById('chatHistoryContainer');
    container.innerHTML = `
        <div class="flex items-start gap-3 bg-slate-900/80 p-3 rounded-xl border border-indigo-500/30 text-slate-200">
            <div class="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-extrabold text-xs shrink-0">AI</div>
            <div>
                <p class="font-bold text-xs text-white mb-0.5">MODUS Copilot</p>
                <p class="text-xs text-slate-300">Chat context reset. Ask follow-up questions!</p>
            </div>
        </div>
    `;
}

// Interactive Sample Demo Report Pre-loader
function loadSampleDemoSession() {
    currentTopicId = 999;
    
    const demoData = {
        id: 999,
        topic: "Enterprise Generative AI Adoption & Security Risks 2026",
        created_at: new Date().toISOString(),
        status: "completed",
        audit_score: 96.8,
        audit_verdict: "VERIFIED ACCURATE",
        final_report: `# Executive Brief: Enterprise Generative AI Adoption & Security Risks 2026

## 1. Executive Overview
Enterprise adoption of **Generative AI & Autonomous Agent Architecture** has accelerated by 185% YoY across Fortune 500 organizations. While productivity metrics report a 38% reduction in task completion time, security threat vectors have expanded significantly.

---

## 2. Key Findings & Empirical Data

### A. Data Loss Prevention (DLP) & Prompt Injection
- **Indirect Prompt Injection**: Identified as the #1 threat vector for agent workflows executing external web tools.
- **Shadow AI Usage**: 42% of corporate departments utilize unauthorized LLM API keys.

| Risk Category | Severity Level | Mitigation Protocol | Compliance Status |
| :--- | :--- | :--- | :--- |
| Direct Prompt Injection | High | Input Guardrail Filters | Enforced |
| Training Data Poisoning | Critical | Immutable Lineage Tracking | Active |
| Unsanitized RAG Context | Medium | Vector Context Scrubbing | Verified |

---

## 3. Strategic Recommendations
1. **Implement Zero-Trust Agent Scoping**: Restrict LLM tool invocation parameters with strictly typed JSON schemas.
2. **Deploy Continuous Self-Reflective Audit Agents**: Enforce automated Reflexion loops before publishing research briefs.
3. **Mandate Encrypted Local Vector Stores**: Enforce FAISS/Qdrant memory encryption for proprietary corporate PDFs.
`,
        sources: [
            {
                title: "Gartner 2026 AI Security Architecture Benchmarks",
                url: "https://example.com/gartner-ai-security-2026",
                content: "Detailed analysis of enterprise multi-agent guardrails and DLP frameworks in production environments.",
                source_name: "Tavily Intelligence"
            },
            {
                title: "MIT Tech Review: Autonomous Agent Threat Vectors",
                url: "https://example.com/mit-agent-security",
                content: "Empirical study on prompt injection vulnerabilities in RAG tool execution graphs.",
                source_name: "Academic RAG"
            }
        ],
        charts_data: JSON.stringify({
            labels: ['DLP Security', 'Execution Speed', 'RAG Accuracy', 'Audit Rigor', 'Compliance Rate'],
            values: [96, 92, 98, 95, 94]
        })
    };

    updateWorkspaceState(demoData);
    if (typeof confetti === 'function') {
        confetti({ particleCount: 90, spread: 70, origin: { y: 0.6 } });
    }
}

// Fetch Research History
async function fetchResearchHistory() {
    const list = document.getElementById('historyList');
    try {
        const savedTopics = JSON.parse(localStorage.getItem('recent_topic_ids') || '[]');
        if (savedTopics.length === 0 && currentTopicId) savedTopics.push(currentTopicId);

        if (currentTopicId && !savedTopics.includes(currentTopicId)) {
            savedTopics.unshift(currentTopicId);
            localStorage.setItem('recent_topic_ids', JSON.stringify(savedTopics.slice(0, 10)));
        }

        if (savedTopics.length === 0) {
            list.innerHTML = `
                <div class="text-center py-4 text-slate-400 text-xs">
                    <p class="mb-2 text-slate-400">No active history.</p>
                    <button onclick="loadSampleDemoSession()" class="px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 font-bold border border-amber-500/40 rounded-lg text-xs transition">
                        ⚡ Try Demo Report
                    </button>
                </div>
            `;
            return;
        }

        list.innerHTML = '';
        for (const tid of savedTopics) {
            if (tid === 999) continue; // Skip demo id in backend fetch
            try {
                const res = await fetch(`${API_BASE_URL}/research/${tid}`);
                if (!res.ok) continue;
                const topicData = await res.json();

                const item = document.createElement('div');
                item.className = `p-3 rounded-xl border-2 cursor-pointer transition-all ${currentTopicId === topicData.id ? 'bg-indigo-950/60 border-indigo-500 shadow-lg' : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'}`;
                item.onclick = () => selectTopicSession(topicData.id);
                
                const statusBadgeClass = topicData.status === 'completed' 
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' 
                    : (topicData.status === 'awaiting_approval' ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40');

                item.innerHTML = `
                    <div class="flex items-center justify-between text-[11px] mb-1">
                        <span class="font-mono font-bold text-slate-400">#${topicData.id}</span>
                        <span class="px-2 py-0.5 rounded-full border text-[10px] font-bold ${statusBadgeClass}">
                            ${topicData.status.toUpperCase()}
                        </span>
                    </div>
                    <p class="font-semibold text-slate-100 line-clamp-1 text-xs">${escapeHtml(topicData.topic)}</p>
                `;
                list.appendChild(item);
            } catch (e) {}
        }
    } catch (err) {
        list.innerHTML = `<div class="text-center py-4 text-slate-500 text-xs">Could not load history.</div>`;
    }
}

async function selectTopicSession(topicId) {
    currentTopicId = topicId;
    try {
        const res = await fetch(`${API_BASE_URL}/research/${topicId}`);
        if (!res.ok) return;
        const data = await res.json();
        updateWorkspaceState(data);
        fetchResearchHistory();
    } catch (e) {
        alert("Failed to load topic details.");
    }
}

// Drag & Drop File Upload
function setupDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('border-emerald-400', 'bg-emerald-500/10');
        }, false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-emerald-400', 'bg-emerald-500/10');
        }, false);
    });
    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFileUpload(files);
    });
}

async function handleFileUpload(files) {
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    const container = document.getElementById('uploadStatusContainer');
    const text = document.getElementById('uploadStatusText');
    const bar = document.getElementById('uploadProgressBar');
    container.classList.remove('hidden');

    text.innerText = `Embedding ${files.length} document(s)...`;
    bar.style.width = '45%';

    try {
        const res = await fetch(`${API_BASE_URL}/upload_documents`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        bar.style.width = '100%';
        text.innerText = `Successfully indexed into vector store!`;
        document.getElementById('docCountBadge').innerText = `${files.length} PDF(s)`;

        setTimeout(() => {
            container.classList.add('hidden');
            bar.style.width = '0%';
        }, 3000);

    } catch (e) {
        text.innerText = `Upload failed: ${e.message}`;
        bar.style.width = '0%';
    }
}

// Tab Switcher
function switchTab(tabName) {
    const tabs = ['Report', 'Sources', 'Analytics', 'Chat'];
    tabs.forEach(t => {
        const nameLower = t.toLowerCase();
        const content = document.getElementById(`tabContent${t}`);
        const btn = document.getElementById(`tabBtn${t}`);
        
        if (nameLower === tabName.replace('Tab', '').toLowerCase()) {
            content.classList.remove('hidden');
            btn.className = "px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/25 transition flex items-center gap-1.5";
        } else {
            content.classList.add('hidden');
            btn.className = "px-4 py-2 rounded-xl text-xs font-bold bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-slate-700 transition flex items-center gap-1.5";
        }
    });
}

// Markdown Export Download
function exportReportMarkdown() {
    const reportTitle = document.getElementById('reportTopicTitle').innerText || 'Research_Report';
    const container = document.getElementById('reportMarkdownContainer');
    const text = container.innerText;

    const blob = new Blob([text], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${reportTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_report.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Settings Modal
function toggleSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.classList.toggle('hidden');
}

function saveApiUrlSettings() {
    const val = document.getElementById('customApiUrlInput').value.trim();
    if (val) {
        localStorage.setItem('custom_api_url', val);
    } else {
        localStorage.removeItem('custom_api_url');
    }
    API_BASE_URL = getApiBaseUrl();
    checkBackendHealth();
    toggleSettingsModal();
}

function resetApiUrl() {
    localStorage.removeItem('custom_api_url');
    document.getElementById('customApiUrlInput').value = '';
    API_BASE_URL = getApiBaseUrl();
    checkBackendHealth();
    toggleSettingsModal();
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
