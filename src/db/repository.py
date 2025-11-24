"""Repository layer for database operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, and_, or_, desc, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    PatternDetectionModel,
    TradeModel,
    AnalysisResultModel,
    AlertModel,
    BacktestResultModel,
)
from src.core.types import PatternResult, AnalysisResult


class PatternDetectionRepository:
    """Repository for pattern detection operations."""

    @staticmethod
    def save_pattern(session: Session, pattern: PatternResult) -> PatternDetectionModel:
        """
        Save a pattern detection to the database.

        Args:
            session: Database session
            pattern: Pattern result to save

        Returns:
            Saved pattern model
        """
        model = PatternDetectionModel(
            pattern_id=pattern.pattern_id,
            pattern_name=pattern.pattern_name,
            pattern_type=pattern.pattern_type.value,
            symbol=pattern.symbol,
            exchange=pattern.exchange.value if pattern.exchange else None,
            timeframe=pattern.timeframe.value if pattern.timeframe else None,
            timestamp=pattern.timestamp,
            signal=pattern.signal.value,
            confidence=pattern.confidence,
            entry_price=pattern.entry_price,
            target_price=pattern.target_price,
            stop_loss=pattern.stop_loss,
            metadata_json=pattern.metadata,
            description=pattern.description,
        )

        session.add(model)
        session.flush()
        return model

    @staticmethod
    async def save_pattern_async(session: AsyncSession, pattern: PatternResult) -> PatternDetectionModel:
        """Save a pattern detection (async)."""
        model = PatternDetectionModel(
            pattern_id=pattern.pattern_id,
            pattern_name=pattern.pattern_name,
            pattern_type=pattern.pattern_type.value,
            symbol=pattern.symbol,
            exchange=pattern.exchange.value if pattern.exchange else None,
            timeframe=pattern.timeframe.value if pattern.timeframe else None,
            timestamp=pattern.timestamp,
            signal=pattern.signal.value,
            confidence=pattern.confidence,
            entry_price=pattern.entry_price,
            target_price=pattern.target_price,
            stop_loss=pattern.stop_loss,
            metadata_json=pattern.metadata,
            description=pattern.description,
        )

        session.add(model)
        await session.flush()
        return model

    @staticmethod
    def get_by_pattern_id(session: Session, pattern_id: str) -> Optional[PatternDetectionModel]:
        """Get pattern by ID."""
        return session.query(PatternDetectionModel).filter(
            PatternDetectionModel.pattern_id == pattern_id
        ).first()

    @staticmethod
    def get_recent_patterns(
        session: Session,
        symbol: Optional[str] = None,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 100,
    ) -> List[PatternDetectionModel]:
        """
        Get recent pattern detections with filters.

        Args:
            session: Database session
            symbol: Filter by symbol
            pattern_type: Filter by pattern type
            min_confidence: Minimum confidence threshold
            limit: Maximum number of results

        Returns:
            List of pattern detections
        """
        query = session.query(PatternDetectionModel)

        if symbol:
            query = query.filter(PatternDetectionModel.symbol == symbol)
        if pattern_type:
            query = query.filter(PatternDetectionModel.pattern_type == pattern_type)
        if min_confidence > 0:
            query = query.filter(PatternDetectionModel.confidence >= min_confidence)

        return query.order_by(desc(PatternDetectionModel.timestamp)).limit(limit).all()

    @staticmethod
    def delete_old_patterns(session: Session, before_date: datetime) -> int:
        """Delete patterns older than specified date."""
        result = session.query(PatternDetectionModel).filter(
            PatternDetectionModel.timestamp < before_date
        ).delete()
        return result


class TradeRepository:
    """Repository for trade operations."""

    @staticmethod
    def save_trade(
        session: Session,
        trade_id: str,
        symbol: str,
        direction: str,
        position_size: float,
        entry_time: datetime,
        entry_price: float,
        pattern_id: Optional[str] = None,
        strategy_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TradeModel:
        """
        Save a new trade to the database.

        Args:
            session: Database session
            trade_id: Unique trade identifier
            symbol: Trading symbol
            direction: 'long' or 'short'
            position_size: Size of the position
            entry_time: Entry timestamp
            entry_price: Entry price
            pattern_id: Associated pattern ID
            strategy_name: Strategy name
            metadata: Additional metadata

        Returns:
            Saved trade model
        """
        model = TradeModel(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            position_size=position_size,
            entry_time=entry_time,
            entry_price=entry_price,
            pattern_id=pattern_id,
            strategy_name=strategy_name,
            metadata_json=metadata,
            is_open=True,
        )

        session.add(model)
        session.flush()
        return model

    @staticmethod
    def close_trade(
        session: Session,
        trade_id: str,
        exit_time: datetime,
        exit_price: float,
        pnl: float,
        pnl_pct: float,
        fees: float = 0.0,
    ) -> Optional[TradeModel]:
        """
        Close an open trade.

        Args:
            session: Database session
            trade_id: Trade identifier
            exit_time: Exit timestamp
            exit_price: Exit price
            pnl: Profit/loss in absolute terms
            pnl_pct: Profit/loss percentage
            fees: Trading fees

        Returns:
            Updated trade model or None if not found
        """
        trade = session.query(TradeModel).filter(TradeModel.trade_id == trade_id).first()

        if trade:
            trade.exit_time = exit_time
            trade.exit_price = exit_price
            trade.pnl = pnl
            trade.pnl_pct = pnl_pct
            trade.fees = fees
            trade.is_open = False
            trade.updated_at = datetime.utcnow()
            session.flush()

        return trade

    @staticmethod
    def get_open_trades(session: Session, symbol: Optional[str] = None) -> List[TradeModel]:
        """Get all open trades, optionally filtered by symbol."""
        query = session.query(TradeModel).filter(TradeModel.is_open == True)

        if symbol:
            query = query.filter(TradeModel.symbol == symbol)

        return query.order_by(desc(TradeModel.entry_time)).all()

    @staticmethod
    def get_trade_history(
        session: Session,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[TradeModel]:
        """Get trade history with filters."""
        query = session.query(TradeModel).filter(TradeModel.is_open == False)

        if symbol:
            query = query.filter(TradeModel.symbol == symbol)
        if start_date:
            query = query.filter(TradeModel.entry_time >= start_date)
        if end_date:
            query = query.filter(TradeModel.entry_time <= end_date)

        return query.order_by(desc(TradeModel.entry_time)).limit(limit).all()

    @staticmethod
    def get_trade_statistics(session: Session, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Calculate trade statistics."""
        query = session.query(TradeModel).filter(TradeModel.is_open == False)

        if symbol:
            query = query.filter(TradeModel.symbol == symbol)

        trades = query.all()

        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
            }

        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl <= 0]

        return {
            'total_trades': len(trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(trades)) * 100,
            'total_pnl': sum(t.pnl for t in trades),
            'avg_pnl': sum(t.pnl for t in trades) / len(trades),
            'total_fees': sum(t.fees for t in trades),
        }


class AnalysisResultRepository:
    """Repository for analysis result operations."""

    @staticmethod
    def save_analysis(session: Session, analysis: AnalysisResult) -> AnalysisResultModel:
        """
        Save an analysis result to the database.

        Args:
            session: Database session
            analysis: Analysis result to save

        Returns:
            Saved analysis model
        """
        model = AnalysisResultModel(
            analysis_id=analysis.analysis_id,
            symbol=analysis.symbol,
            timeframe=analysis.timeframe.value,
            timestamp=analysis.timestamp,
            overall_signal=analysis.overall_signal.value,
            confidence=analysis.confidence,
            trend=analysis.trend,
            volatility=analysis.volatility,
            volume_profile=analysis.volume_profile,
            risk_score=analysis.risk_score,
            current_price=analysis.metadata.get('price', 0.0),
            support_levels=analysis.support_levels,
            resistance_levels=analysis.resistance_levels,
            num_patterns_detected=len(analysis.patterns),
            patterns_summary=[
                {
                    'name': p.pattern_name,
                    'type': p.pattern_type.value,
                    'signal': p.signal.value,
                    'confidence': p.confidence,
                }
                for p in analysis.patterns[:10]  # Store top 10
            ],
            insights=analysis.insights,
            metadata_json=analysis.metadata,
        )

        session.add(model)
        session.flush()
        return model

    @staticmethod
    def get_latest_analysis(session: Session, symbol: str) -> Optional[AnalysisResultModel]:
        """Get the latest analysis for a symbol."""
        return (
            session.query(AnalysisResultModel)
            .filter(AnalysisResultModel.symbol == symbol)
            .order_by(desc(AnalysisResultModel.timestamp))
            .first()
        )

    @staticmethod
    def get_analysis_history(
        session: Session,
        symbol: str,
        start_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AnalysisResultModel]:
        """Get analysis history for a symbol."""
        query = session.query(AnalysisResultModel).filter(
            AnalysisResultModel.symbol == symbol
        )

        if start_date:
            query = query.filter(AnalysisResultModel.timestamp >= start_date)

        return query.order_by(desc(AnalysisResultModel.timestamp)).limit(limit).all()


class AlertRepository:
    """Repository for alert operations."""

    @staticmethod
    def save_alert(
        session: Session,
        alert_id: str,
        timestamp: datetime,
        priority: str,
        message: str,
        symbol: str,
        pattern_id: Optional[str] = None,
        pattern_name: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AlertModel:
        """
        Save a new alert to the database.

        Args:
            session: Database session
            alert_id: Unique alert identifier
            timestamp: Alert timestamp
            priority: Alert priority (low/medium/high/critical)
            message: Alert message
            symbol: Trading symbol
            pattern_id: Associated pattern ID
            pattern_name: Associated pattern name
            conditions: Alert conditions
            metadata: Additional metadata

        Returns:
            Saved alert model
        """
        model = AlertModel(
            alert_id=alert_id,
            timestamp=timestamp,
            priority=priority,
            message=message,
            symbol=symbol,
            pattern_id=pattern_id,
            pattern_name=pattern_name,
            conditions=conditions,
            metadata_json=metadata,
            sent=False,
            acknowledged=False,
        )

        session.add(model)
        session.flush()
        return model

    @staticmethod
    def mark_as_sent(
        session: Session,
        alert_id: str,
        sent_to: List[str],
    ) -> Optional[AlertModel]:
        """Mark an alert as sent."""
        alert = session.query(AlertModel).filter(AlertModel.alert_id == alert_id).first()

        if alert:
            alert.sent = True
            alert.sent_to = sent_to
            session.flush()

        return alert

    @staticmethod
    def acknowledge_alert(session: Session, alert_id: str) -> Optional[AlertModel]:
        """Acknowledge an alert."""
        alert = session.query(AlertModel).filter(AlertModel.alert_id == alert_id).first()

        if alert:
            alert.acknowledged = True
            session.flush()

        return alert

    @staticmethod
    def get_unsent_alerts(session: Session, priority: Optional[str] = None) -> List[AlertModel]:
        """Get alerts that haven't been sent yet."""
        query = session.query(AlertModel).filter(AlertModel.sent == False)

        if priority:
            query = query.filter(AlertModel.priority == priority)

        return query.order_by(desc(AlertModel.priority), AlertModel.timestamp).all()

    @staticmethod
    def get_recent_alerts(
        session: Session,
        symbol: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
    ) -> List[AlertModel]:
        """Get recent alerts with filters."""
        query = session.query(AlertModel)

        if symbol:
            query = query.filter(AlertModel.symbol == symbol)
        if priority:
            query = query.filter(AlertModel.priority == priority)

        return query.order_by(desc(AlertModel.timestamp)).limit(limit).all()


class BacktestResultRepository:
    """Repository for backtest result operations."""

    @staticmethod
    def save_backtest_result(
        session: Session,
        backtest_id: str,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        final_capital: float,
        metrics: Dict[str, Any],
    ) -> BacktestResultModel:
        """
        Save backtest results to the database.

        Args:
            session: Database session
            backtest_id: Unique backtest identifier
            strategy_name: Strategy name
            symbol: Trading symbol
            timeframe: Timeframe
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital
            final_capital: Final capital
            metrics: Complete metrics dictionary

        Returns:
            Saved backtest result model
        """
        model = BacktestResultModel(
            backtest_id=backtest_id,
            strategy_name=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=metrics.get('total_return', 0.0),
            total_return_pct=metrics.get('total_return_pct', 0.0),
            annualized_return_pct=metrics.get('annualized_return_pct'),
            total_trades=metrics.get('total_trades', 0),
            winning_trades=metrics.get('winning_trades', 0),
            losing_trades=metrics.get('losing_trades', 0),
            win_rate=metrics.get('win_rate'),
            profit_factor=metrics.get('profit_factor'),
            sharpe_ratio=metrics.get('sharpe_ratio'),
            sortino_ratio=metrics.get('sortino_ratio'),
            calmar_ratio=metrics.get('calmar_ratio'),
            max_drawdown=metrics.get('max_drawdown'),
            max_drawdown_pct=metrics.get('max_drawdown_pct'),
            avg_win=metrics.get('avg_win'),
            avg_loss=metrics.get('avg_loss'),
            expectancy=metrics.get('expectancy'),
            metrics_json=metrics,
        )

        session.add(model)
        session.flush()
        return model

    @staticmethod
    def get_backtest_by_id(session: Session, backtest_id: str) -> Optional[BacktestResultModel]:
        """Get backtest result by ID."""
        return session.query(BacktestResultModel).filter(
            BacktestResultModel.backtest_id == backtest_id
        ).first()

    @staticmethod
    def get_strategy_results(
        session: Session,
        strategy_name: str,
        symbol: Optional[str] = None,
    ) -> List[BacktestResultModel]:
        """Get all backtest results for a strategy."""
        query = session.query(BacktestResultModel).filter(
            BacktestResultModel.strategy_name == strategy_name
        )

        if symbol:
            query = query.filter(BacktestResultModel.symbol == symbol)

        return query.order_by(desc(BacktestResultModel.created_at)).all()

    @staticmethod
    def get_best_strategies(
        session: Session,
        metric: str = 'sharpe_ratio',
        limit: int = 10,
    ) -> List[BacktestResultModel]:
        """
        Get top performing strategies by metric.

        Args:
            session: Database session
            metric: Metric to sort by (sharpe_ratio, total_return_pct, etc.)
            limit: Number of results

        Returns:
            List of backtest results sorted by metric
        """
        order_column = getattr(BacktestResultModel, metric, BacktestResultModel.sharpe_ratio)
        return (
            session.query(BacktestResultModel)
            .order_by(desc(order_column))
            .limit(limit)
            .all()
        )

    @staticmethod
    def compare_strategies(
        session: Session,
        strategy_names: List[str],
        symbol: Optional[str] = None,
    ) -> List[BacktestResultModel]:
        """Compare multiple strategies."""
        query = session.query(BacktestResultModel).filter(
            BacktestResultModel.strategy_name.in_(strategy_names)
        )

        if symbol:
            query = query.filter(BacktestResultModel.symbol == symbol)

        return query.order_by(
            BacktestResultModel.strategy_name,
            desc(BacktestResultModel.total_return_pct)
        ).all()
