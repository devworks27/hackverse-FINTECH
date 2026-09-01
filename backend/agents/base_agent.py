"""
Base Agent Interface & Structured Output Contracts
Ensures strict typed communication across all specialized reasoning agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class AgentOutputContract:
    agent_name: str
    symbol: str
    stance: str  # BULLISH, MODERATELY_BULLISH, NEUTRAL, MODERATELY_BEARISH, BEARISH
    score: float # -1.0 to +1.0
    confidence: float # 0.0 to 1.0
    key_findings: List[str]
    citations: List[Dict[str, Any]] = field(default_factory=list)
    raw_signals: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    is_degraded: bool = False
    degraded_reason: Optional[str] = None

class BaseFinancialAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def analyze(self, symbol: str, context: Dict[str, Any]) -> AgentOutputContract:
        pass
