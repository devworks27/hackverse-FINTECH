"""
Sentiment & Market Microstructure Agent
Specialized in news sentiment polarity, FII/DII institutional net flows, and Options Chain PCR/Max Pain dynamics.
"""

import time
from typing import Dict, Any, List

try:
    from agents.base_agent import BaseFinancialAgent, AgentOutputContract
    from core.market_feed import MarketFeed
except ImportError:
    from .base_agent import BaseFinancialAgent, AgentOutputContract
    from ..core.market_feed import MarketFeed

class SentimentMicrostructureAgent(BaseFinancialAgent):
    def __init__(self, market_feed: MarketFeed):
        super().__init__(name="Sentiment & Microstructure Analyst")
        self.market_feed = market_feed

    def analyze(self, symbol: str, context: Dict[str, Any]) -> AgentOutputContract:
        start_time = time.time()
        conflict_mode = context.get("simulate_signal_conflict", False)

        stock = self.market_feed.get_stock_data(symbol)
        if not stock:
            elapsed = (time.time() - start_time) * 1000
            return AgentOutputContract(
                agent_name=self.name,
                symbol=symbol,
                stance="NEUTRAL",
                score=0.0,
                confidence=0.20,
                key_findings=["No sentiment or derivatives data found."],
                execution_time_ms=elapsed,
                is_degraded=True,
                degraded_reason="Symbol not in universe."
            )

        findings: List[str] = []
        citations: List[Dict[str, Any]] = []

        cmp = stock["cmp"]
        pcr = stock["options_pcr"]
        max_pain = stock["options_max_pain"]
        fii_net = stock["fii_net_flow_cr"]
        dii_net = stock["dii_net_flow_cr"]
        tot_inst = fii_net + dii_net
        news_score = stock["news_sentiment_score"]
        headlines = stock["news_headlines"]

        if conflict_mode:
            news_score = -0.85
            pcr = 0.55
            findings.append("🚨 [SIMULATED CONFLICT]: High-priority regulatory investigation breaking news headline injected.")
            findings.append(f"Derivatives PCR collapses to {pcr:.2f} as aggressive call writers overwhelm the option chain.")
            flow_score = -0.80
            pcr_score = -0.80
        else:
            if news_score >= 0.5:
                findings.append(f"Highly Positive Newsflow (Sentiment Index: {news_score:+.2f}). Catalysts driving retail optimism.")
            elif news_score <= -0.2:
                findings.append(f"Cautious/Negative Newsflow (Sentiment Index: {news_score:+.2f}). Near-term macro headwinds cited.")
            else:
                findings.append(f"Neutral Newsflow (Sentiment Index: {news_score:+.2f}). Routine business updates.")

            for h in headlines[:2]:
                findings.append(f"• Headline: \"{h}\"")

            pain_dist_pct = ((cmp - max_pain) / max_pain) * 100
            if pcr >= 1.20:
                findings.append(f"Bullish PCR of {pcr:.2f}: Significant Put writing support indicates a firm price floor near ₹{max_pain:,.0f}.")
                pcr_score = 0.7
            elif pcr <= 0.80:
                findings.append(f"Bearish PCR of {pcr:.2f}: Heavy Call writing overhead resistance; Max Pain at ₹{max_pain:,.0f} ({pain_dist_pct:+.1f}%).")
                pcr_score = -0.7
            else:
                findings.append(f"Balanced PCR of {pcr:.2f}: Option chain indicates neutral range-bound expiration.")
                pcr_score = 0.1

            if tot_inst > 250:
                findings.append(f"Institutional Buying Pressure: Combined FII + DII net inflow of +INR {tot_inst:.1f} Crores.")
                flow_score = 0.75
            elif tot_inst < -150:
                findings.append(f"Institutional Distribution: Combined FII + DII net outflow of -INR {abs(tot_inst):.1f} Crores.")
                flow_score = -0.75
            else:
                findings.append(f"Institutional Neutrality: Modest net flow of +INR {tot_inst:.1f} Crores.")
                flow_score = 0.1

        composite_score = (news_score * 0.35) + (pcr_score * 0.35) + (flow_score * 0.30)
        composite_score = max(-1.0, min(1.0, composite_score))

        if composite_score >= 0.35:
            stance = "BULLISH"
        elif composite_score >= 0.10:
            stance = "MODERATELY_BULLISH"
        elif composite_score <= -0.35:
            stance = "BEARISH"
        elif composite_score <= -0.10:
            stance = "MODERATELY_BEARISH"
        else:
            stance = "NEUTRAL"

        citations.append({
            "type": "DERIVATIVES_&_FLOW",
            "pcr": pcr,
            "max_pain": max_pain,
            "fii_net_cr": fii_net,
            "dii_net_cr": dii_net
        })

        elapsed = (time.time() - start_time) * 1000

        return AgentOutputContract(
            agent_name=self.name,
            symbol=symbol,
            stance=stance,
            score=round(composite_score, 3),
            confidence=0.82 if not conflict_mode else 0.90,
            key_findings=findings,
            citations=citations,
            raw_signals={
                "sentiment_index": news_score,
                "options_pcr": pcr,
                "max_pain": max_pain,
                "net_institutional_flow_cr": tot_inst
            },
            execution_time_ms=round(elapsed, 2),
            is_degraded=False
        )
