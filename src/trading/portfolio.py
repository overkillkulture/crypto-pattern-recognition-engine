"""Portfolio management module."""

from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PortfolioState:
    """Snapshot of portfolio state at a point in time."""

    timestamp: datetime
    total_value: float
    cash: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    num_positions: int
    allocation: Dict[str, float]  # symbol -> % of portfolio


class Portfolio:
    """
    Portfolio management with allocation tracking and rebalancing.

    Provides high-level portfolio management on top of trading simulator.

    Example:
        portfolio = Portfolio(simulator)

        # Set target allocations
        portfolio.set_target_allocation({
            "BTC/USDT": 0.50,  # 50%
            "ETH/USDT": 0.30,  # 30%
            "SOL/USDT": 0.20,  # 20%
        })

        # Rebalance to target
        portfolio.rebalance(current_prices)

        # Get portfolio state
        state = portfolio.get_state()
    """

    def __init__(self, simulator):
        """
        Initialize portfolio.

        Args:
            simulator: TradingSimulator instance
        """
        self.simulator = simulator
        self.target_allocation: Dict[str, float] = {}
        self.history: List[PortfolioState] = []

        # Risk parameters
        self.max_position_size_pct = 25.0  # Max 25% in single position
        self.rebalance_threshold = 5.0  # Rebalance if off by 5%+

    def set_target_allocation(self, allocations: Dict[str, float]):
        """
        Set target portfolio allocations.

        Args:
            allocations: Dictionary of symbol -> target % (0-1 or 0-100)

        Example:
            portfolio.set_target_allocation({
                "BTC/USDT": 0.50,
                "ETH/USDT": 0.30,
                "USDC": 0.20,  # Cash reserve
            })
        """
        # Normalize to percentages (0-100)
        total = sum(allocations.values())
        if total > 1.01:  # Already in percentage form
            self.target_allocation = allocations.copy()
        else:  # Convert from decimal to percentage
            self.target_allocation = {k: v * 100 for k, v in allocations.items()}

        # Validate
        total = sum(self.target_allocation.values())
        if abs(total - 100.0) > 0.01:
            logger.warning(f"Target allocation sums to {total}%, adjusting to 100%")
            # Normalize
            factor = 100.0 / total
            self.target_allocation = {k: v * factor for k, v in self.target_allocation.items()}

        logger.info(f"Target allocation set: {self.target_allocation}")

    def get_current_allocation(self) -> Dict[str, float]:
        """
        Get current portfolio allocation percentages.

        Returns:
            Dictionary of symbol -> current % of portfolio
        """
        total_value = self.simulator.get_equity()

        if total_value == 0:
            return {}

        allocations = {}

        # Cash allocation
        cash_pct = (self.simulator.cash / total_value) * 100
        if cash_pct > 0.01:
            allocations["CASH"] = cash_pct

        # Position allocations
        for symbol, position in self.simulator.positions.items():
            position_value = position.quantity * position.current_price
            allocations[symbol] = (position_value / total_value) * 100

        return allocations

    def needs_rebalancing(self) -> bool:
        """
        Check if portfolio needs rebalancing based on threshold.

        Returns:
            True if any position is off target by more than threshold
        """
        if not self.target_allocation:
            return False

        current = self.get_current_allocation()

        for symbol, target_pct in self.target_allocation.items():
            current_pct = current.get(symbol, 0.0)
            diff = abs(current_pct - target_pct)

            if diff > self.rebalance_threshold:
                logger.info(f"{symbol}: current {current_pct:.1f}%, target {target_pct:.1f}%, diff {diff:.1f}%")
                return True

        return False

    def rebalance(self, current_prices: Dict[str, float], dry_run: bool = False) -> Dict[str, float]:
        """
        Rebalance portfolio to target allocations.

        Args:
            current_prices: Current market prices for all symbols
            dry_run: If True, only calculate but don't execute trades

        Returns:
            Dictionary of trades to execute (symbol -> quantity change)
        """
        if not self.target_allocation:
            logger.warning("No target allocation set")
            return {}

        total_value = self.simulator.get_equity()
        current_allocation = self.get_current_allocation()

        trades = {}

        # Calculate required trades
        for symbol, target_pct in self.target_allocation.items():
            if symbol == "CASH":
                continue  # Skip cash

            if symbol not in current_prices:
                logger.warning(f"No price data for {symbol}, skipping")
                continue

            current_pct = current_allocation.get(symbol, 0.0)
            diff_pct = target_pct - current_pct

            # Calculate target value and quantity
            target_value = (target_pct / 100) * total_value
            current_position = self.simulator.get_position(symbol)
            current_quantity = current_position.quantity if current_position else 0.0

            target_quantity = target_value / current_prices[symbol]
            quantity_diff = target_quantity - current_quantity

            # Only trade if significant difference
            if abs(quantity_diff) > 0.0001:  # Minimum trade size
                trades[symbol] = quantity_diff

                logger.info(
                    f"{symbol}: {current_pct:.1f}% -> {target_pct:.1f}% "
                    f"({quantity_diff:+.4f} units @ ${current_prices[symbol]:.2f})"
                )

        if dry_run:
            return trades

        # Execute trades
        for symbol, quantity_diff in trades.items():
            if quantity_diff > 0:
                # Buy
                self.simulator.market_order(
                    symbol,
                    self.simulator.OrderSide.BUY,
                    abs(quantity_diff),
                    current_prices[symbol]
                )
            else:
                # Sell
                self.simulator.market_order(
                    symbol,
                    self.simulator.OrderSide.SELL,
                    abs(quantity_diff),
                    current_prices[symbol]
                )

        return trades

    def get_state(self) -> PortfolioState:
        """
        Get current portfolio state snapshot.

        Returns:
            PortfolioState with current metrics
        """
        total_value = self.simulator.get_equity()
        positions_value = self.simulator.get_total_position_value()

        unrealized_pnl = sum(p.unrealized_pnl for p in self.simulator.positions.values())

        state = PortfolioState(
            timestamp=datetime.utcnow(),
            total_value=total_value,
            cash=self.simulator.cash,
            positions_value=positions_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=self.simulator.total_realized_pnl,
            num_positions=len(self.simulator.positions),
            allocation=self.get_current_allocation(),
        )

        self.history.append(state)
        return state

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Calculate portfolio performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        stats = self.simulator.get_statistics()

        # Add portfolio-specific metrics
        if len(self.history) > 1:
            # Calculate volatility from historical values
            values = [state.total_value for state in self.history]
            returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]

            import numpy as np
            volatility = np.std(returns) * np.sqrt(252) * 100 if returns else 0.0

            # Calculate Sharpe ratio (assuming 0% risk-free rate)
            avg_return = np.mean(returns) if returns else 0.0
            sharpe = (avg_return / (np.std(returns) + 1e-9)) * np.sqrt(252) if returns else 0.0
        else:
            volatility = 0.0
            sharpe = 0.0

        return {
            **stats,
            'volatility_pct': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': self._calculate_max_drawdown(),
        }

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from portfolio history."""
        if len(self.history) < 2:
            return 0.0

        values = [state.total_value for state in self.history]
        peak = values[0]
        max_dd = 0.0

        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def check_risk_limits(self) -> List[str]:
        """
        Check if portfolio violates any risk limits.

        Returns:
            List of warning messages
        """
        warnings = []

        current_allocation = self.get_current_allocation()

        # Check position size limits
        for symbol, pct in current_allocation.items():
            if symbol == "CASH":
                continue

            if pct > self.max_position_size_pct:
                warnings.append(
                    f"{symbol} position {pct:.1f}% exceeds limit of {self.max_position_size_pct}%"
                )

        # Check margin usage
        if self.simulator.enable_margin:
            equity = self.simulator.get_equity()
            position_value = self.simulator.get_total_position_value()
            leverage = position_value / equity if equity > 0 else 0

            if leverage > self.simulator.margin_multiplier:
                warnings.append(f"Leverage {leverage:.1f}x exceeds limit {self.simulator.margin_multiplier}x")

        return warnings

    def optimize_allocation(
        self,
        symbols: List[str],
        historical_returns: Dict[str, List[float]],
        risk_free_rate: float = 0.0,
    ) -> Dict[str, float]:
        """
        Calculate optimal portfolio allocation using mean-variance optimization.

        Args:
            symbols: List of symbols to include
            historical_returns: Dictionary of symbol -> list of historical returns
            risk_free_rate: Risk-free rate for Sharpe ratio calculation

        Returns:
            Dictionary of optimal allocations
        """
        import numpy as np

        # Simple equal-weight allocation as baseline
        # In production, use more sophisticated optimization (e.g., scipy.optimize)
        n = len(symbols)
        return {symbol: 100.0 / n for symbol in symbols}

    def print_summary(self):
        """Print portfolio summary."""
        state = self.get_state()
        metrics = self.get_performance_metrics()

        print("\n" + "="*70)
        print("PORTFOLIO SUMMARY")
        print("="*70)
        print(f"Total Value: ${state.total_value:,.2f}")
        print(f"Cash: ${state.cash:,.2f}")
        print(f"Positions Value: ${state.positions_value:,.2f}")
        print(f"Unrealized P&L: ${state.unrealized_pnl:+,.2f}")
        print(f"Realized P&L: ${state.realized_pnl:+,.2f}")
        print(f"Total Return: {metrics['total_return_pct']:+.2f}%")
        print(f"\nOpen Positions: {state.num_positions}")

        if state.allocation:
            print(f"\nCurrent Allocation:")
            for symbol, pct in sorted(state.allocation.items(), key=lambda x: x[1], reverse=True):
                print(f"  {symbol:12s} {pct:6.2f}%")

        if self.target_allocation:
            print(f"\nTarget Allocation:")
            for symbol, pct in sorted(self.target_allocation.items(), key=lambda x: x[1], reverse=True):
                print(f"  {symbol:12s} {pct:6.2f}%")

        print(f"\nPerformance:")
        print(f"  Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
        print(f"  Total Fees: ${metrics['total_fees']:.2f}")
        print("="*70 + "\n")

        # Check risk limits
        warnings = self.check_risk_limits()
        if warnings:
            print("⚠️  RISK WARNINGS:")
            for warning in warnings:
                print(f"  • {warning}")
            print()
