"""
User Behavioral Profiling & Risk Modeling Engine
Captures risk profiles, portfolio composition, behavioral biases, and personalizes agent synthesis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class Holding:
    symbol: str
    quantity: int
    avg_buy_price: float
    current_price: float

    @property
    def current_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def invested_value(self) -> float:
        return self.quantity * self.avg_buy_price

    @property
    def pnl_pct(self) -> float:
        if self.invested_value == 0:
            return 0.0
        return ((self.current_value - self.invested_value) / self.invested_value) * 100

@dataclass
class UserProfile:
    profile_id: str
    name: str
    risk_category: str  # CONSERVATIVE, MODERATE, AGGRESSIVE, FO_TRADER
    investment_horizon: str  # Long-term, Medium-term, Swing, Intraday/F&O
    max_drawdown_tolerance_pct: float
    cash_balance: float
    holdings: List[Holding] = field(default_factory=list)
    behavioral_traits: List[str] = field(default_factory=list)
    
    # Weightings for Multi-Agent Synthesis (Sums to 1.0)
    weight_technical: float = 0.33
    weight_fundamental: float = 0.34
    weight_sentiment: float = 0.33

    @property
    def portfolio_total_value(self) -> float:
        return self.cash_balance + sum(h.current_value for h in self.holdings)

    def get_stock_allocation_pct(self, symbol: str) -> float:
        tot = self.portfolio_total_value
        if tot == 0:
            return 0.0
        holding = next((h for h in self.holdings if h.symbol.upper() == symbol.upper()), None)
        if not holding:
            return 0.0
        return (holding.current_value / tot) * 100

    def detect_behavioral_flags(self, target_symbol: str, target_rsi: float, target_change_pct: float) -> List[str]:
        flags = []
        alloc_pct = self.get_stock_allocation_pct(target_symbol)
        
        if alloc_pct > 25.0:
            flags.append(f"⚠️ High Concentration Alert: {target_symbol} already constitutes {alloc_pct:.1f}% of your total portfolio.")

        if target_rsi > 72 and target_change_pct > 3.0:
            flags.append("🚨 FOMO Alert: Stock has rallied aggressively and RSI is overbought. Risk of buying at local peak.")

        holding = next((h for h in self.holdings if h.symbol.upper() == target_symbol.upper()), None)
        if holding and holding.pnl_pct < -15.0:
            flags.append(f"📉 Loss Aversion Warning: You are down {abs(holding.pnl_pct):.1f}% on {target_symbol}. Avoid uncontrolled averaging down without strict catalyst.")

        return flags

def get_preset_profiles() -> Dict[str, UserProfile]:
    return {
        "CONSERVATIVE": UserProfile(
            profile_id="user_cons_01",
            name="Ramesh (Conservative / Capital Preservation)",
            risk_category="CONSERVATIVE",
            investment_horizon="Long-term (5-10 Years)",
            max_drawdown_tolerance_pct=6.0,
            cash_balance=150000.0,
            holdings=[
                Holding(symbol="HDFCBANK", quantity=100, avg_buy_price=1650.0, current_price=1720.40),
                Holding(symbol="TCS", quantity=40, avg_buy_price=3950.0, current_price=4180.00),
            ],
            behavioral_traits=["High risk aversion", "Prefers dividend yields & low debt", "Avoids high-beta momentum"],
            weight_technical=0.15,
            weight_fundamental=0.65,
            weight_sentiment=0.20
        ),
        "MODERATE": UserProfile(
            profile_id="user_mod_02",
            name="Priya (Moderate / Balanced Growth)",
            risk_category="MODERATE",
            investment_horizon="Medium to Long-term (2-5 Years)",
            max_drawdown_tolerance_pct=15.0,
            cash_balance=85000.0,
            holdings=[
                Holding(symbol="RELIANCE", quantity=30, avg_buy_price=2820.0, current_price=2980.50),
                Holding(symbol="INFY", quantity=45, avg_buy_price=1780.0, current_price=1845.20),
            ],
            behavioral_traits=["Growth at reasonable price", "Systematic SIP allocator", "Tolerates sector cyclicality"],
            weight_technical=0.35,
            weight_fundamental=0.45,
            weight_sentiment=0.20
        ),
        "AGGRESSIVE": UserProfile(
            profile_id="user_agg_03",
            name="Arjun (Aggressive / Momentum Alpha)",
            risk_category="AGGRESSIVE",
            investment_horizon="Short to Medium-term (Weeks to Months)",
            max_drawdown_tolerance_pct=28.0,
            cash_balance=60000.0,
            holdings=[
                Holding(symbol="ZOMATO", quantity=350, avg_buy_price=230.0, current_price=262.50),
                Holding(symbol="TATASTEEL", quantity=400, avg_buy_price=158.0, current_price=148.60),
            ],
            behavioral_traits=["Breakout seeker", "High volatility appetite", "Susceptible to FOMO on high-volume spikes"],
            weight_technical=0.55,
            weight_fundamental=0.15,
            weight_sentiment=0.30
        ),
        "FO_TRADER": UserProfile(
            profile_id="user_fo_04",
            name="Vikram (F&O Derivatives & Options Trader)",
            risk_category="FO_TRADER",
            investment_horizon="Intraday & Swing Options",
            max_drawdown_tolerance_pct=35.0,
            cash_balance=200000.0,
            holdings=[],
            behavioral_traits=["Derivatives-focused", "PCR & Max Pain follower", "Needs tight Stop-Loss guardrails"],
            weight_technical=0.50,
            weight_fundamental=0.10,
            weight_sentiment=0.40
        )
    }
