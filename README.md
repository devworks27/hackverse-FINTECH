# ⚡ FinIntel: Multi-Agent Autonomous Financial Intelligence Platform
**Full-Stack Cyber-Fintech Decision Engine for Retail Investors**

[![Hackverse 2026](https://img.shields.io/badge/Hackathon-Hackverse%202026-blue.svg)](https://vit.ac.in)
[![Track](https://img.shields.io/badge/Problem%20Statement-PS--01%20Financial%20Intelligence-emerald.svg)]()
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%2B%20WebSockets-009688.svg)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/Frontend-Glassmorphic%20SPA-6366f1.svg)]()
[![Status](https://img.shields.io/badge/Tests-100%25%20Passing-brightgreen.svg)]()

---

## 📁 Full-Stack Architecture in `C:\FinTech`

```
C:\FinTech/
│
├── frontend/                          # High-End Glassmorphic SPA Frontend
│   ├── index.html                     # Semantic responsive HTML5 structure
│   ├── styles.css                     # Dark cyber-fintech stylesheet & animations
│   └── app.js                         # Dynamic state, WebSockets, Chart.js, RAG Search
│
├── backend/                           # High-Performance Analytical Engine
│   ├── main.py                        # FastAPI REST + WebSocket Live Tick Streamer
│   ├── test_pipeline.py               # Automated verification test suite
│   │
│   ├── core/                          # Quantitative Core Modules
│   │   ├── market_feed.py             # 3D Signal Classifier & Candlestick Generator
│   │   ├── rag_engine.py              # Semantic chunking & SEBI citation grounding
│   │   ├── user_profile.py            # Personas & Behavioral bias detector
│   │   └── metrics_logger.py          # SLA Latency, HHI Concentration & VaR 95%
│   │
│   ├── agents/                        # Parallel Reasoning Agent Desks
│   │   ├── base_agent.py              # Strict typed output schemas
│   │   ├── technical_agent.py         # RSI, MACD, Volume Spikes, EMA Trend
│   │   ├── fundamental_agent.py       # P/E valuation & grounded SEBI disclosures
│   │   ├── sentiment_agent.py         # Options PCR, Max Pain & FII/DII Net Flows
│   │   └── synthesis_orchestrator.py   # Multi-agent weighted synthesis & conflict engine
│   │
│   └── data/                          # Ground Truth Document & Market Store
│       ├── market_universe.json       # Stock metadata, beta, options PCR, flows
│       └── sebi_filings/              # Real-world SEBI LODR corporate filings
│           ├── reliance_q3_disclosure.txt
│           ├── tatasteel_debt_update.txt
│           ├── hdfcbank_merger_filing.txt
│           ├── tcs_tcv_quarterly.txt
│           ├── infy_guidance_report.txt
│           └── zomato_profitability_filing.txt
│
├── run_system.bat                     # Double-click startup script (Launches server & opens browser)
├── requirements.txt                   # Backend dependencies
└── README.md                          # Documentation
```

---

## 🚀 Quick Launch

### 1. Run Automated Test Suite
```bash
python C:\FinTech\backend\test_pipeline.py
```

### 2. Start Full-Stack System
```bash
python -m uvicorn backend.main:app --app-dir C:\FinTech --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

*(Or simply double-click `C:\FinTech\run_system.bat` on Windows)*
