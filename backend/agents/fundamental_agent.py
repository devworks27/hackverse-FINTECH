"""
Fundamental & Regulatory RAG Agent
Specialized in balance sheet safety, valuation multiples (P/E, P/B), and grounded SEBI disclosure retrieval.
"""

import time
from typing import Dict, Any, List

try:
    from agents.base_agent import BaseFinancialAgent, AgentOutputContract
    from core.rag_engine import RAGEngine
    from core.market_feed import MarketFeed
except ImportError:
    from .base_agent import BaseFinancialAgent, AgentOutputContract
    from ..core.rag_engine import RAGEngine
    from ..core.market_feed import MarketFeed

class FundamentalRAGAgent(BaseFinancialAgent):
    def __init__(self, rag_engine: RAGEngine, market_feed: MarketFeed):
        super().__init__(name="Fundamental & Regulatory RAG Analyst")
        self.rag_engine = rag_engine
        self.market_feed = market_feed

    def analyze(self, symbol: str, context: Dict[str, Any]) -> AgentOutputContract:
        start_time = time.time()
        
        if context.get("simulate_missing_filing", False):
            elapsed = (time.time() - start_time) * 1000
            return AgentOutputContract(
                agent_name=self.name,
                symbol=symbol,
                stance="NEUTRAL",
                score=0.0,
                confidence=0.35,
                key_findings=[
                    "⚠️ DEGRADED STATE: SEBI filing / regulatory document corpus unreachable.",
                    "Unable to ground debt covenants or capex disclosures in authoritative filings.",
                    "Confidence penalized by 45%; retail user should exercise caution."
                ],
                citations=[],
                raw_signals={},
                execution_time_ms=elapsed,
                is_degraded=True,
                degraded_reason="Regulatory document retrieval service returned empty/unreachable corpus."
            )

        stock = self.market_feed.get_stock_data(symbol)
        if not stock:
            elapsed = (time.time() - start_time) * 1000
            return AgentOutputContract(
                agent_name=self.name,
                symbol=symbol,
                stance="NEUTRAL",
                score=0.0,
                confidence=0.20,
                key_findings=["No fundamental profile found."],
                execution_time_ms=elapsed,
                is_degraded=True,
                degraded_reason="Stock symbol not recognized in universe."
            )

        query_text = f"{symbol} quarterly revenue ebitda margin debt capex dividend growth"
        rag_results = self.rag_engine.query(symbol=symbol, query_text=query_text, top_k=3)

        findings: List[str] = []
        citations: List[Dict[str, Any]] = []

        pe = stock["pe_ratio"]
        sector_pe = stock["sector_pe"]
        div_yield = stock["dividend_yield"]
        
        pe_discount_pct = ((sector_pe - pe) / sector_pe) * 100
        if pe_discount_pct > 10:
            val_score = 0.7
            findings.append(f"Attractive Valuation: Trading at P/E of {pe:.1f}x vs Sector P/E of {sector_pe:.1f}x ({pe_discount_pct:.1f}% discount).")
        elif pe_discount_pct < -25:
            val_score = -0.6
            findings.append(f"Premium Valuation: Trading at P/E of {pe:.1f}x vs Sector P/E of {sector_pe:.1f}x (growth already heavily priced in).")
        else:
            val_score = 0.2
            findings.append(f"Fairly Valued: Trading in-line at P/E of {pe:.1f}x vs Sector P/E of {sector_pe:.1f}x.")

        if div_yield >= 2.0:
            findings.append(f"Strong Capital Return: Healthy dividend yield of {div_yield:.2f}% provides downside cushion.")
            div_score = 0.5
        else:
            div_score = 0.0

        rag_grounding_score = 0.0
        if rag_results:
            for res in rag_results:
                chunk = res.chunk
                citations.append({
                    "doc_id": chunk.doc_id,
                    "source_tag": chunk.source_tag,
                    "section": chunk.section_title,
                    "relevance_score": res.relevance_score,
                    "snippet": chunk.content[:220] + "..." if len(chunk.content) > 220 else chunk.content
                })
                first_sentence = chunk.content.split(".")[0].strip()
                findings.append(f"{first_sentence}. {chunk.source_tag}")

            rag_grounding_score = 0.6
        else:
            findings.append("⚠️ No direct SEBI regulatory filing found in local repository. Relying purely on valuation metrics.")

        composite_score = (val_score * 0.50) + (div_score * 0.20) + (rag_grounding_score * 0.30)
        composite_score = max(-1.0, min(1.0, composite_score))

        if composite_score >= 0.40:
            stance = "BULLISH"
        elif composite_score >= 0.10:
            stance = "MODERATELY_BULLISH"
        elif composite_score <= -0.40:
            stance = "BEARISH"
        elif composite_score <= -0.10:
            stance = "MODERATELY_BEARISH"
        else:
            stance = "NEUTRAL"

        confidence = 0.88 if len(citations) >= 2 else 0.65
        elapsed = (time.time() - start_time) * 1000

        return AgentOutputContract(
            agent_name=self.name,
            symbol=symbol,
            stance=stance,
            score=round(composite_score, 3),
            confidence=round(confidence, 3),
            key_findings=findings,
            citations=citations,
            raw_signals={
                "pe_ratio": pe,
                "sector_pe": sector_pe,
                "dividend_yield": div_yield,
                "rag_chunks_found": len(rag_results)
            },
            execution_time_ms=round(elapsed, 2),
            is_degraded=False
        )
