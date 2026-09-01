"""
FinIntel Full-Stack FastAPI Backend Server
Serves REST APIs, WebSocket real-time NSE market tick streamer, and mounts the modern frontend UI.
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.market_feed import MarketFeed
from core.rag_engine import RAGEngine
from core.user_profile import get_preset_profiles, UserProfile
from core.metrics_logger import MetricsLogger
from agents.technical_agent import TechnicalAnalystAgent
from agents.fundamental_agent import FundamentalRAGAgent
from agents.sentiment_agent import SentimentMicrostructureAgent
from agents.synthesis_orchestrator import MultiAgentSynthesisOrchestrator

app = FastAPI(
    title="FinIntel Autonomous Multi-Agent API",
    version="1.0.0",
    description="FastAPI Backend for PS-01 Multi-Agent Financial Intelligence System"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Instances
market_feed = MarketFeed()
rag_engine = RAGEngine()
tech_agent = TechnicalAnalystAgent(market_feed)
fund_agent = FundamentalRAGAgent(rag_engine, market_feed)
sent_agent = SentimentMicrostructureAgent(market_feed)
metrics_logger = MetricsLogger()
orchestrator = MultiAgentSynthesisOrchestrator(tech_agent, fund_agent, sent_agent, metrics_logger)
preset_profiles = get_preset_profiles()

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

class SynthesizeRequest(BaseModel):
    symbol: str = Field(..., example="RELIANCE")
    persona: str = Field("MODERATE", example="CONSERVATIVE")
    simulate_feed_failure: bool = False
    simulate_missing_filing: bool = False
    simulate_signal_conflict: bool = False

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "system": "FinIntel Multi-Agent Financial Intelligence Platform",
        "supported_tickers": market_feed.get_supported_tickers(),
        "indexed_sebi_chunks": len(rag_engine.chunks)
    }

@app.get("/api/stocks")
def get_all_stocks():
    stocks = {}
    for ticker in market_feed.get_supported_tickers():
        stocks[ticker] = market_feed.get_stock_data(ticker)
    return {"stocks": stocks}

@app.get("/api/candles/{symbol}")
def get_stock_candles(symbol: str, periods: int = 45):
    try:
        df = market_feed.generate_historical_candles(symbol=symbol.upper(), periods=periods)
        return {
            "symbol": symbol.upper(),
            "dates": df["Date"].tolist(),
            "opens": df["Open"].tolist(),
            "highs": df["High"].tolist(),
            "lows": df["Low"].tolist(),
            "closes": df["Close"].tolist(),
            "volumes": df["Volume"].tolist(),
            "ema20": df["EMA20"].tolist(),
            "ema50": df["EMA50"].tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/signals/{symbol}")
def get_signal_classification(symbol: str):
    try:
        sig = market_feed.evaluate_multi_dimensional_signals(symbol.upper())
        return {
            "symbol": sig.symbol,
            "cmp": sig.cmp,
            "change_pct": sig.change_pct,
            "rsi_14": sig.rsi_14,
            "macd_stance": sig.macd_stance,
            "volume_spike_ratio": sig.volume_spike_ratio,
            "options_pcr": sig.options_pcr,
            "overall_signal": sig.overall_signal,
            "confidence_score": sig.confidence_score,
            "rationale": sig.rationale_points
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/personas")
def get_personas():
    profiles_data = {}
    for k, p in preset_profiles.items():
        risk_m = metrics_logger.calculate_portfolio_risk(p)
        profiles_data[k] = {
            "id": p.profile_id,
            "name": p.name,
            "risk_category": p.risk_category,
            "investment_horizon": p.investment_horizon,
            "max_drawdown_tolerance_pct": p.max_drawdown_tolerance_pct,
            "cash_balance": p.cash_balance,
            "portfolio_value": p.portfolio_total_value,
            "concentration_hhi": risk_m["concentration_score"],
            "var_95_pct": risk_m["var_95_pct"],
            "diversification_status": risk_m["diversification_status"],
            "weights": {
                "technical": p.weight_technical,
                "fundamental": p.weight_fundamental,
                "sentiment": p.weight_sentiment
            },
            "holdings": [
                {
                    "symbol": h.symbol,
                    "quantity": h.quantity,
                    "avg_buy_price": h.avg_buy_price,
                    "current_price": h.current_price,
                    "current_value": h.current_value,
                    "pnl_pct": round(h.pnl_pct, 2)
                }
                for h in p.holdings
            ]
        }
    return {"personas": profiles_data}

@app.get("/api/rag/search")
def search_rag(symbol: str, query: str = Query(..., min_length=2)):
    results = rag_engine.query(symbol=symbol.upper(), query_text=query, top_k=4)
    return {
        "symbol": symbol.upper(),
        "query": query,
        "results": [
            {
                "citation": r.citation_text,
                "source_tag": r.chunk.source_tag,
                "relevance_score": r.relevance_score,
                "section": r.chunk.section_title,
                "filing_type": r.chunk.filing_type,
                "date": r.chunk.date,
                "snippet": r.chunk.content
            }
            for r in results
        ]
    }

@app.post("/api/synthesize")
def synthesize_decision(req: SynthesizeRequest):
    sym = req.symbol.upper()
    if sym not in market_feed.get_supported_tickers():
        raise HTTPException(status_code=404, detail=f"Stock {sym} not found in market universe.")

    profile = preset_profiles.get(req.persona.upper(), preset_profiles["MODERATE"])
    context = {
        "simulate_feed_failure": req.simulate_feed_failure,
        "simulate_missing_filing": req.simulate_missing_filing,
        "simulate_signal_conflict": req.simulate_signal_conflict
    }

    intel = orchestrator.synthesize(symbol=sym, user_profile=profile, context=context)

    # Format agent breakdowns
    agents_summary = {}
    for agent_key, out in intel.agent_outputs.items():
        agents_summary[agent_key] = {
            "name": out.agent_name,
            "stance": out.stance,
            "score": out.score,
            "confidence": out.confidence,
            "latency_ms": out.execution_time_ms,
            "key_findings": out.key_findings,
            "citations": out.citations,
            "is_degraded": out.is_degraded,
            "degraded_reason": out.degraded_reason
        }

    return {
        "symbol": intel.symbol,
        "user_profile": intel.user_profile_name,
        "risk_category": intel.risk_category,
        "action": intel.action,
        "confidence_pct": intel.composite_confidence_pct,
        "risk_score": intel.risk_score,
        "executive_summary": intel.executive_summary,
        "personalized_rationale": intel.personalized_rationale,
        "target_entry_range": intel.target_entry_range,
        "suggested_stop_loss": intel.suggested_stop_loss,
        "guardrails": intel.guardrails,
        "behavioral_alerts": intel.behavioral_alerts,
        "conflict_detected": intel.conflict_detected,
        "conflict_explanation": intel.conflict_explanation,
        "degraded_mode_active": intel.degraded_mode_active,
        "degraded_mode_details": intel.degraded_mode_details,
        "reasoning_trace_waterfall": intel.reasoning_trace_waterfall,
        "agents": agents_summary,
        "metrics": {
            "pipeline_latency_ms": intel.session_metrics.total_pipeline_latency_ms,
            "portfolio_concentration_score": intel.session_metrics.portfolio_concentration_score,
            "portfolio_var_95_pct": intel.session_metrics.portfolio_var_95_pct,
            "rag_grounding_score": intel.session_metrics.rag_citation_grounding_score,
            "simulated_30d_return_est": intel.session_metrics.simulated_30d_forward_return_est,
            "backtest_win_rate_pct": intel.session_metrics.backtest_win_rate_pct
        }
    }

@app.websocket("/ws/live-ticks")
async def websocket_ticks_endpoint(websocket: WebSocket):
    await websocket.accept()
    tickers = market_feed.get_supported_tickers()
    try:
        while True:
            # Broadcast ticks for all stocks
            ticks = {}
            for t in tickers:
                ticks[t] = market_feed.get_live_tick_update(t)
            await websocket.send_json({"type": "TICKS_UPDATE", "data": ticks})
            await asyncio.sleep(1.2)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# Mount static frontend assets
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(str(frontend_dir / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
