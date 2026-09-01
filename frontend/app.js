/**
 * FinIntel Dynamic Frontend Application Script
 * Orchestrates Real-Time WebSockets, Multi-Agent Synthesis, Charting, RAG Search & Persona Modeling
 */

const API_BASE = window.location.origin;

// Application State
const state = {
  currentSymbol: "RELIANCE",
  currentPersona: "MODERATE",
  stocks: {},
  personas: {},
  simulationFlags: {
    simulate_feed_failure: false,
    simulate_missing_filing: false,
    simulate_signal_conflict: false
  },
  chart: null,
  activeTab: "overview",
  wsConnected: false
};

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
  initLucideIcons();
  fetchInitialData();
  setupEventListeners();
  initWebSocket();
  startClock();
});

function initLucideIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function startClock() {
  const clockEl = document.getElementById("istClock");
  setInterval(() => {
    const now = new Date();
    const istTime = now.toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour12: false });
    if (clockEl) clockEl.textContent = `${istTime} IST`;
  }, 1000);
}

// Fetch Initial Data
async function fetchInitialData() {
  try {
    const [stocksRes, personasRes] = await Promise.all([
      fetch(`${API_BASE}/api/stocks`).then(r => r.json()),
      fetch(`${API_BASE}/api/personas`).then(r => r.json())
    ]);

    state.stocks = stocksRes.stocks || {};
    state.personas = personasRes.personas || {};

    renderTickerTape();
    renderStockPills();
    renderPersonaPills();
    
    // Trigger initial synthesis
    await triggerSynthesis();
    await loadChartData();
    renderScreenerTable();
  } catch (err) {
    console.error("Failed to fetch initial data:", err);
  }
}

// Render Top Streaming Ticker Marquee
function renderTickerTape() {
  const tape = document.getElementById("tickerTape");
  if (!tape) return;

  const stockList = Object.values(state.stocks);
  const itemsHtml = stockList.map(s => {
    const isUp = s.change_pct >= 0;
    const colorClass = isUp ? "text-emerald-400" : "text-rose-400";
    const arrow = isUp ? "▲" : "▼";
    return `
      <div class="ticker-item" id="ticker-${s.symbol}" onclick="switchStock('${s.symbol}')">
        <span class="font-bold text-slate-200">${s.symbol}</span>
        <span class="mono text-slate-300">₹${s.cmp.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
        <span class="mono font-semibold ${colorClass}">${arrow} ${s.change_pct > 0 ? '+' : ''}${s.change_pct.toFixed(2)}%</span>
      </div>
    `;
  }).join('');

  // Duplicate for seamless infinite loop
  tape.innerHTML = itemsHtml + itemsHtml;
}

// Render Quick Stock Selector Buttons
function renderStockPills() {
  const container = document.getElementById("stockPills");
  if (!container) return;

  container.innerHTML = Object.keys(state.stocks).map(sym => {
    const s = state.stocks[sym];
    const isActive = sym === state.currentSymbol;
    return `
      <button onclick="switchStock('${sym}')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-2 ${
        isActive 
          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm shadow-cyan-500/20' 
          : 'bg-slate-800/60 text-slate-400 border border-slate-700/50 hover:bg-slate-800 hover:text-slate-200'
      }">
        <span>${sym}</span>
        <span class="mono text-[11px] ${s.change_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
          ${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(1)}%
        </span>
      </button>
    `;
  }).join('');
}

// Render Persona Selector Buttons
function renderPersonaPills() {
  const container = document.getElementById("personaPills");
  if (!container) return;

  container.innerHTML = Object.keys(state.personas).map(key => {
    const p = state.personas[key];
    const isActive = key === state.currentPersona;
    return `
      <button onclick="switchPersona('${key}')" class="px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 text-left ${
        isActive 
          ? 'bg-indigo-600/30 text-indigo-200 border border-indigo-500 shadow-md shadow-indigo-500/20' 
          : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:bg-slate-800/80 hover:text-slate-200'
      }">
        <div class="font-bold flex items-center justify-between">
          <span>${p.name.split('(')[0].trim()}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">${p.risk_category}</span>
        </div>
        <div class="text-[10px] text-slate-500 mt-0.5">${p.investment_horizon}</div>
      </button>
    `;
  }).join('');
}

// Switch Active Stock
async function switchStock(symbol) {
  if (state.currentSymbol === symbol) return;
  state.currentSymbol = symbol;
  renderStockPills();
  await triggerSynthesis();
  await loadChartData();
}

// Switch Active Persona
async function switchPersona(personaKey) {
  if (state.currentPersona === personaKey) return;
  state.currentPersona = personaKey;
  renderPersonaPills();
  await triggerSynthesis();
}

// Trigger Multi-Agent Synthesis via FastAPI Backend
async function triggerSynthesis() {
  const spinner = document.getElementById("loadingIndicator");
  if (spinner) spinner.classList.remove("hidden");

  try {
    const response = await fetch(`${API_BASE}/api/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: state.currentSymbol,
        persona: state.currentPersona,
        simulate_feed_failure: state.simulationFlags.simulate_feed_failure,
        simulate_missing_filing: state.simulationFlags.simulate_missing_filing,
        simulate_signal_conflict: state.simulationFlags.simulate_signal_conflict
      })
    });

    const data = await response.json();
    renderSynthesisOutput(data);
  } catch (err) {
    console.error("Synthesis failed:", err);
  } finally {
    if (spinner) spinner.classList.add("hidden");
  }
}

// Render Synthesis Results on Dashboard
function renderSynthesisOutput(data) {
  const stock = state.stocks[state.currentSymbol] || {};

  // Header Stock Info
  document.getElementById("activeStockName").textContent = stock.name || state.currentSymbol;
  document.getElementById("activeStockSymbol").textContent = `NSE: ${state.currentSymbol}`;
  document.getElementById("activeStockSector").textContent = stock.sector || "Equities";
  document.getElementById("activeStockPrice").textContent = `₹${(stock.cmp || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
  
  const chgEl = document.getElementById("activeStockChange");
  const isUp = (stock.change_pct || 0) >= 0;
  chgEl.textContent = `${isUp ? '+' : ''}${(stock.change_pct || 0).toFixed(2)}%`;
  chgEl.className = `mono text-sm font-bold ${isUp ? 'text-emerald-400' : 'text-rose-400'}`;

  // Telemetry Badges
  document.getElementById("telemetryLatency").textContent = `${data.metrics.pipeline_latency_ms.toFixed(1)} ms`;
  document.getElementById("telemetryGrounding").textContent = `${data.metrics.rag_grounding_score.toFixed(0)}%`;
  document.getElementById("telemetryVaR").textContent = `${data.metrics.portfolio_var_95_pct.toFixed(2)}%`;
  document.getElementById("telemetryHHI").textContent = `${data.metrics.portfolio_concentration_score.toFixed(1)}`;

  // Stance Hero Badge
  const actionBadge = document.getElementById("heroActionBadge");
  const actionText = data.action.replace(/_/g, ' ');
  actionBadge.textContent = `ACTION: ${actionText}`;

  if (data.action.includes("BUY") || data.action.includes("ACCUMULATE") || data.action.includes("ALPHA")) {
    actionBadge.className = "inline-flex items-center px-4 py-1.5 rounded-xl font-extrabold text-sm tracking-wide badge-strong-buy";
  } else if (data.action.includes("SELL") || data.action.includes("AVOID") || data.action.includes("SHORT")) {
    actionBadge.className = "inline-flex items-center px-4 py-1.5 rounded-xl font-extrabold text-sm tracking-wide badge-strong-sell";
  } else {
    actionBadge.className = "inline-flex items-center px-4 py-1.5 rounded-xl font-extrabold text-sm tracking-wide badge-neutral";
  }

  // Confidence meter
  document.getElementById("heroConfidenceText").textContent = `${data.confidence_pct}%`;
  document.getElementById("heroConfidenceBar").style.width = `${Math.min(100, data.confidence_pct)}%`;
  document.getElementById("heroRiskScore").textContent = `${data.risk_score}/10 Risk`;

  // Summaries
  document.getElementById("executiveSummaryText").textContent = data.executive_summary;
  document.getElementById("personalizedRationaleText").textContent = data.personalized_rationale;

  // Execution Plan
  document.getElementById("planEntryRange").textContent = data.target_entry_range;
  document.getElementById("planStopLoss").textContent = data.suggested_stop_loss;

  // Behavioral Alerts & Guardrails
  const alertsContainer = document.getElementById("behavioralAlertsContainer");
  if (alertsContainer) {
    if (data.behavioral_alerts && data.behavioral_alerts.length > 0) {
      alertsContainer.innerHTML = data.behavioral_alerts.map(a => `
        <div class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
          <span>⚠️</span><span>${a}</span>
        </div>
      `).join('');
      alertsContainer.classList.remove("hidden");
    } else {
      alertsContainer.classList.add("hidden");
    }
  }

  const guardrailsContainer = document.getElementById("guardrailsList");
  if (guardrailsContainer) {
    guardrailsContainer.innerHTML = data.guardrails.map(g => `
      <li class="text-xs text-slate-300 flex items-start gap-2">
        <span class="text-indigo-400 mt-0.5">•</span>
        <span>${g}</span>
      </li>
    `).join('');
  }

  // Degraded / Conflict Alerts
  const faultBanner = document.getElementById("faultAlertBanner");
  if (faultBanner) {
    if (data.degraded_mode_active || data.conflict_detected) {
      let msg = "";
      if (data.degraded_mode_active) msg += `⚠️ <b>DEGRADED STATE:</b> ${data.degraded_mode_details} `;
      if (data.conflict_detected) msg += `⚡ <b>CROSS-AGENT CONFLICT:</b> ${data.conflict_explanation}`;
      faultBanner.innerHTML = msg;
      faultBanner.classList.remove("hidden");
    } else {
      faultBanner.classList.add("hidden");
    }
  }

  // Waterfall Reasoning Trace
  const waterfallEl = document.getElementById("reasoningWaterfall");
  if (waterfallEl) {
    waterfallEl.innerHTML = data.reasoning_trace_waterfall.map(step => `
      <div class="waterfall-card pb-4">
        <div class="waterfall-node"></div>
        <div class="font-bold text-xs text-indigo-300">${step.stage}</div>
        <div class="text-xs text-slate-400 mt-1">${step.detail}</div>
      </div>
    `).join('');
  }

  // 3-Agent Parallel Desks
  renderAgentCards(data.agents);
}

// Render Agent Desks
function renderAgentCards(agents) {
  if (!agents) return;

  // Technical
  const t = agents.technical;
  if (t) {
    document.getElementById("techAgentStance").textContent = t.stance;
    document.getElementById("techAgentScore").textContent = `Score: ${t.score > 0 ? '+' : ''}${t.score.toFixed(2)}`;
    document.getElementById("techAgentLatency").textContent = `${t.latency_ms.toFixed(1)}ms`;
    document.getElementById("techAgentFindings").innerHTML = t.key_findings.map(f => `<li class="text-xs text-slate-300 mb-1">• ${f}</li>`).join('');
  }

  // Fundamental
  const f = agents.fundamental;
  if (f) {
    document.getElementById("fundAgentStance").textContent = f.stance;
    document.getElementById("fundAgentScore").textContent = `Score: ${f.score > 0 ? '+' : ''}${f.score.toFixed(2)}`;
    document.getElementById("fundAgentLatency").textContent = `${f.latency_ms.toFixed(1)}ms`;
    document.getElementById("fundAgentFindings").innerHTML = f.key_findings.map(item => `<li class="text-xs text-slate-300 mb-1">• ${item}</li>`).join('');
  }

  // Sentiment
  const s = agents.sentiment;
  if (s) {
    document.getElementById("sentAgentStance").textContent = s.stance;
    document.getElementById("sentAgentScore").textContent = `Score: ${s.score > 0 ? '+' : ''}${s.score.toFixed(2)}`;
    document.getElementById("sentAgentLatency").textContent = `${s.latency_ms.toFixed(1)}ms`;
    document.getElementById("sentAgentFindings").innerHTML = s.key_findings.map(item => `<li class="text-xs text-slate-300 mb-1">• ${item}</li>`).join('');
  }
}

// Load and Render Candlestick & Volume Chart
async function loadChartData() {
  try {
    const res = await fetch(`${API_BASE}/api/candles/${state.currentSymbol}?periods=45`);
    const candleData = await res.json();
    renderChart(candleData);
  } catch (err) {
    console.error("Failed to load chart data:", err);
  }
}

function renderChart(candleData) {
  const ctx = document.getElementById("marketChart");
  if (!ctx) return;

  if (state.chart) {
    state.chart.destroy();
  }

  state.chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: candleData.dates,
      datasets: [
        {
          label: "Close Price (₹)",
          data: candleData.closes,
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.08)",
          fill: true,
          tension: 0.2,
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 5
        },
        {
          label: "EMA 20",
          data: candleData.ema20,
          borderColor: "#818cf8",
          borderWidth: 1.5,
          borderDash: [4, 4],
          pointRadius: 0,
          fill: false
        },
        {
          label: "EMA 50",
          data: candleData.ema50,
          borderColor: "#f59e0b",
          borderWidth: 1.5,
          borderDash: [2, 2],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: '#94a3b8',
            font: { size: 11, family: "'Plus Jakarta Sans'" }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleColor: '#38bdf8',
          bodyColor: '#f8fafc',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 10
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#64748b', font: { size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { 
            color: '#64748b', 
            font: { size: 10 },
            callback: (val) => `₹${val.toLocaleString('en-IN')}`
          }
        }
      }
    }
  });
}

// Multi-Dimensional Signal Screener Table
async function renderScreenerTable() {
  const tbody = document.getElementById("screenerTableBody");
  if (!tbody) return;

  const tickers = Object.keys(state.stocks);
  const rowsHtml = await Promise.all(tickers.map(async sym => {
    try {
      const res = await fetch(`${API_BASE}/api/signals/${sym}`);
      const sig = await res.json();
      const isBuy = sig.overall_signal.includes("BUY");
      const isSell = sig.overall_signal.includes("SELL") || sig.overall_signal.includes("AVOID");
      const badgeClass = isBuy ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" : (isSell ? "text-rose-400 bg-rose-500/10 border-rose-500/30" : "text-amber-400 bg-amber-500/10 border-amber-500/30");

      return `
        <tr class="hover:bg-slate-800/40 transition-colors border-b border-slate-800/60 cursor-pointer" onclick="switchStock('${sym}')">
          <td class="py-3 px-4 font-bold text-slate-200">${sym}</td>
          <td class="py-3 px-4 mono text-slate-300">₹${sig.cmp.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
          <td class="py-3 px-4 mono font-semibold ${sig.change_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
            ${sig.change_pct >= 0 ? '+' : ''}${sig.change_pct.toFixed(2)}%
          </td>
          <td class="py-3 px-4 mono text-slate-400">${sig.rsi_14.toFixed(1)}</td>
          <td class="py-3 px-4 mono text-slate-400">${sig.volume_spike_ratio.toFixed(2)}x</td>
          <td class="py-3 px-4 mono text-slate-400">${sig.options_pcr.toFixed(2)}</td>
          <td class="py-3 px-4">
            <span class="px-2.5 py-1 rounded-md text-[11px] font-bold border ${badgeClass}">
              ${sig.overall_signal.replace('_', ' ')}
            </span>
          </td>
          <td class="py-3 px-4 mono text-cyan-400 font-semibold">${(sig.confidence_score * 100).toFixed(0)}%</td>
        </tr>
      `;
    } catch {
      return '';
    }
  }));

  tbody.innerHTML = rowsHtml.join('');
}

// WebSocket Connection for Live Tick Streaming
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/live-ticks`;

  try {
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      state.wsConnected = true;
      const statusBadge = document.getElementById("wsStatusBadge");
      if (statusBadge) {
        statusBadge.innerHTML = `<span class="pulse-dot"></span><span class="text-xs text-emerald-400 font-semibold">NSE LIVE STREAM</span>`;
      }
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "TICKS_UPDATE") {
        handleLiveTicks(msg.data);
      }
    };

    ws.onclose = () => {
      state.wsConnected = false;
      // Reconnect after 3s
      setTimeout(initWebSocket, 3000);
    };
  } catch (e) {
    console.warn("WebSocket stream fallback to polling.");
  }
}

// Handle Real-Time Tick Update with Visual Flashes
function handleLiveTicks(ticks) {
  for (const [sym, tick] of Object.entries(ticks)) {
    const oldStock = state.stocks[sym];
    if (oldStock) {
      const priceDiff = tick.cmp - oldStock.cmp;
      oldStock.cmp = tick.cmp;
      oldStock.change_pct = tick.change_pct;

      // Update Ticker Item Flash
      const tickerEl = document.getElementById(`ticker-${sym}`);
      if (tickerEl && Math.abs(priceDiff) > 0.05) {
        tickerEl.classList.remove("flash-green", "flash-red");
        void tickerEl.offsetWidth; // Trigger reflow
        tickerEl.classList.add(priceDiff > 0 ? "flash-green" : "flash-red");
      }
    }
  }

  // Update active stock price if matching
  const activeTick = ticks[state.currentSymbol];
  if (activeTick) {
    document.getElementById("activeStockPrice").textContent = `₹${activeTick.cmp.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    const chgEl = document.getElementById("activeStockChange");
    const isUp = activeTick.change_pct >= 0;
    chgEl.textContent = `${isUp ? '+' : ''}${activeTick.change_pct.toFixed(2)}%`;
    chgEl.className = `mono text-sm font-bold ${isUp ? 'text-emerald-400' : 'text-rose-400'}`;
  }
}

// RAG Search Handler
async function performRAGSearch() {
  const queryInput = document.getElementById("ragSearchInput");
  const resultsContainer = document.getElementById("ragResultsContainer");
  if (!queryInput || !resultsContainer) return;

  const query = queryInput.value.trim();
  if (!query) return;

  resultsContainer.innerHTML = `<div class="text-xs text-slate-400 p-4 text-center">Searching SEBI regulatory repository...</div>`;

  try {
    const res = await fetch(`${API_BASE}/api/rag/search?symbol=${state.currentSymbol}&query=${encodeURIComponent(query)}`);
    const data = await res.json();

    if (data.results && data.results.length > 0) {
      resultsContainer.innerHTML = data.results.map(r => `
        <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 mb-2.5">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="font-bold text-indigo-400">${r.source_tag}</span>
            <span class="mono px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 font-semibold">${(r.relevance_score * 100).toFixed(1)}% Match</span>
          </div>
          <div class="text-[11px] text-slate-500 mb-1">${r.section} | ${r.filing_type} (${r.date})</div>
          <div class="text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/50">
            "${r.snippet}"
          </div>
        </div>
      `).join('');
    } else {
      resultsContainer.innerHTML = `<div class="text-xs text-slate-500 p-4 text-center">No matching SEBI filing chunks found.</div>`;
    }
  } catch (err) {
    resultsContainer.innerHTML = `<div class="text-xs text-rose-400 p-4 text-center">Failed to search regulatory corpus.</div>`;
  }
}

// Event Listeners for Simulation Toggles
function setupEventListeners() {
  const feedFailCheck = document.getElementById("simFeedFail");
  const missingRagCheck = document.getElementById("simMissingRAG");
  const conflictCheck = document.getElementById("simConflict");

  if (feedFailCheck) {
    feedFailCheck.addEventListener("change", (e) => {
      state.simulationFlags.simulate_feed_failure = e.target.checked;
      triggerSynthesis();
    });
  }

  if (missingRagCheck) {
    missingRagCheck.addEventListener("change", (e) => {
      state.simulationFlags.simulate_missing_filing = e.target.checked;
      triggerSynthesis();
    });
  }

  if (conflictCheck) {
    conflictCheck.addEventListener("change", (e) => {
      state.simulationFlags.simulate_signal_conflict = e.target.checked;
      triggerSynthesis();
    });
  }

  const ragBtn = document.getElementById("ragSearchBtn");
  if (ragBtn) ragBtn.addEventListener("click", performRAGSearch);

  const ragInput = document.getElementById("ragSearchInput");
  if (ragInput) {
    ragInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") performRAGSearch();
    });
  }
}

// Modal Toggle Functions
function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove("hidden");
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add("hidden");
}
