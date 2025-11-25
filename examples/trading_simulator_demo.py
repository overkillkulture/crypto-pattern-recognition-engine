"""
Trading Simulator Demo - Paper Trading with Pattern Recognition

Demonstrates:
1. Paper trading with the TradingSimulator
2. Pattern-based entry/exit decisions
3. Risk management integration
4. Portfolio tracking and metrics
5. Performance analysis
"""

import asyncio
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, "/home/user/crypto-pattern-recognition-engine")

from src.core.types import OHLCV, SignalType
from src.patterns.technical import (BollingerBandsPattern, MACDPattern,
                                    RSIPattern)
from src.trading.portfolio import Portfolio
from src.trading.simulator import OrderSide, TradingSimulator
from src.utils.risk import RiskManager


def generate_market_data(days=30, initial_price=50000):
    """Generate synthetic market data with trends."""
    print(f"📊 Generating {days} days of market data...")

    periods = days * 24  # Hourly data
    timestamps = np.array(
        [
            (datetime.now() - timedelta(hours=periods - i)).timestamp()
            for i in range(periods)
        ]
    )

    # Create price movement with trend changes (hourly returns, not daily)
    # First half: uptrend (0.05% per hour avg = ~1.2% per day)
    # Second half: downtrend (-0.025% per hour avg = -0.6% per day)
    trend1 = np.linspace(0, 0.0005, periods // 2)
    trend2 = np.linspace(0.0005, -0.00025, periods - periods // 2)
    trend = np.concatenate([trend1, trend2])

    # Add volatility (0.2% per hour)
    volatility = np.random.randn(periods) * 0.002

    # Create price series
    returns = trend + volatility
    prices = initial_price * np.cumprod(1 + returns)

    # Generate OHLCV
    closes = prices
    opens = np.roll(closes, 1)
    opens[0] = closes[0]

    highs = np.maximum(opens, closes) * (1 + np.abs(np.random.randn(periods)) * 0.01)
    lows = np.minimum(opens, closes) * (1 - np.abs(np.random.randn(periods)) * 0.01)
    volumes = np.random.lognormal(20, 1, periods) * 100

    print(f"✓ Generated {periods} periods")
    print(f"  Price range: ${lows.min():.0f} - ${highs.max():.0f}")
    print(f"  Start: ${closes[0]:.0f}, End: ${closes[-1]:.0f}")
    print(f"  Return: {((closes[-1] / closes[0]) - 1) * 100:+.1f}%\n")

    return OHLCV(
        timestamps=timestamps,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        volume=volumes,
    )


async def run_pattern_trading_strategy():
    """Run a pattern-based trading strategy simulation."""

    print("\n" + "=" * 70)
    print("📈 PATTERN-BASED TRADING STRATEGY SIMULATION")
    print("=" * 70 + "\n")

    # Initialize simulator
    initial_capital = 10000
    simulator = TradingSimulator(
        initial_capital=initial_capital,
        fee_rate=0.001,  # 0.1% fee
        slippage_pct=0.05,  # 0.05% slippage
    )

    # Initialize risk manager
    risk_mgr = RiskManager(
        account_size=initial_capital,
        risk_per_trade_pct=2.0,  # Risk 2% per trade
        max_risk_pct=10.0,  # Max 10% total portfolio risk
    )

    # Initialize portfolio tracker
    portfolio = Portfolio(simulator)

    # Setup pattern detectors
    rsi = RSIPattern(period=14, oversold=30, overbought=70)
    macd = MACDPattern()
    bb = BollingerBandsPattern(period=20, std_dev=2.0)

    print("Strategy Configuration:")
    print(f"  Initial Capital: ${initial_capital:,}")
    print(f"  Risk Per Trade: {risk_mgr.risk_per_trade_pct}%")
    print(f"  Max Portfolio Risk: {risk_mgr.max_risk_pct}%")
    print(f"  Fee Rate: {simulator.fee_rate * 100}%")
    print(f"\n  Pattern Detectors:")
    print(f"    • RSI (oversold/overbought)")
    print(f"    • MACD (crossovers)")
    print(f"    • Bollinger Bands (breakouts)")
    print()

    # Generate market data
    data = generate_market_data(days=30, initial_price=50000)

    symbol = "BTC/USDT"
    current_position = None

    print("=" * 70)
    print("RUNNING BACKTEST")
    print("=" * 70 + "\n")

    # Simulate trading period by period
    for i in range(50, len(data.close)):  # Start after warmup period
        # Get current slice of data
        window_data = OHLCV(
            timestamps=data.timestamps[: i + 1],
            open=data.open[: i + 1],
            high=data.high[: i + 1],
            low=data.low[: i + 1],
            close=data.close[: i + 1],
            volume=data.volume[: i + 1],
        )

        current_price = data.close[i]
        current_time = datetime.fromtimestamp(data.timestamps[i])

        # Update simulator with current prices
        simulator.update_prices({symbol: current_price})

        # Detect patterns
        rsi_patterns = rsi.detect(window_data)
        macd_patterns = macd.detect(window_data)
        bb_patterns = bb.detect(window_data)

        all_patterns = rsi_patterns + macd_patterns + bb_patterns

        # Count signals
        buy_signals = [p for p in all_patterns if p.signal == SignalType.BUY]
        sell_signals = [p for p in all_patterns if p.signal == SignalType.SELL]

        # Trading logic
        if current_position is None and len(buy_signals) >= 2:
            # ENTRY: Multiple buy signals

            # Update risk manager with current equity
            current_equity = simulator.get_equity()
            risk_mgr.account_size = current_equity

            # Calculate position size with risk management
            # Use 2% stop loss
            stop_loss = current_price * 0.98

            position_size = risk_mgr.calculate_position_size(
                entry_price=current_price,
                stop_loss=stop_loss,
                risk_reward_ratio=2.0,
                symbol=symbol,
            )

            if position_size.quantity > 0:
                # Cap position size to available capital (with buffer for fees/slippage)
                max_position_value = current_equity * 0.998  # Reserve 0.2% for fees
                max_qty = max_position_value / (current_price * 1.002)  # 0.2% buffer
                actual_quantity = min(position_size.quantity, max_qty)

                # Place market order
                order = simulator.market_order(
                    symbol,
                    OrderSide.BUY,
                    actual_quantity,
                    current_price,
                )

                if order and order.is_filled:
                    current_position = {
                        "entry_price": current_price,
                        "stop_loss": stop_loss,
                        "take_profit": position_size.take_profit,
                        "quantity": actual_quantity,
                        "entry_time": current_time,
                    }

                    print(
                        f"🟢 BUY at ${current_price:,.0f} ({len(buy_signals)} signals)"
                    )
                    print(f"   Quantity: {actual_quantity:.4f}")
                    print(f"   Stop Loss: ${stop_loss:,.0f}")
                    print(f"   Take Profit: ${position_size.take_profit:,.0f}")
                    print(f"   Risk: ${position_size.risk_amount:.2f}\n")

        elif current_position is not None:
            # EXIT logic: Check stop loss, take profit, or sell signals

            should_exit = False
            exit_reason = ""

            # Stop loss hit
            if current_price <= current_position["stop_loss"]:
                should_exit = True
                exit_reason = "Stop Loss"

            # Take profit hit
            elif (
                current_position["take_profit"]
                and current_price >= current_position["take_profit"]
            ):
                should_exit = True
                exit_reason = "Take Profit"

            # Sell signals
            elif len(sell_signals) >= 2:
                should_exit = True
                exit_reason = "Sell Signals"

            if should_exit:
                # Close position
                order = simulator.market_order(
                    symbol,
                    OrderSide.SELL,
                    current_position["quantity"],
                    current_price,
                )

                if order and order.is_filled:
                    pnl = (
                        current_price - current_position["entry_price"]
                    ) * current_position["quantity"]
                    pnl_pct = (
                        (current_price / current_position["entry_price"]) - 1
                    ) * 100

                    emoji = "🟢" if pnl > 0 else "🔴"
                    print(f"{emoji} SELL at ${current_price:,.0f} ({exit_reason})")
                    print(f"   Entry: ${current_position['entry_price']:,.0f}")
                    print(f"   P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)")
                    print(
                        f"   Hold Time: {(current_time - current_position['entry_time']).days} days\n"
                    )

                    # Clear position
                    risk_mgr.close_position_risk(symbol)
                    current_position = None

    # Close any remaining position
    if current_position is not None:
        final_price = data.close[-1]
        simulator.market_order(
            symbol, OrderSide.SELL, current_position["quantity"], final_price
        )
        print(f"🔵 CLOSE FINAL POSITION at ${final_price:,.0f}\n")

    # Get final statistics
    print("=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70 + "\n")

    stats = simulator.get_statistics()

    print(f"Initial Capital: ${stats['initial_capital']:,.2f}")
    print(f"Final Equity: ${stats['equity']:,.2f}")
    print(f"Total Return: {stats['total_return_pct']:+.2f}%")
    print()

    print(f"Trading Activity:")
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Winning Trades: {stats['winning_trades']}")
    print(f"  Losing Trades: {stats['losing_trades']}")
    print(f"  Win Rate: {stats['win_rate']:.1f}%")
    print()

    print(f"Profit & Loss:")
    print(f"  Realized P&L: ${stats['realized_pnl']:+,.2f}")
    print(f"  Unrealized P&L: ${stats['unrealized_pnl']:+,.2f}")
    print(f"  Total Fees Paid: ${stats['total_fees']:,.2f}")
    print()

    print(f"Risk Management:")
    print(f"  Risk Per Trade: 2.0%")
    print(f"  Max Portfolio Risk: 10.0%")
    print(f"  Remaining Risk Capacity: {risk_mgr.get_remaining_risk_capacity():.2f}%")
    print()

    # Buy & hold comparison
    buy_hold_return = ((data.close[-1] / data.close[50]) - 1) * 100
    print(f"Benchmark (Buy & Hold): {buy_hold_return:+.2f}%")
    outperformance = stats["total_return_pct"] - buy_hold_return
    print(f"Strategy Outperformance: {outperformance:+.2f}%")
    print()

    print("=" * 70)

    if stats["total_return_pct"] > 0:
        print("✅ PROFITABLE STRATEGY")
    else:
        print("❌ UNPROFITABLE STRATEGY")

    if stats["win_rate"] > 50:
        print("✅ POSITIVE WIN RATE")
    else:
        print("⚠️  WIN RATE BELOW 50%")

    if stats["total_return_pct"] > buy_hold_return:
        print("✅ OUTPERFORMED BUY & HOLD")
    else:
        print("⚠️  UNDERPERFORMED BUY & HOLD")

    print("=" * 70 + "\n")


async def main():
    """Run trading simulator demonstrations."""

    print("\n" + "=" * 70)
    print("🚀 TRADING SIMULATOR DEMONSTRATION")
    print("=" * 70)
    print()
    print("This demo shows paper trading with:")
    print("  • Pattern-based entry/exit signals")
    print("  • Risk management (2% per trade, 10% max)")
    print("  • Position sizing with stop loss/take profit")
    print("  • Performance tracking and analysis")
    print()

    try:
        await run_pattern_trading_strategy()

        print("\n💡 Key Takeaways:")
        print("  • Pattern recognition drives trading decisions")
        print("  • Risk management prevents excessive losses")
        print("  • Position sizing optimizes risk/reward")
        print("  • Multiple confirmation signals improve win rate")
        print("  • Paper trading validates strategies risk-free")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
