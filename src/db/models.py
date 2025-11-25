"""Database models for pattern recognition engine."""

from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, Index, Integer,
                        String, Text)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PatternDetectionModel(Base):
    """Model for storing pattern detections."""

    __tablename__ = "pattern_detections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(String(255), unique=True, nullable=False, index=True)

    # Pattern info
    pattern_name = Column(String(255), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False, index=True)

    # Market info
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(50), nullable=True)
    timeframe = Column(String(20), nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Signal info
    signal = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False, index=True)

    # Price levels
    entry_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)

    # Additional data
    metadata_json = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_symbol_timestamp", "symbol", "timestamp"),
        Index("idx_pattern_confidence", "pattern_name", "confidence"),
    )

    def __repr__(self):
        return f"<PatternDetection(id={self.id}, pattern={self.pattern_name}, symbol={self.symbol})>"


class TradeModel(Base):
    """Model for storing backtest and live trades."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(255), unique=True, nullable=False, index=True)

    # Trade info
    symbol = Column(String(50), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # 'long' or 'short'
    position_size = Column(Float, nullable=False)

    # Entry
    entry_time = Column(DateTime, nullable=False, index=True)
    entry_price = Column(Float, nullable=False)

    # Exit
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)

    # P&L
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    fees = Column(Float, default=0.0)

    # Associated pattern
    pattern_id = Column(String(255), nullable=True, index=True)

    # Strategy info
    strategy_name = Column(String(255), nullable=True)

    # Status
    is_open = Column(Boolean, default=True, index=True)

    # Additional data
    metadata_json = Column(JSON, nullable=True)

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_symbol_entry", "symbol", "entry_time"),
        Index("idx_open_trades", "is_open", "symbol"),
    )

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, direction={self.direction}, pnl={self.pnl})>"


class AnalysisResultModel(Base):
    """Model for storing analysis results."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(255), unique=True, nullable=False, index=True)

    # Market info
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Overall assessment
    overall_signal = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    trend = Column(String(20), nullable=False)
    volatility = Column(Float, nullable=False)
    volume_profile = Column(String(20), nullable=False)
    risk_score = Column(Float, nullable=False)

    # Price levels
    current_price = Column(Float, nullable=False)
    support_levels = Column(JSON, nullable=True)  # Array of floats
    resistance_levels = Column(JSON, nullable=True)  # Array of floats

    # Pattern summary
    num_patterns_detected = Column(Integer, default=0)
    patterns_summary = Column(JSON, nullable=True)  # Summary of patterns

    # Insights
    insights = Column(JSON, nullable=True)  # Array of strings

    # Additional data
    metadata_json = Column(JSON, nullable=True)

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_symbol_timestamp_analysis", "symbol", "timestamp"),
        Index("idx_signal_confidence", "overall_signal", "confidence"),
    )

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, symbol={self.symbol}, signal={self.overall_signal})>"


class AlertModel(Base):
    """Model for storing alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(255), unique=True, nullable=False, index=True)

    # Alert info
    timestamp = Column(DateTime, nullable=False, index=True)
    priority = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)

    # Associated pattern
    pattern_id = Column(String(255), nullable=True, index=True)
    pattern_name = Column(String(255), nullable=True)
    symbol = Column(String(50), nullable=False, index=True)

    # Delivery tracking
    sent = Column(Boolean, default=False, index=True)
    sent_to = Column(JSON, nullable=True)  # Array of channels
    acknowledged = Column(Boolean, default=False)

    # Metadata
    conditions = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_priority_sent", "priority", "sent"),
        Index("idx_symbol_timestamp_alert", "symbol", "timestamp"),
    )

    def __repr__(self):
        return f"<Alert(id={self.id}, priority={self.priority}, symbol={self.symbol})>"


class BacktestResultModel(Base):
    """Model for storing backtest results."""

    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(String(255), unique=True, nullable=False, index=True)

    # Backtest info
    strategy_name = Column(String(255), nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(20), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Capital
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)

    # Performance metrics
    total_return = Column(Float, nullable=False)
    total_return_pct = Column(Float, nullable=False, index=True)
    annualized_return_pct = Column(Float, nullable=True)

    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)

    # Ratios
    profit_factor = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True, index=True)
    sortino_ratio = Column(Float, nullable=True)
    calmar_ratio = Column(Float, nullable=True)

    # Risk metrics
    max_drawdown = Column(Float, nullable=True)
    max_drawdown_pct = Column(Float, nullable=True)

    # Additional metrics
    avg_win = Column(Float, nullable=True)
    avg_loss = Column(Float, nullable=True)
    expectancy = Column(Float, nullable=True)

    # Full metrics
    metrics_json = Column(JSON, nullable=True)  # Complete metrics dict

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_strategy_return", "strategy_name", "total_return_pct"),
        Index("idx_symbol_dates", "symbol", "start_date", "end_date"),
    )

    def __repr__(self):
        return f"<BacktestResult(id={self.id}, strategy={self.strategy_name}, return={self.total_return_pct:.2f}%)>"
