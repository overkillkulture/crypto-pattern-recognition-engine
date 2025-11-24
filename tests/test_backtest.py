"""Tests for backtesting framework."""

import pytest
import numpy as np
from datetime import datetime

from src.core.types import OHLCV, PatternResult, PatternType, SignalType, Timeframe
from src.backtest.engine import BacktestEngine, Trade
from src.backtest.strategy import SimplePatternStrategy, TrendFollowingStrategy
from src.backtest.metrics import BacktestMetrics


def create_test_data(length: int = 100, trend: str = 'uptrend') -> OHLCV:
    """Create test OHLCV data."""
    timestamps = np.arange(length, dtype=float) * 3600

    if trend == 'uptrend':
        prices = np.linspace(100, 150, length)
    elif trend == 'downtrend':
        prices = np.linspace(150, 100, length)
    else:
        prices = np.ones(length) * 100

    return OHLCV(
        timestamps=timestamps,
        open=prices,
        high=prices + 2,
        low=prices - 2,
        close=prices,
        volume=np.ones(length) * 1000,
    )


def create_test_pattern(signal: SignalType, confidence: float = 0.80) -> PatternResult:
    """Create test pattern."""
    return PatternResult(
        pattern_id="test_id",
        pattern_name="Test Pattern",
        pattern_type=PatternType.TECHNICAL_INDICATOR,
        symbol="BTC/USDT",
        timeframe=Timeframe.ONE_HOUR,
        timestamp=datetime.now(),
        confidence=confidence,
        signal=signal,
        metadata={},
    )


class TestTrade:
    """Tests for Trade class."""

    def test_trade_initialization(self):
        """Test trade initialization."""
        trade = Trade(
            entry_time=datetime.now(),
            entry_price=100.0,
            position_size=1000.0,
            direction='long',
        )

        assert trade.entry_price == 100.0
        assert trade.position_size == 1000.0
        assert trade.direction == 'long'
        assert trade.is_open()

    def test_trade_close_long(self):
        """Test closing a long trade."""
        trade = Trade(
            entry_time=datetime.now(),
            entry_price=100.0,
            position_size=1000.0,
            direction='long',
        )

        trade.close(datetime.now(), 110.0, fee_rate=0.001)

        assert not trade.is_open()
        assert trade.exit_price == 110.0
        assert trade.pnl_pct == 0.10  # 10% gain
        assert trade.pnl > 0  # Profitable after fees

    def test_trade_close_short(self):
        """Test closing a short trade."""
        trade = Trade(
            entry_time=datetime.now(),
            entry_price=100.0,
            position_size=1000.0,
            direction='short',
        )

        trade.close(datetime.now(), 90.0, fee_rate=0.001)

        assert not trade.is_open()
        assert trade.pnl_pct == 0.10  # 10% gain (short)
        assert trade.pnl > 0

    def test_trade_loss(self):
        """Test a losing trade."""
        trade = Trade(
            entry_time=datetime.now(),
            entry_price=100.0,
            position_size=1000.0,
            direction='long',
        )

        trade.close(datetime.now(), 95.0, fee_rate=0.001)

        assert trade.pnl < 0  # Losing trade


class TestBacktestEngine:
    """Tests for BacktestEngine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = BacktestEngine(
            initial_capital=10000.0,
            position_size_pct=0.10,
            fee_rate=0.001,
        )

        assert engine.initial_capital == 10000.0
        assert engine.capital == 10000.0
        assert engine.position_size_pct == 0.10
        assert engine.fee_rate == 0.001

    @pytest.mark.asyncio
    async def test_backtest_no_signals(self):
        """Test backtest with no trading signals."""
        engine = BacktestEngine(initial_capital=10000.0)
        strategy = SimplePatternStrategy(min_confidence=0.99)  # Very high threshold
        data = create_test_data(100)
        patterns = []  # No patterns

        results = await engine.run(strategy, data, patterns)

        assert results['final_capital'] == 10000.0  # No trades
        assert len(results['trades']) == 0

    @pytest.mark.asyncio
    async def test_backtest_with_buy_signals(self):
        """Test backtest with buy signals."""
        engine = BacktestEngine(initial_capital=10000.0)
        strategy = SimplePatternStrategy(min_confidence=0.75)

        # Create uptrend data
        data = create_test_data(100, trend='uptrend')

        # Create buy patterns at beginning
        patterns = [create_test_pattern(SignalType.BUY, confidence=0.80)]
        patterns[0].timestamp = datetime.fromtimestamp(data.timestamps[10])

        results = await engine.run(strategy, data, patterns)

        # Should have made at least one trade
        assert len(results['trades']) > 0

    @pytest.mark.asyncio
    async def test_backtest_respects_capital(self):
        """Test that backtest respects initial capital."""
        engine = BacktestEngine(
            initial_capital=10000.0,
            position_size_pct=0.10,
        )

        strategy = SimplePatternStrategy()
        data = create_test_data(50)

        # Create pattern
        pattern = create_test_pattern(SignalType.BUY, confidence=0.85)
        pattern.timestamp = datetime.fromtimestamp(data.timestamps[10])

        results = await engine.run(strategy, data, [pattern])

        # Final capital should not exceed initial by absurd amounts
        assert results['final_capital'] < 20000.0  # Reasonable bounds


class TestSimplePatternStrategy:
    """Tests for SimplePatternStrategy."""

    def test_strategy_initialization(self):
        """Test strategy initialization."""
        strategy = SimplePatternStrategy(
            min_confidence=0.75,
            stop_loss_pct=0.02,
            take_profit_pct=0.05,
        )

        assert strategy.name == "Simple Pattern Strategy"
        assert strategy.min_confidence == 0.75
        assert strategy.stop_loss_pct == 0.02
        assert strategy.take_profit_pct == 0.05

    def test_strategy_should_enter_buy(self):
        """Test strategy enters on buy signal."""
        strategy = SimplePatternStrategy(min_confidence=0.75)

        pattern = create_test_pattern(SignalType.BUY, confidence=0.80)
        data = create_test_data(50)

        should_enter, direction = strategy.should_enter(
            [pattern],
            datetime.now(),
            100.0,
            data,
            10,
        )

        assert should_enter
        assert direction == 'long'

    def test_strategy_should_enter_sell(self):
        """Test strategy enters on sell signal."""
        strategy = SimplePatternStrategy(min_confidence=0.75)

        pattern = create_test_pattern(SignalType.SELL, confidence=0.80)
        data = create_test_data(50)

        should_enter, direction = strategy.should_enter(
            [pattern],
            datetime.now(),
            100.0,
            data,
            10,
        )

        assert should_enter
        assert direction == 'short'

    def test_strategy_ignores_low_confidence(self):
        """Test strategy ignores low confidence patterns."""
        strategy = SimplePatternStrategy(min_confidence=0.90)

        pattern = create_test_pattern(SignalType.BUY, confidence=0.70)  # Too low
        data = create_test_data(50)

        should_enter, direction = strategy.should_enter(
            [pattern],
            datetime.now(),
            100.0,
            data,
            10,
        )

        assert not should_enter

    def test_strategy_stop_loss(self):
        """Test strategy exits on stop loss."""
        strategy = SimplePatternStrategy(stop_loss_pct=0.02)

        trade = Trade(
            entry_time=datetime.now(),
            entry_price=100.0,
            position_size=1000.0,
            direction='long',
        )

        data = create_test_data(50)

        # Price dropped 3% (beyond 2% stop loss)
        should_exit, reason = strategy.should_exit(
            trade,
            datetime.now(),
            97.0,  # 3% loss
            data,
            10,
        )

        assert should_exit
        assert reason == 'stop_loss'

    def test_strategy_take_profit(self):
        """Test strategy exits on take profit."""
        strategy = SimplePatternStrategy(take_profit_pct=0.05)

        trade = Trade(
            entry_time=datetime.now(),
            entry_price=100.0,
            position_size=1000.0,
            direction='long',
        )

        data = create_test_data(50)

        # Price increased 6% (beyond 5% take profit)
        should_exit, reason = strategy.should_exit(
            trade,
            datetime.now(),
            106.0,  # 6% gain
            data,
            10,
        )

        assert should_exit
        assert reason == 'take_profit'


class TestTrendFollowingStrategy:
    """Tests for TrendFollowingStrategy."""

    def test_trend_strategy_initialization(self):
        """Test trend strategy initialization."""
        strategy = TrendFollowingStrategy(fast_ma=20, slow_ma=50)

        assert strategy.name == "Trend Following Strategy"
        assert strategy.fast_ma == 20
        assert strategy.slow_ma == 50

    def test_trend_strategy_requires_data(self):
        """Test trend strategy requires sufficient data."""
        strategy = TrendFollowingStrategy(fast_ma=20, slow_ma=50)

        pattern = create_test_pattern(SignalType.BUY, confidence=0.80)
        data = create_test_data(30)  # Not enough for slow MA

        should_enter, direction = strategy.should_enter(
            [pattern],
            datetime.now(),
            100.0,
            data,
            20,  # Index 20 < slow_ma 50
        )

        assert not should_enter  # Insufficient data


class TestBacktestMetrics:
    """Tests for BacktestMetrics."""

    def test_metrics_empty_trades(self):
        """Test metrics calculation with no trades."""
        engine = BacktestEngine(initial_capital=10000.0)
        metrics = BacktestMetrics.calculate(engine)

        assert metrics['total_return'] == 0.0
        assert metrics['total_trades'] == 0
        assert metrics['win_rate'] == 0.0

    def test_metrics_with_trades(self):
        """Test metrics calculation with trades."""
        engine = BacktestEngine(initial_capital=10000.0)

        # Create winning trade
        trade1 = Trade(
            entry_time=datetime.now(),
            entry_price=100.0,
            position_size=1000.0,
            direction='long',
        )
        trade1.close(datetime.now(), 110.0, fee_rate=0.001)
        engine.trades.append(trade1)

        # Create losing trade
        trade2 = Trade(
            entry_time=datetime.now(),
            entry_price=100.0,
            position_size=1000.0,
            direction='long',
        )
        trade2.close(datetime.now(), 95.0, fee_rate=0.001)
        engine.trades.append(trade2)

        engine.capital = 10000.0 + trade1.pnl + trade2.pnl

        metrics = BacktestMetrics.calculate(engine)

        assert metrics['total_trades'] == 2
        assert metrics['winning_trades'] == 1
        assert metrics['losing_trades'] == 1
        assert metrics['win_rate'] == 50.0

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation."""
        returns = np.array([0.01, 0.02, -0.01, 0.03, 0.01])
        sharpe = BacktestMetrics._calculate_sharpe(returns)

        assert isinstance(sharpe, float)
        # Sharpe should be reasonable
        assert -10 < sharpe < 10

    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        equity = np.array([10000, 11000, 10500, 9500, 10000, 11500])

        max_dd, max_dd_pct = BacktestMetrics._calculate_max_drawdown(equity)

        assert max_dd >= 0
        assert max_dd_pct >= 0
        # Max DD should be when we went from 11000 to 9500
        assert max_dd_pct > 10  # More than 10%
