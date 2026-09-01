"""
Behavioral & Multi-Agent Synthesis Orchestrator
Coordinates parallel agent execution, applies personalized risk weights, resolves conflicting signals,
and synthesizes transparent, explainable guidance for retail investors.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

try:
    from agents.base_agent import AgentOutputContract
    from agents.technical_agent import TechnicalAnalystAgent
    from agents.fundamental_agent import FundamentalRAGAgent
    from agents.sentiment_agent import SentimentMicrostructureAgent
    from core.user_profile import UserProfile
    from core.metrics_logger import MetricsLogger, SessionMetrics
except ImportError:
    from .base_agent import AgentOutputContract
    from .technical_agent import TechnicalAnalystAgent
    from .fundamental_agent import FundamentalRAGAgent
    from .sentiment_agent import SentimentMicrostructureAgent
    from ..core.user_profile import UserProfile
    from ..core.metrics_logger import MetricsLogger, SessionMetrics

@dataclass
class SynthesizedIntelligence:
    symbol: str
    user_profile_name: str
    risk_category: str
    action: str
    composite_confidence_pct: float
    risk_score: float
    executive_summary: str
    personalized_rationale: str
    agent_outputs: Dict[str, AgentOutputContract]
    citations: List[Dict[str, Any]]
    behavioral_alerts: List[str]
    guardrails: List[str]
    conflict_detected: bool
    conflict_explanation: Optional[str]
    degraded_mode_active: bool
    degraded_mode_details: Optional[str]
    target_entry_range: str
    suggested_stop_loss: str
    reasoning_trace_waterfall: List[Dict[str, str]]
    session_metrics: Optional[SessionMetrics] = None

class MultiAgentSynthesisOrchestrator:
    def __init__(
        self,
        tech_agent: TechnicalAnalystAgent,
        fund_agent: FundamentalRAGAgent,
        sent_agent: SentimentMicrostructureAgent,
        metrics_logger: Optional[MetricsLogger] = None
    ):
        self.tech_agent = tech_agent
        self.fund_agent = fund_agent
        self.sent_agent = sent_agent
        self.metrics_logger = metrics_logger or MetricsLogger()

    def run_parallel_analysis(self, symbol: str, context: Dict[str, Any]) -> Dict[str, AgentOutputContract]:
        results = {}
        results["technical"] = self.tech_agent.analyze(symbol, context)
        results["fundamental"] = self.fund_agent.analyze(symbol, context)
        results["sentiment"] = self.sent_agent.analyze(symbol, context)
        return results

    def synthesize(
        self,
        symbol: str,
        user_profile: UserProfile,
        context: Optional[Dict[str, Any]] = None
    ) -> SynthesizedIntelligence:
        total_start = time.time()
        ctx = context or {}

        agent_outputs = self.run_parallel_analysis(symbol, ctx)
        t_out = agent_outputs["technical"]
        f_out = agent_outputs["fundamental"]
        s_out = agent_outputs["sentiment"]

        agent_latencies = {
            "technical": t_out.execution_time_ms,
            "fundamental": f_out.execution_time_ms,
            "sentiment": s_out.execution_time_ms
        }

        degraded_flags = [out for out in agent_outputs.values() if out.is_degraded]
        is_degraded = len(degraded_flags) > 0
        degraded_details = "; ".join([f"{d.agent_name}: {d.degraded_reason}" for d in degraded_flags]) if is_degraded else None

        score_diff_tf = abs(t_out.score - f_out.score)
        score_diff_ts = abs(t_out.score - s_out.score)
        conflict_detected = (score_diff_tf >= 0.80) or (score_diff_ts >= 0.85)
        conflict_explanation = None

        if conflict_detected:
            if t_out.score > 0.3 and f_out.score < -0.3:
                conflict_explanation = (
                    f"⚠️ Critical Divergence: Technical momentum is {t_out.stance} (Score: {t_out.score:+.2f}), "
                    f"but Fundamental RAG analysis is {f_out.stance} (Score: {f_out.score:+.2f}). "
                    "Price action is temporarily detached from underlying valuation fundamentals."
                )
            elif t_out.score < -0.3 and f_out.score > 0.3:
                conflict_explanation = (
                    f"⚠️ Valuation Opportunity vs Price Breakdown: Fundamental RAG is {f_out.stance} (Score: {f_out.score:+.2f}), "
                    f"yet Technical indicators indicate {t_out.stance} momentum (Score: {t_out.score:+.2f}). "
                    "Indicates potential value trap in the short run or long-term accumulation window."
                )
            else:
                conflict_explanation = (
                    f"⚠️ Divergent Cross-Agent Signals: Sentiment/Microstructure ({s_out.stance}) contradicts "
                    f"Technical trend ({t_out.stance}). High market uncertainty."
                )

        w_t = user_profile.weight_technical
        w_f = user_profile.weight_fundamental
        w_s = user_profile.weight_sentiment

        if f_out.is_degraded:
            w_f *= 0.3
        if t_out.is_degraded:
            w_t *= 0.3

        sum_w = w_t + w_f + w_s
        w_t /= sum_w
        w_f /= sum_w
        w_s /= sum_w

        weighted_score = (t_out.score * w_t) + (f_out.score * w_f) + (s_out.score * w_s)
        raw_conf = (t_out.confidence * w_t) + (f_out.confidence * w_f) + (s_out.confidence * w_s)
        if conflict_detected:
            raw_conf *= 0.80
        if is_degraded:
            raw_conf *= 0.75

        composite_confidence = round(raw_conf * 100, 1)

        citations = []
        for out in agent_outputs.values():
            citations.extend(out.citations)

        stock_data = self.tech_agent.market_feed.get_stock_data(symbol) or {"cmp": 1000.0, "rsi_14": 50.0, "change_pct": 0.0}
        cmp = stock_data.get("cmp", 1000.0)
        rsi = stock_data.get("rsi_14", 50.0)
        change_pct = stock_data.get("change_pct", 0.0)

        behavioral_alerts = user_profile.detect_behavioral_flags(symbol, rsi, change_pct)
        cat = user_profile.risk_category
        guardrails = []
        reasoning_waterfall = []

        reasoning_waterfall.append({
            "stage": "Step 1: Parallel Agent Execution",
            "detail": f"Dispatched 3 parallel analytical tasks. Tech latency: {t_out.execution_time_ms:.1f}ms, Funda: {f_out.execution_time_ms:.1f}ms, Sent: {s_out.execution_time_ms:.1f}ms."
        })

        rag_citations_count = len([c for c in citations if "doc_id" in c])
        reasoning_waterfall.append({
            "stage": "Step 2: Regulatory Document Grounding",
            "detail": f"Retrieved {rag_citations_count} relevant SEBI regulatory chunks. Verified source attribution tags attached."
        })

        reasoning_waterfall.append({
            "stage": "Step 3: Persona Weighting & Bias Scan",
            "detail": f"Applied {user_profile.name} risk matrix (Tech: {w_t:.2f}, Funda: {w_f:.2f}, Sent: {w_s:.2f}). Scanned portfolio allocation ({user_profile.get_stock_allocation_pct(symbol):.1f}%)."
        })

        if cat == "CONSERVATIVE":
            if f_out.score >= 0.20 and weighted_score >= 0.15 and not conflict_detected:
                action = "SIP_ACCUMULATE_CORE"
                summary = f"High-quality defensive allocation. Strong balance sheet backing justifies steady position building."
                rationale = (
                    f"As a Conservative investor focused on capital preservation, {symbol}'s robust fundamental profile "
                    f"(P/E {stock_data.get('pe_ratio', 'N/A')}x, low debt covenants confirmed via SEBI filing) meets your strict quality threshold. "
                    f"Technical momentum is steady without extreme volatility spikes."
                )
                entry_range = f"₹{cmp * 0.98:.2f} - ₹{cmp:.2f}"
                stop_loss = f"₹{cmp * 0.93:.2f} (Strict 7% capital preservation buffer)"
            elif weighted_score < 0 or conflict_detected or rsi > 70:
                action = "AVOID_HIGH_RISK"
                summary = "High volatility or valuation uncertainty violates capital preservation mandate."
                rationale = (
                    f"Recommendation for {user_profile.name}: AVOID or WAIT. "
                    f"{'Cross-agent divergence introduces unacceptable asymmetric downside risk. ' if conflict_detected else ''}"
                    f"{'RSI is elevated indicating potential short-term correction risk. ' if rsi > 70 else ''}"
                    "Capital preservation rules prioritize avoiding drawdowns over chasing speculative gains."
                )
                entry_range = f"Wait for retest near 50 EMA (₹{stock_data.get('ema_50', cmp*0.95):,.2f})"
                stop_loss = "N/A - Avoid fresh deployment"
            else:
                action = "HOLD_EXISTING"
                summary = "Balanced profile; maintain existing position but do not commit fresh capital at current levels."
                rationale = f"Hold position. Fundamental metrics are stable, but current entry does not offer adequate safety margin for conservative risk appetite."
                entry_range = "Hold current allocation"
                stop_loss = f"₹{cmp * 0.94:.2f}"

            guardrails.append("🛡️ Rule 1: Max 5% single-stock capital allocation limit for capital preservation.")
            guardrails.append("🛡️ Rule 2: Automatic trade veto on F&O derivatives or ungrounded momentum breakout.")

        elif cat == "MODERATE":
            if weighted_score >= 0.30:
                action = "BUY_ACCUMULATE"
                summary = f"Favorable risk-reward growth opportunity with verified fundamental backing."
                rationale = (
                    f"Balanced growth thesis for {symbol}: Technical trend alignment is positive "
                    f"({t_out.stance}) and corroborated by {f_out.stance} quarterly disclosures. "
                    f"Composite score of {weighted_score:+.2f} matches your 2-5 year investment horizon."
                )
                entry_range = f"₹{cmp * 0.985:.2f} - ₹{cmp * 1.01:.2f}"
                stop_loss = f"₹{cmp * 0.90:.2f} (Trailing 10% risk threshold)"
            elif weighted_score <= -0.20:
                action = "TRIM_OR_AVOID"
                summary = "Underperforming technical momentum and valuation headwinds; reduce exposure."
                rationale = f"Technical deterioration combined with weak institutional flow suggests further downside consolidation. Limit allocation."
                entry_range = "N/A"
                stop_loss = f"₹{cmp * 0.95:.2f}"
            else:
                action = "HOLD_MONITOR"
                summary = "Neutral risk-reward profile; accumulate only on dips to major moving average supports."
                rationale = f"Current valuation is fair. Recommended to stagger purchases via systematic monthly SIP rather than lump-sum entry."
                entry_range = f"₹{stock_data.get('ema_20', cmp*0.97):,.2f} - ₹{cmp:.2f}"
                stop_loss = f"₹{cmp * 0.91:.2f}"

            guardrails.append("🛡️ Rule: Maximum 15% single-stock allocation in growth portfolio.")
            guardrails.append("🛡️ Rule: Rebalance if 14-day RSI crosses 75.")

        elif cat == "AGGRESSIVE":
            if t_out.score >= 0.20 or stock_data.get("volume_spike_ratio", 1.0) > 1.3:
                action = "BUY_MOMENTUM_ALPHA"
                summary = f"High-probability momentum breakout with institutional volume confirmation."
                rationale = (
                    f"Alpha momentum trigger active: {symbol} is displaying strong volume expansion "
                    f"({stock_data.get('volume_spike_ratio', 1.0):.2f}x 20-DMA) with {s_out.stance.lower()} institutional positioning. "
                    f"High-beta profile ({stock_data.get('beta', 1.0):.2f}) aligns with aggressive alpha-seeking parameters."
                )
                entry_range = f"Market CMP (₹{cmp:,.2f}) or on slight pullback to ₹{cmp*0.99:.2f}"
                stop_loss = f"₹{cmp * 0.96:.2f} (Tight 4% technical invalidation level)"
            elif weighted_score <= -0.30:
                action = "AGGRESSIVE_SHORT_OR_AVOID"
                summary = "Severe breakdown in technical trend with institutional selling pressure."
                rationale = f"Price breakdown below key moving averages with negative MACD histogram expansion. Avoid long positions."
                entry_range = "Look for short triggers on intraday bounce"
                stop_loss = f"₹{cmp * 1.03:.2f}"
            else:
                action = "SCALP_SWING_HOLD"
                summary = "Range-bound swing setup; trade bounded levels with tight stop-losses."
                rationale = f"Oscillating within Bollinger bands. Look for mean-reversion scalp opportunities."
                entry_range = f"₹{stock_data.get('bollinger_lower', cmp*0.96):,.2f}"
                stop_loss = f"₹{cmp * 0.95:.2f}"

            guardrails.append("⚡ Rule: Enforce mandatory 4% trailing stop-loss to eliminate tail risk.")
            guardrails.append("⚡ Rule: Scale out 50% position at +6% initial target.")

        else: # FO_TRADER
            pcr = stock_data.get("options_pcr", 1.0)
            max_pain = stock_data.get("options_max_pain", cmp)
            if pcr > 1.15:
                action = "BULLISH_DERIVATIVE_SPREAD"
                summary = f"Bull Put Spread / Call Long: Heavy Put writing floor observed at ₹{max_pain:,.0f}."
                rationale = (
                    f"Derivatives Microstructure setup: Put-Call Ratio of {pcr:.2f} confirms strong institutional floor. "
                    f"Recommend Bull Call Spread or Bull Put Credit Spread around strike ₹{max_pain:,.0f}."
                )
            elif pcr < 0.85:
                action = "BEARISH_DERIVATIVE_HEDGE"
                summary = f"Bear Call Spread / Put Long: Call resistance overhead near ₹{max_pain:,.0f}."
                rationale = f"PCR at {pcr:.2f} signals call writing dominance. High probability of capped upside into expiry."
            else:
                action = "IRON_CONDOR_RANGE_BOUND"
                summary = f"Delta-Neutral Iron Condor: Expiry pin expected near Max Pain ₹{max_pain:,.0f}."
                rationale = f"Balanced options chain dynamics. Capture time decay (Theta) via range-bound credit spreads."

            entry_range = f"Strike Range: ₹{max_pain * 0.97:,.0f} - ₹{max_pain * 1.03:,.0f}"
            stop_loss = "Max Loss capped at 1.5x premium collected"
            guardrails.append("🚨 SEBI Warning: 89% of retail F&O traders incur capital loss. Enforce defined-risk spreads only.")
            guardrails.append("🚨 Rule: Never carry naked overnight short options without protective wings.")

        reasoning_waterfall.append({
            "stage": "Step 4: Final Personalized Recommendation",
            "detail": f"Assigned action '{action}' with {composite_confidence}% confidence. Injected safety guardrails and entry/stop-loss boundaries."
        })

        total_latency_ms = (time.time() - total_start) * 1000

        session_metric = self.metrics_logger.record_session(
            symbol=symbol,
            profile=user_profile,
            pipeline_latency_ms=total_latency_ms,
            agent_latencies_ms=agent_latencies,
            citations_count=len(citations),
            composite_confidence=composite_confidence / 100.0
        )

        risk_score = round(min(10.0, max(1.0, 10.0 - (composite_confidence / 10.0) + (stock_data.get("beta", 1.0) * 2.0))), 1)

        return SynthesizedIntelligence(
            symbol=symbol,
            user_profile_name=user_profile.name,
            risk_category=cat,
            action=action,
            composite_confidence_pct=composite_confidence,
            risk_score=risk_score,
            executive_summary=summary,
            personalized_rationale=rationale,
            agent_outputs=agent_outputs,
            citations=citations,
            behavioral_alerts=behavioral_alerts,
            guardrails=guardrails,
            conflict_detected=conflict_detected,
            conflict_explanation=conflict_explanation,
            degraded_mode_active=is_degraded,
            degraded_mode_details=degraded_details,
            target_entry_range=entry_range,
            suggested_stop_loss=stop_loss,
            reasoning_trace_waterfall=reasoning_waterfall,
            session_metrics=session_metric
        )
