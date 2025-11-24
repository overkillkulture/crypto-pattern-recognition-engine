"""Backtesting performance metrics calculator."""

import numpy as np
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.backtest.engine import BacktestEngine


class BacktestMetrics:
    """Calculate performance metrics for backtest results."""

    @staticmethod
    def calculate(engine: 'BacktestEngine') -> Dict[str, Any]:
        """
        Calculate comprehensive backtest metrics.

        Args:
            engine: Backtest engine with completed run

        Returns:
            Dictionary of performance metrics
        """
        trades = engine.trades
        equity_curve = np.array(engine.equity_curve)
        initial_capital = engine.initial_capital

        if not trades:
            return {
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
            }

        # Basic metrics
        total_return = engine.capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100

        # Trade statistics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]

        num_wins = len(winning_trades)
        num_losses = len(losing_trades)
        win_rate = (num_wins / total_trades) * 100 if total_trades > 0 else 0

        # Average win/loss
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t.pnl) for t in losing_trades]) if losing_trades else 0

        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = sum(abs(t.pnl) for t in losing_trades)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Sharpe ratio
        returns = np.diff(equity_curve) / equity_curve[:-1]
        sharpe_ratio = BacktestMetrics._calculate_sharpe(returns)

        # Maximum drawdown
        max_dd, max_dd_pct = BacktestMetrics._calculate_max_drawdown(equity_curve)

        # Sortino ratio
        sortino_ratio = BacktestMetrics._calculate_sortino(returns)

        # Calmar ratio
        calmar_ratio = (total_return_pct / 100) / (max_dd_pct / 100) if max_dd_pct > 0 else 0

        # Average trade duration
        durations = []
        for trade in trades:
            if trade.entry_time and trade.exit_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 3600  # hours
                durations.append(duration)

        avg_duration_hours = np.mean(durations) if durations else 0

        # Consecutive wins/losses
        max_consec_wins, max_consec_losses = BacktestMetrics._calculate_consecutive_trades(trades)

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)

        return {
            # Returns
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'annualized_return_pct': BacktestMetrics._annualize_return(
                total_return_pct / 100,
                len(equity_curve)
            ) * 100,

            # Trade statistics
            'total_trades': total_trades,
            'winning_trades': num_wins,
            'losing_trades': num_losses,
            'win_rate': win_rate,

            # Win/Loss metrics
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_win_pct': (avg_win / initial_capital * 100) if initial_capital > 0 else 0,
            'avg_loss_pct': (avg_loss / initial_capital * 100) if initial_capital > 0 else 0,
            'largest_win': max([t.pnl for t in trades], default=0),
            'largest_loss': min([t.pnl for t in trades], default=0),

            # Ratios
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,

            # Risk metrics
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd_pct,

            # Other
            'expectancy': expectancy,
            'avg_trade_duration_hours': avg_duration_hours,
            'max_consecutive_wins': max_consec_wins,
            'max_consecutive_losses': max_consec_losses,

            # Fees
            'total_fees': sum(t.fees for t in trades),
        }

    @staticmethod
    def _calculate_sharpe(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - risk_free_rate
        if np.std(returns) == 0:
            return 0.0

        return np.mean(excess_returns) / np.std(returns) * np.sqrt(252)  # Annualized

    @staticmethod
    def _calculate_sortino(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """Calculate Sortino ratio (downside deviation)."""
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - risk_free_rate
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return 0.0

        return np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252)

    @staticmethod
    def _calculate_max_drawdown(equity_curve: np.ndarray) -> tuple:
        """Calculate maximum drawdown in absolute and percentage terms."""
        if len(equity_curve) < 2:
            return 0.0, 0.0

        peak = equity_curve[0]
        max_dd = 0.0
        max_dd_pct = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value

            dd = peak - value
            dd_pct = (dd / peak) * 100 if peak > 0 else 0

            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct

        return max_dd, max_dd_pct

    @staticmethod
    def _calculate_consecutive_trades(trades: list) -> tuple:
        """Calculate maximum consecutive wins and losses."""
        if not trades:
            return 0, 0

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    @staticmethod
    def _annualize_return(total_return: float, periods: int, periods_per_year: int = 365) -> float:
        """Annualize total return."""
        if periods == 0:
            return 0.0

        years = periods / periods_per_year
        if years == 0:
            return 0.0

        return (1 + total_return) ** (1 / years) - 1

    @staticmethod
    def print_summary(metrics: Dict[str, Any]) -> None:
        """Print formatted backtest summary."""
        print("\n" + "=" * 60)
        print("BACKTEST SUMMARY")
        print("=" * 60)

        print(f"\nReturns:")
        print(f"  Total Return: ${metrics['total_return']:.2f} ({metrics['total_return_pct']:.2f}%)")
        print(f"  Annualized Return: {metrics['annualized_return_pct']:.2f}%")

        print(f"\nTrade Statistics:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Winning Trades: {metrics['winning_trades']}")
        print(f"  Losing Trades: {metrics['losing_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.2f}%")

        print(f"\nWin/Loss Metrics:")
        print(f"  Average Win: ${metrics['avg_win']:.2f} ({metrics['avg_win_pct']:.2f}%)")
        print(f"  Average Loss: ${metrics['avg_loss']:.2f} ({metrics['avg_loss_pct']:.2f}%)")
        print(f"  Largest Win: ${metrics['largest_win']:.2f}")
        print(f"  Largest Loss: ${metrics['largest_loss']:.2f}")

        print(f"\nPerformance Ratios:")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        print(f"  Calmar Ratio: {metrics['calmar_ratio']:.2f}")

        print(f"\nRisk Metrics:")
        print(f"  Max Drawdown: ${metrics['max_drawdown']:.2f} ({metrics['max_drawdown_pct']:.2f}%)")
        print(f"  Max Consecutive Wins: {metrics['max_consecutive_wins']}")
        print(f"  Max Consecutive Losses: {metrics['max_consecutive_losses']}")

        print(f"\nOther:")
        print(f"  Expectancy: ${metrics['expectancy']:.2f}")
        print(f"  Avg Trade Duration: {metrics['avg_trade_duration_hours']:.1f} hours")
        print(f"  Total Fees: ${metrics['total_fees']:.2f}")

        print("=" * 60 + "\n")
