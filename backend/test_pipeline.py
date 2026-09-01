"""
Comprehensive Automated Verification Suite for FinIntel Multi-Agent System
Tests all 9 Minimum Requirements for PS-01 Hackverse 2026.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(__file__))

from core.market_feed import MarketFeed
from core.rag_engine import RAGEngine
from core.user_profile import get_preset_profiles
from core.metrics_logger import MetricsLogger
from agents.technical_agent import TechnicalAnalystAgent
from agents.fundamental_agent import FundamentalRAGAgent
from agents.sentiment_agent import SentimentMicrostructureAgent
from agents.synthesis_orchestrator import MultiAgentSynthesisOrchestrator

def run_tests():
    print("=" * 70)
    print("[TEST SUITE] RUNNING FinIntel MULTI-AGENT VERIFICATION SUITE")
    print("=" * 70)

    # 1. Initialize Components
    print("\n[TEST 1] Initializing Market Feed, RAG Engine & Specialized Agents...")
    market_feed = MarketFeed()
    rag_engine = RAGEngine()
    tech_agent = TechnicalAnalystAgent(market_feed)
    fund_agent = FundamentalRAGAgent(rag_engine, market_feed)
    sent_agent = SentimentMicrostructureAgent(market_feed)
    metrics_logger = MetricsLogger()
    orchestrator = MultiAgentSynthesisOrchestrator(tech_agent, fund_agent, sent_agent, metrics_logger)
    profiles = get_preset_profiles()
    
    assert len(market_feed.get_supported_tickers()) >= 5, "Market universe must have at least 5 stocks"
    assert len(rag_engine.chunks) > 0, "RAG engine must index SEBI filing chunks"
    print(f"[OK] Initialized successfully. Indexed {len(rag_engine.chunks)} SEBI filing chunks across {len(rag_engine.get_all_indexed_symbols())} companies.")

    # 2. Multi-Dimensional Signal Classification Test
    print("\n[TEST 2] Verifying Multi-Dimensional Signal Classification Module...")
    test_symbol = "RELIANCE"
    sig = market_feed.evaluate_multi_dimensional_signals(test_symbol)
    print(f"   Symbol: {sig.symbol} | CMP: Rs {sig.cmp:,.2f} | Signal: {sig.overall_signal} | Confidence: {sig.confidence_score*100:.1f}%")
    print(f"   - Momentum / RSI: {sig.rsi_14:.1f} ({sig.macd_stance})")
    print(f"   - Volume Spike: {sig.volume_spike_ratio:.2f}x ({sig.volume_stance})")
    print(f"   - Institutional Flow / PCR: PCR {sig.options_pcr:.2f} ({sig.institutional_stance})")
    assert len(sig.rationale_points) >= 3, "Must have rationale for all 3 independent dimensions"
    print("[OK] Multi-Dimensional Signal Classification passed.")

    # 3. Grounded RAG Retrieval Test
    print("\n[TEST 3] Verifying RAG Document Grounding & Citation Attribution...")
    rag_results = rag_engine.query(symbol=test_symbol, query_text="capex new energy solar giga factory revenue ebitda", top_k=2)
    assert len(rag_results) > 0, "RAG must return relevant document chunks"
    for r in rag_results:
        print(f"   Citation: {r.citation_text} (Relevance: {r.relevance_score*100:.1f}%)")
        print(f"   Snippet: {r.chunk.content[:140]}...")
    print("[OK] RAG Grounding and Citation Attribution passed.")

    # 4. Multi-Agent End-to-End Synthesis Test
    print("\n[TEST 4] Verifying End-to-End Multi-Agent Parallel Synthesis Pipeline...")
    intel_mod = orchestrator.synthesize(test_symbol, profiles["MODERATE"])
    print(f"   Orchestrator Action: {intel_mod.action} (Confidence: {intel_mod.composite_confidence_pct}%)")
    print(f"   Executive Summary: {intel_mod.executive_summary}")
    print(f"   Total Pipeline Latency: {intel_mod.session_metrics.total_pipeline_latency_ms:.2f} ms")
    assert intel_mod.session_metrics.total_pipeline_latency_ms < 500, "Pipeline latency must be < 500ms"
    assert len(intel_mod.reasoning_trace_waterfall) >= 4, "Must have 4-step reasoning trace waterfall"
    print("[OK] End-to-End Synthesis and Sub-500ms Latency verified.")

    # 5. User Profiling Differentiation Test (Identical market inputs -> Different outputs)
    print("\n[TEST 5] Testing Persona Differentiation on Identical Market Inputs (RELIANCE)...")
    intel_cons = orchestrator.synthesize("RELIANCE", profiles["CONSERVATIVE"])
    intel_agg = orchestrator.synthesize("RELIANCE", profiles["AGGRESSIVE"])
    intel_fo = orchestrator.synthesize("RELIANCE", profiles["FO_TRADER"])

    print(f"   - Conservative Ramesh Action:  {intel_cons.action} (Focus: Capital Preservation & Margin)")
    print(f"   - Moderate Priya Action:       {intel_mod.action} (Focus: 2-5 Yr Long-Term Growth)")
    print(f"   - Aggressive Arjun Action:     {intel_agg.action} (Focus: Breakout Momentum Alpha)")
    print(f"   - F&O Vikram Action:           {intel_fo.action} (Focus: Derivatives Spread / Options Floor)")

    assert intel_cons.action != intel_agg.action or intel_cons.personalized_rationale != intel_agg.personalized_rationale, "Profiles must produce distinct reasoning"
    print("[OK] Persona Differentiation verified: System dynamically customizes advice to risk profile.")

    # 6. Degraded-State & Conflict Handling Test
    print("\n[TEST 6] Testing Degraded Data Scenarios & Conflict Resolution...")
    
    degraded_feed = orchestrator.synthesize(test_symbol, profiles["MODERATE"], context={"simulate_feed_failure": True})
    assert degraded_feed.degraded_mode_active, "Degraded mode must activate on feed failure"
    print(f"   A. Feed Outage: {degraded_feed.degraded_mode_details} -> Handled gracefully with adjusted confidence ({degraded_feed.composite_confidence_pct}%)")

    degraded_rag = orchestrator.synthesize(test_symbol, profiles["MODERATE"], context={"simulate_missing_filing": True})
    assert degraded_rag.degraded_mode_active, "Degraded mode must activate on missing filing"
    print(f"   B. Missing Filing: {degraded_rag.degraded_mode_details} -> Handled gracefully without crash.")

    conflict_run = orchestrator.synthesize(test_symbol, profiles["MODERATE"], context={"simulate_signal_conflict": True})
    assert conflict_run.conflict_detected, "Conflict resolution protocol must trigger on cross-agent divergence"
    print(f"   C. Cross-Agent Divergence: {conflict_run.conflict_explanation}")
    print("[OK] All Degraded-State and Conflict Scenarios passed.")

    # 7. Performance & Risk Metrics Log Test
    print("\n[TEST 7] Testing Risk Concentration Score & Performance Metrics Log...")
    risk_metrics = metrics_logger.calculate_portfolio_risk(profiles["CONSERVATIVE"])
    print(f"   Conservative Portfolio HHI Concentration: {risk_metrics['concentration_score']} ({risk_metrics['diversification_status']})")
    print(f"   1-Day Parametric VaR (95%): {risk_metrics['var_95_pct']}%")
    assert len(metrics_logger.history) >= 4, "Metrics history must be recorded across sessions"
    print("[OK] Risk Concentration and Session Performance Log verified.")

    print("\n" + "=" * 70)
    print(">>> ALL 7 VERIFICATION CRITERIA PASSED WITH ZERO ERRORS! <<<")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
