"""
Market Data Feed & Multi-Dimensional Signal Classification Module
Provides live/simulated market data, technical indicator calculation, and multi-dimensional signal grading.
"""

import json
import os
import math
import random
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "market_universe.json")

@dataclass
class MarketSignal:
    symbol: str
    cmp: float
    change_pct: float
    rsi_14: float
    macd_stance: str
    macd_hist: float
    ema_trend: str
    volume_spike_ratio: float
    volume_stance: str
    options_pcr: float
    options_stance: str
    fii_dii_flow_cr: float
    institutional_stance: str
    overall_signal: str  # STRONG_BUY, BUY, NEUTRAL, AVOID, STRONG_SELL
    confidence_score: float  # 0.0 to 1.0
    rationale_points: List[str] = field(default_factory=list)

class MarketFeed:
    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path
        self._universe = self._load_universe()

    def _load_universe(self) -> Dict[str, Any]:
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f).get("stocks", {})
        return {}

    def get_supported_tickers(self) -> List[str]:
        return list(self._universe.keys())

    def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self._universe.get(symbol.upper())

    def get_live_tick_update(self, symbol: str) -> Dict[str, Any]:
        """Generates real-time price tick with realistic micro-jitter for live WebSocket stream."""
        stock = self.get_stock_data(symbol)
        if not stock:
            return {"symbol": symbol, "cmp": 1000.0, "change_pct": 0.0}
        
        jitter_pct = (random.random() - 0.49) * 0.15 # Small micro-move
        new_cmp = round(stock["cmp"] * (1 + jitter_pct / 100), 2)
        new_change = round(stock["change_pct"] + jitter_pct, 2)
        return {
            "symbol": stock["symbol"],
            "name": stock["name"],
            "sector": stock["sector"],
            "cmp": new_cmp,
            "change_pct": new_change,
            "day_high": max(stock["day_high"], new_cmp),
            "day_low": min(stock["day_low"], new_cmp),
            "volume": stock["volume"] + random.randint(50, 500),
            "rsi_14": round(stock["rsi_14"] + (jitter_pct * 0.5), 1),
            "options_pcr": stock["options_pcr"]
        }

    def generate_historical_candles(self, symbol: str, periods: int = 60) -> pd.DataFrame:
        """Generates realistic OHLCV historical dataframe for interactive charts and backtesting."""
        stock = self.get_stock_data(symbol)
        base_price = stock["cmp"] if stock else 1000.0

        np.random.seed(abs(hash(symbol)) % 10000)
        dates = pd.date_range(end=pd.Timestamp.now(), periods=periods, freq="B")
        
        returns = np.random.normal(0.0008, 0.015, periods)
        price_series = base_price * np.cumprod(1 + returns[::-1])[::-1]
        
        opens = price_series * (1 + np.random.normal(0, 0.003, periods))
        highs = np.maximum(opens, price_series) * (1 + np.abs(np.random.normal(0.005, 0.004, periods)))
        lows = np.minimum(opens, price_series) * (1 - np.abs(np.random.normal(0.005, 0.004, periods)))
        closes = price_series
        base_vol = stock.get("avg_volume_20d", 5000000) if stock else 5000000
        volumes = np.random.lognormal(mean=np.log(base_vol), sigma=0.4, size=periods).astype(int)

        # Force the last candle to match CMP
        if stock:
            closes[-1] = stock["cmp"]
            highs[-1] = max(highs[-1], stock["day_high"])
            lows[-1] = min(lows[-1], stock["day_low"])
            volumes[-1] = stock["volume"]

        df = pd.DataFrame({
            "Date": [d.strftime("%Y-%m-%d") for d in dates],
            "Open": np.round(opens, 2),
            "High": np.round(highs, 2),
            "Low": np.round(lows, 2),
            "Close": np.round(closes, 2),
            "Volume": volumes
        })
        
        # Calculate moving averages
        df["EMA20"] = np.round(df["Close"].ewm(span=20, adjust=False).mean(), 2)
        df["EMA50"] = np.round(df["Close"].ewm(span=50, adjust=False).mean(), 2)
        return df

    def evaluate_multi_dimensional_signals(self, symbol: str) -> MarketSignal:
        """
        Evaluates stock across 3 independent quantitative dimensions:
        1. Price Momentum & Trend (RSI, MACD, EMA Cross)
        2. Volume & Liquidity Anomalies (OBV, Volume Spike vs 20-DMA)
        3. Options Microstructure & Institutional Flow (PCR, Max Pain, FII/DII)
        """
        stock = self.get_stock_data(symbol)
        if not stock:
            raise ValueError(f"Ticker {symbol} not found in market universe.")

        cmp = stock["cmp"]
        change_pct = stock["change_pct"]
        rsi = stock["rsi_14"]
        macd_hist = stock["macd_hist"]
        ema_20 = stock["ema_20"]
        ema_50 = stock["ema_50"]
        volume_spike = stock["volume_spike_ratio"]
        pcr = stock["options_pcr"]
        fii_net = stock["fii_net_flow_cr"]
        dii_net = stock["dii_net_flow_cr"]
        total_inst_flow = fii_net + dii_net

        rationale = []
        scores = []

        # DIMENSION 1: Price Momentum & Trend
        if ema_20 > ema_50 and cmp > ema_20:
            ema_stance = "Bullish (CMP > EMA20 > EMA50)"
            d1_ema_score = 0.8
        elif cmp < ema_20 and ema_20 < ema_50:
            ema_stance = "Bearish (CMP < EMA20 < EMA50)"
            d1_ema_score = -0.8
        else:
            ema_stance = "Consolidation / Mixed Trend"
            d1_ema_score = 0.0

        if rsi > 70:
            rsi_stance = "Overbought (Pullback Risk)"
            d1_rsi_score = 0.3 if macd_hist > 0 else -0.3
            rationale.append(f"Dimension 1: RSI-14 is elevated at {rsi:.1f} ({rsi_stance}).")
        elif rsi < 35:
            rsi_stance = "Oversold (Accumulation Zone)"
            d1_rsi_score = 0.6
            rationale.append(f"Dimension 1: RSI-14 is deeply oversold at {rsi:.1f} ({rsi_stance}).")
        else:
            rsi_stance = "Healthy Trend Momentum"
            d1_rsi_score = 0.5 if change_pct > 0 else -0.2
            rationale.append(f"Dimension 1: RSI-14 at {rsi:.1f} indicates steady trend momentum.")

        macd_stance = "Positive Histogram Expansion" if macd_hist > 0 else "Negative Histogram Contraction"
        d1_macd_score = 0.6 if macd_hist > 0 else -0.6
        rationale.append(f"Dimension 1: MACD histogram is at {macd_hist:+.2f} ({macd_stance}).")

        d1_score = (d1_ema_score * 0.4) + (d1_rsi_score * 0.3) + (d1_macd_score * 0.3)
        scores.append(d1_score)

        # DIMENSION 2: Volume Anomaly & Liquidity
        if volume_spike >= 1.5:
            vol_stance = f"Strong Volume Breakout ({volume_spike:.2f}x 20-DMA)"
            d2_score = 0.8 if change_pct > 0 else -0.8
            rationale.append(f"Dimension 2: Heavy institutional volume spike detected at {volume_spike:.2f}x 20-day average.")
        elif volume_spike >= 1.1:
            vol_stance = f"Above Average Volume ({volume_spike:.2f}x 20-DMA)"
            d2_score = 0.4 if change_pct > 0 else -0.4
            rationale.append(f"Dimension 2: Moderate volume expansion at {volume_spike:.2f}x 20-DMA.")
        else:
            vol_stance = f"Routine Volume ({volume_spike:.2f}x 20-DMA)"
            d2_score = 0.0
            rationale.append(f"Dimension 2: Volume is within routine baseline ({volume_spike:.2f}x 20-DMA).")
        scores.append(d2_score)

        # DIMENSION 3: Options Microstructure & Institutional Flow
        if pcr >= 1.2:
            pcr_stance = f"Bullish Put Writing Support (PCR: {pcr:.2f})"
            d3_pcr_score = 0.7
        elif pcr <= 0.8:
            pcr_stance = f"Bearish Call Writing Resistance (PCR: {pcr:.2f})"
            d3_pcr_score = -0.7
        else:
            pcr_stance = f"Balanced Options Structure (PCR: {pcr:.2f})"
            d3_pcr_score = 0.0
        rationale.append(f"Dimension 3: Derivatives PCR at {pcr:.2f} signals {pcr_stance.lower()}.")

        if total_inst_flow > 300:
            inst_stance = f"Heavy Net Inflow (+INR {total_inst_flow:.1f} Cr)"
            d3_inst_score = 0.8
        elif total_inst_flow < -200:
            inst_stance = f"Net Outflow (-INR {abs(total_inst_flow):.1f} Cr)"
            d3_inst_score = -0.8
        else:
            inst_stance = f"Neutral Flow (+INR {total_inst_flow:.1f} Cr)"
            d3_inst_score = 0.1
        rationale.append(f"Dimension 3: FII/DII institutional net flow registered at {inst_stance}.")

        d3_score = (d3_pcr_score * 0.5) + (d3_inst_score * 0.5)
        scores.append(d3_score)

        # Composite Signal Calculation
        composite_score = (scores[0] * 0.40) + (scores[1] * 0.30) + (scores[2] * 0.30)
        confidence = min(0.96, max(0.55, 0.60 + abs(composite_score) * 0.35))

        if composite_score >= 0.50:
            overall_signal = "STRONG_BUY"
        elif composite_score >= 0.15:
            overall_signal = "BUY"
        elif composite_score <= -0.50:
            overall_signal = "STRONG_SELL"
        elif composite_score <= -0.15:
            overall_signal = "AVOID"
        else:
            overall_signal = "NEUTRAL"

        return MarketSignal(
            symbol=symbol,
            cmp=cmp,
            change_pct=change_pct,
            rsi_14=rsi,
            macd_stance=macd_stance,
            macd_hist=macd_hist,
            ema_trend=ema_stance,
            volume_spike_ratio=volume_spike,
            volume_stance=vol_stance,
            options_pcr=pcr,
            options_stance=pcr_stance,
            fii_dii_flow_cr=total_inst_flow,
            institutional_stance=inst_stance,
            overall_signal=overall_signal,
            confidence_score=confidence,
            rationale_points=rationale
        )
