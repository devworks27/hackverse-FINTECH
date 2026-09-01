# FinIntel Backend Package
from .core.market_feed import MarketFeed, MarketSignal
from .core.rag_engine import RAGEngine, DocumentChunk, RAGQueryResult
from .core.user_profile import UserProfile, Holding, get_preset_profiles
from .core.metrics_logger import MetricsLogger, SessionMetrics

from .agents.base_agent import BaseFinancialAgent, AgentOutputContract
from .agents.technical_agent import TechnicalAnalystAgent
from .agents.fundamental_agent import FundamentalRAGAgent
from .agents.sentiment_agent import SentimentMicrostructureAgent
from .agents.synthesis_orchestrator import MultiAgentSynthesisOrchestrator, SynthesizedIntelligence

__all__ = [
    "MarketFeed",
    "MarketSignal",
    "RAGEngine",
    "DocumentChunk",
    "RAGQueryResult",
    "UserProfile",
    "Holding",
    "get_preset_profiles",
    "MetricsLogger",
    "SessionMetrics",
    "BaseFinancialAgent",
    "AgentOutputContract",
    "TechnicalAnalystAgent",
    "FundamentalRAGAgent",
    "SentimentMicrostructureAgent",
    "MultiAgentSynthesisOrchestrator",
    "SynthesizedIntelligence"
]
