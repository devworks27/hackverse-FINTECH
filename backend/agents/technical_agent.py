"""
Technical & Momentum Analysis Agent
Specialized in quantitative price action, trend strength, volatility bands, and volume anomaly detection.
"""

import time
from typing import Dict, Any, List

try:
    from agents.base_agent import BaseFinancialAgent, AgentOutputContract
    from core.market_feed import MarketFeed
except ImportError:
    from .base_agent import BaseFinancialAgent, AgentOutputContract
    from ..core.market_feed import MarketFeed

class TechnicalAnalystAgent(BaseFinancialAgent):
    def __init__(self, market_feed: MarketFeed):
        super().__init__(name="Technical & Momentum Analyst")
        self.market_feed = market_feed

    def analyze(self, symbol: str, context: Dict[str, Any]) -> AgentOutputContract:
        start_time = time.time()
        
        if context.get("simulate_feed_failure", False):
            elapsed = (time.time() - start_time) * 1000
            return AgentOutputContract(
                agent_name=self.name,
                symbol=symbol,
                stance="NEUTRAL",
                score=0.0,
                confidence=0.30,
                key_findings=[
                    "⚠️ DEGRADED STATE: Live market price feed offline.",
                    "Falling back to last known daily closing reference.",
                    "Confidence capped at 30% due to missing real-time tickstream."
                ],
                citations=[],
                raw_signals={},
                execution_time_ms=elapsed,
                is_degraded=True,
                degraded_reason="NSE real-time WebSocket tick stream timeout / unavailable."
            )

        try:
            signal = self.market_feed.evaluate_multi_dimensional_signals(symbol)
            stock = self.market_feed.get_stock_data(symbol)
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return AgentOutputContract(
                agent_name=self.name,
                symbol=symbol,
                stance="NEUTRAL",
                score=0.0,
                confidence=0.20,
                key_findings=[f"Failed to fetch market data: {str(e)}"],
                is_degraded=True,
                degraded_reason=str(e),
                execution_time_ms=elapsed
            )

        findings: List[str] = []
        cmp = stock["cmp"]
        ema_20 = stock["ema_20"]
        ema_50 = stock["ema_50"]
        
        if cmp > ema_20 and ema_20 > ema_50:
            trend_score = 0.85
            findings.append(f"Golden Trend Alignment: CMP (₹{cmp:,.2f}) > 20 EMA (₹{ema_20:,.2f}) > 50 EMA (₹{ema_50:,.2f}).")
        elif cmp < ema_20 and ema_20 < ema_50:
            trend_score = -0.85
            findings.append(f"Bearish Trend Breakdown: CMP (₹{cmp:,.2f}) < 20 EMA (₹{ema_20:,.2f}) < 50 EMA (₹{ema_50:,.2f}).")
        else:
            trend_score = 0.1
            findings.append(f"Consolidation Phase: Price hovering between 20 EMA (₹{ema_20:,.2f}) and 50 EMA (₹{ema_50:,.2f}).")

        rsi = stock["rsi_14"]
        if rsi > 70:
            findings.append(f"RSI-14 at {rsi:.1f} indicates overbought momentum (risk of pullback).")
            rsi_weight = -0.2 if trend_score > 0 else -0.5
        elif rsi < 35:
            findings.append(f"RSI-14 at {rsi:.1f} indicates deep oversold zone (potential mean reversion).")
            rsi_weight = 0.6
        else:
            findings.append(f"RSI-14 at {rsi:.1f} is well-balanced within the healthy momentum zone (40-65).")
            rsi_weight = 0.4 if trend_score > 0 else -0.2

        vol_spike = stock["volume_spike_ratio"]
        if vol_spike >= 1.4:
            findings.append(f"Institutional volume surge: Trading at {vol_spike:.2f}x the 20-day moving average volume.")
            vol_score = 0.8 if stock["change_pct"] > 0 else -0.8
        else:
            findings.append(f"Volume behavior is normal ({vol_spike:.2f}x 20-DMA).")
            vol_score = 0.0

        composite_score = (trend_score * 0.50) + (rsi_weight * 0.25) + (vol_score * 0.25)
        composite_score = max(-1.0, min(1.0, composite_score))

        if composite_score >= 0.45:
            stance = "BULLISH"
        elif composite_score >= 0.15:
            stance = "MODERATELY_BULLISH"
        elif composite_score <= -0.45:
            stance = "BEARISH"
        elif composite_score <= -0.15:
            stance = "MODERATELY_BEARISH"
        else:
            stance = "NEUTRAL"

        confidence = signal.confidence_score
        elapsed = (time.time() - start_time) * 1000

        return AgentOutputContract(
            agent_name=self.name,
            symbol=symbol,
            stance=stance,
            score=round(composite_score, 3),
            confidence=round(confidence, 3),
            key_findings=findings,
            citations=[{
                "type": "TECHNICAL_INDICATOR",
                "indicators": {
                    "RSI_14": rsi,
                    "MACD_Hist": stock["macd_hist"],
                    "EMA_20": ema_20,
                    "EMA_50": ema_50,
                    "Volume_Spike": f"{vol_spike:.2f}x"
                }
            }],
            raw_signals={
                "rsi": rsi,
                "volume_spike": vol_spike,
                "trend_alignment": trend_score
            },
            execution_time_ms=round(elapsed, 2),
            is_degraded=False
        )
