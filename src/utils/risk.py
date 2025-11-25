"""Risk management utilities for trading."""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PositionSize:
    """Position sizing recommendation."""

    quantity: float
    position_value: float
    risk_amount: float
    risk_pct: float
    stop_loss: float
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None


@dataclass
class RiskMetrics:
    """Risk metrics for a trading strategy or portfolio."""

    total_risk: float
    risk_per_trade: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    volatility: float
    var_95: float  # Value at Risk at 95% confidence
    cvar_95: float  # Conditional Value at Risk
    kelly_criterion: float


class RiskManager:
    """
    Risk management calculator for trading strategies.

    Provides position sizing, risk metrics, and risk limits enforcement.

    Example:
        risk_mgr = RiskManager(
            account_size=10000,
            risk_per_trade_pct=1.0,
            max_risk_pct=5.0
        )

        # Calculate position size
        position = risk_mgr.calculate_position_size(
            entry_price=50000,
            stop_loss=49000,
            risk_reward_ratio=2.0
        )

        print(f"Buy {position.quantity} units")
        print(f"Stop loss: ${position.stop_loss}")
        print(f"Take profit: ${position.take_profit}")
    """

    def __init__(
        self,
        account_size: float,
        risk_per_trade_pct: float = 1.0,
        max_risk_pct: float = 5.0,
        max_correlation: float = 0.7,
        use_kelly_criterion: bool = False,
    ):
        """
        Initialize risk manager.

        Args:
            account_size: Total account size
            risk_per_trade_pct: Risk per trade as % of account (e.g., 1.0 = 1%)
            max_risk_pct: Maximum total portfolio risk (e.g., 5.0 = 5%)
            max_correlation: Maximum correlation between positions
            use_kelly_criterion: Use Kelly criterion for position sizing
        """
        self.account_size = account_size
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_risk_pct = max_risk_pct
        self.max_correlation = max_correlation
        self.use_kelly_criterion = use_kelly_criterion

        # Track current risk
        self.open_risk: Dict[str, float] = {}

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        risk_reward_ratio: Optional[float] = None,
        symbol: Optional[str] = None,
    ) -> PositionSize:
        """
        Calculate optimal position size based on risk parameters.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_reward_ratio: Target risk/reward ratio (e.g., 2.0 = 2:1)
            symbol: Trading symbol (for risk tracking)

        Returns:
            PositionSize with recommended quantity and levels
        """
        # Calculate risk per share
        risk_per_unit = abs(entry_price - stop_loss)

        if risk_per_unit == 0:
            logger.error("Stop loss cannot equal entry price")
            return PositionSize(0, 0, 0, 0, stop_loss)

        # Calculate risk amount (dollar amount willing to lose)
        risk_amount = self.account_size * (self.risk_per_trade_pct / 100)

        # Adjust for current portfolio risk
        current_total_risk = sum(self.open_risk.values())
        remaining_risk = (
            self.max_risk_pct / 100
        ) * self.account_size - current_total_risk

        if remaining_risk < risk_amount:
            logger.warning(
                f"Reducing risk from ${risk_amount:.2f} to ${remaining_risk:.2f} "
                f"due to portfolio risk limits"
            )
            risk_amount = max(0, remaining_risk)

        # Calculate quantity
        quantity = risk_amount / risk_per_unit

        if quantity <= 0:
            logger.warning("Cannot open position: portfolio risk limit reached")
            return PositionSize(0, 0, 0, 0, stop_loss)

        # Calculate position value
        position_value = quantity * entry_price

        # Calculate take profit if risk/reward ratio provided
        take_profit = None
        if risk_reward_ratio:
            profit_per_unit = risk_per_unit * risk_reward_ratio
            if stop_loss < entry_price:  # Long position
                take_profit = entry_price + profit_per_unit
            else:  # Short position
                take_profit = entry_price - profit_per_unit

        # Track risk if symbol provided
        if symbol:
            self.open_risk[symbol] = risk_amount

        return PositionSize(
            quantity=quantity,
            position_value=position_value,
            risk_amount=risk_amount,
            risk_pct=self.risk_per_trade_pct,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward_ratio,
        )

    def calculate_stop_loss(
        self,
        entry_price: float,
        method: str = "fixed_pct",
        atr: Optional[float] = None,
        support: Optional[float] = None,
        pct: float = 2.0,
        atr_multiplier: float = 2.0,
    ) -> float:
        """
        Calculate stop loss using various methods.

        Args:
            entry_price: Entry price
            method: Method to use ('fixed_pct', 'atr', 'support')
            atr: Average True Range value (for ATR method)
            support: Support level (for support method)
            pct: Fixed percentage for 'fixed_pct' method
            atr_multiplier: ATR multiplier for 'atr' method

        Returns:
            Stop loss price
        """
        if method == "fixed_pct":
            # Fixed percentage below entry
            return entry_price * (1 - pct / 100)

        elif method == "atr":
            # ATR-based stop loss
            if atr is None:
                raise ValueError("ATR value required for 'atr' method")
            return entry_price - (atr * atr_multiplier)

        elif method == "support":
            # Support-based stop loss
            if support is None:
                raise ValueError("Support level required for 'support' method")
            # Place stop slightly below support
            return support * 0.99

        else:
            raise ValueError(f"Unknown method: {method}")

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        risk_reward_ratio: float = 2.0,
    ) -> float:
        """
        Calculate take profit based on risk/reward ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_reward_ratio: Target risk/reward (e.g., 2.0 = 2:1)

        Returns:
            Take profit price
        """
        risk_per_unit = abs(entry_price - stop_loss)
        reward_per_unit = risk_per_unit * risk_reward_ratio

        if stop_loss < entry_price:  # Long position
            return entry_price + reward_per_unit
        else:  # Short position
            return entry_price - reward_per_unit

    def calculate_kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion.

        Kelly % = W - [(1-W) / R]
        where W = win rate, R = avg_win / avg_loss

        Args:
            win_rate: Win rate (0-1)
            avg_win: Average winning trade size
            avg_loss: Average losing trade size (positive)

        Returns:
            Kelly percentage (0-1)
        """
        if avg_loss == 0:
            return 0.0

        win_loss_ratio = avg_win / avg_loss
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)

        # Cap Kelly at 25% (Kelly can be aggressive)
        return min(max(0, kelly), 0.25)

    def check_correlation(
        self,
        symbol1: str,
        symbol2: str,
        price_history: Dict[str, np.ndarray],
    ) -> float:
        """
        Calculate correlation between two symbols.

        Args:
            symbol1: First symbol
            symbol2: Second symbol
            price_history: Dictionary of symbol -> price array

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if symbol1 not in price_history or symbol2 not in price_history:
            return 0.0

        prices1 = price_history[symbol1]
        prices2 = price_history[symbol2]

        # Calculate returns
        returns1 = np.diff(prices1) / prices1[:-1]
        returns2 = np.diff(prices2) / prices2[:-1]

        # Align lengths
        min_len = min(len(returns1), len(returns2))
        returns1 = returns1[-min_len:]
        returns2 = returns2[-min_len:]

        # Calculate correlation
        return np.corrcoef(returns1, returns2)[0, 1]

    def calculate_value_at_risk(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
    ) -> Tuple[float, float]:
        """
        Calculate Value at Risk (VaR) and Conditional VaR.

        Args:
            returns: Array of historical returns
            confidence_level: Confidence level (e.g., 0.95 = 95%)

        Returns:
            Tuple of (VaR, CVaR)
        """
        # Calculate VaR
        var = np.percentile(returns, (1 - confidence_level) * 100)

        # Calculate CVaR (average of returns below VaR)
        cvar = returns[returns <= var].mean()

        return var, cvar

    def calculate_sharpe_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            returns: Array of returns
            risk_free_rate: Risk-free rate
            periods_per_year: Trading periods per year (252 for daily)

        Returns:
            Sharpe ratio
        """
        excess_returns = returns - risk_free_rate
        if len(excess_returns) == 0 or np.std(excess_returns) == 0:
            return 0.0

        return (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(
            periods_per_year
        )

    def calculate_sortino_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> float:
        """
        Calculate Sortino ratio (like Sharpe but uses downside deviation).

        Args:
            returns: Array of returns
            risk_free_rate: Risk-free rate
            periods_per_year: Trading periods per year

        Returns:
            Sortino ratio
        """
        excess_returns = returns - risk_free_rate

        # Only consider negative returns for downside deviation
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return 0.0

        downside_deviation = np.std(downside_returns)
        if downside_deviation == 0:
            return 0.0

        return (np.mean(excess_returns) / downside_deviation) * np.sqrt(
            periods_per_year
        )

    def calculate_max_drawdown(
        self, equity_curve: np.ndarray
    ) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown from equity curve.

        Args:
            equity_curve: Array of equity values over time

        Returns:
            Tuple of (max_drawdown_pct, start_idx, end_idx)
        """
        cummax = np.maximum.accumulate(equity_curve)
        drawdown = (cummax - equity_curve) / cummax

        max_dd = np.max(drawdown)
        end_idx = np.argmax(drawdown)

        # Find start of drawdown
        start_idx = 0
        for i in range(end_idx, -1, -1):
            if equity_curve[i] == cummax[end_idx]:
                start_idx = i
                break

        return max_dd * 100, start_idx, end_idx

    def calculate_risk_metrics(
        self,
        returns: np.ndarray,
        equity_curve: np.ndarray,
        risk_free_rate: float = 0.0,
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics.

        Args:
            returns: Array of returns
            equity_curve: Equity curve over time
            risk_free_rate: Risk-free rate

        Returns:
            RiskMetrics object
        """
        # Calculate metrics
        sharpe = self.calculate_sharpe_ratio(returns, risk_free_rate)
        sortino = self.calculate_sortino_ratio(returns, risk_free_rate)
        max_dd, _, _ = self.calculate_max_drawdown(equity_curve)
        var_95, cvar_95 = self.calculate_value_at_risk(returns, 0.95)
        volatility = np.std(returns) * np.sqrt(252) * 100

        # Calculate Kelly if possible
        winning_returns = returns[returns > 0]
        losing_returns = returns[returns < 0]

        if len(winning_returns) > 0 and len(losing_returns) > 0:
            win_rate = len(winning_returns) / len(returns)
            avg_win = np.mean(winning_returns)
            avg_loss = abs(np.mean(losing_returns))
            kelly = self.calculate_kelly_criterion(win_rate, avg_win, avg_loss)
        else:
            kelly = 0.0

        return RiskMetrics(
            total_risk=sum(self.open_risk.values()),
            risk_per_trade=self.account_size * (self.risk_per_trade_pct / 100),
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            volatility=volatility,
            var_95=var_95,
            cvar_95=cvar_95,
            kelly_criterion=kelly,
        )

    def close_position_risk(self, symbol: str):
        """Remove symbol from risk tracking (called when position closes)."""
        if symbol in self.open_risk:
            del self.open_risk[symbol]

    def get_remaining_risk_capacity(self) -> float:
        """Get remaining risk capacity as percentage of account."""
        current_risk = sum(self.open_risk.values())
        max_risk = (self.max_risk_pct / 100) * self.account_size
        remaining = max_risk - current_risk
        return (remaining / self.account_size) * 100

    def can_open_position(self, risk_amount: float) -> bool:
        """Check if we have capacity to open a new position."""
        current_risk = sum(self.open_risk.values())
        max_risk = (self.max_risk_pct / 100) * self.account_size
        return (current_risk + risk_amount) <= max_risk

    def print_risk_summary(self):
        """Print risk management summary."""
        print("\n" + "=" * 70)
        print("RISK MANAGEMENT SUMMARY")
        print("=" * 70)
        print(f"Account Size: ${self.account_size:,.2f}")
        print(
            f"Risk Per Trade: {self.risk_per_trade_pct}% (${self.account_size * self.risk_per_trade_pct / 100:,.2f})"
        )
        print(
            f"Max Portfolio Risk: {self.max_risk_pct}% (${self.account_size * self.max_risk_pct / 100:,.2f})"
        )

        current_risk = sum(self.open_risk.values())
        current_risk_pct = (current_risk / self.account_size) * 100

        print(f"\nCurrent Risk: ${current_risk:,.2f} ({current_risk_pct:.2f}%)")
        print(f"Remaining Capacity: {self.get_remaining_risk_capacity():.2f}%")

        if self.open_risk:
            print(f"\nOpen Positions Risk:")
            for symbol, risk in self.open_risk.items():
                risk_pct = (risk / self.account_size) * 100
                print(f"  {symbol:12s} ${risk:8,.2f} ({risk_pct:.2f}%)")

        print("=" * 70 + "\n")
