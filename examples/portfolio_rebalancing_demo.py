"""
Portfolio Rebalancing Demo

Demonstrates multi-asset portfolio management with automatic rebalancing:
- 3 assets: BTC/USDT (50%), ETH/USDT (30%), SOL/USDT (20%)
- Monthly rebalancing when drift exceeds threshold
- Performance comparison: Rebalanced vs Buy & Hold each asset
- Rebalancing cost analysis
- Portfolio risk metrics
"""

import asyncio
import sys
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

sys.path.insert(0, '/home/user/crypto-pattern-recognition-engine')

from src.trading.simulator import TradingSimulator, OrderSide
from src.trading.portfolio import Portfolio
from src.core.types import OHLCV


def generate_multi_asset_data(days=180, symbols=None):
    """
    Generate synthetic price data for multiple assets with different characteristics.

    Returns dict of symbol -> OHLCV
    """
    if symbols is None:
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    periods = days * 24  # Hourly data
    timestamps = np.array([
        (datetime.now() - timedelta(hours=periods-i)).timestamp()
        for i in range(periods)
    ])

    asset_data = {}

    # BTC: Lower volatility, steady growth
    btc_drift = 0.00015  # ~0.36% daily
    btc_vol = 0.0015     # ~3.6% daily volatility
    btc_returns = btc_drift + np.random.randn(periods) * btc_vol
    btc_prices = 50000 * np.cumprod(1 + btc_returns)

    asset_data["BTC/USDT"] = create_ohlcv(timestamps, btc_prices)

    # ETH: Medium volatility, higher growth
    eth_drift = 0.00020  # ~0.48% daily
    eth_vol = 0.0020     # ~4.8% daily volatility
    eth_returns = eth_drift + np.random.randn(periods) * eth_vol
    eth_prices = 3000 * np.cumprod(1 + eth_returns)

    asset_data["ETH/USDT"] = create_ohlcv(timestamps, eth_prices)

    # SOL: High volatility, highest growth potential
    sol_drift = 0.00025  # ~0.6% daily
    sol_vol = 0.0030     # ~7.2% daily volatility
    sol_returns = sol_drift + np.random.randn(periods) * sol_vol
    sol_prices = 100 * np.cumprod(1 + sol_returns)

    asset_data["SOL/USDT"] = create_ohlcv(timestamps, sol_prices)

    return asset_data


def create_ohlcv(timestamps, prices):
    """Create OHLCV from timestamps and close prices."""
    periods = len(prices)

    closes = prices
    opens = np.roll(closes, 1)
    opens[0] = closes[0]

    highs = np.maximum(opens, closes) * (1 + np.abs(np.random.randn(periods)) * 0.005)
    lows = np.minimum(opens, closes) * (1 - np.abs(np.random.randn(periods)) * 0.005)
    volumes = np.random.lognormal(20, 1, periods) * 100

    return OHLCV(
        timestamps=timestamps,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        volume=volumes,
    )


async def run_portfolio_demo():
    """Run portfolio rebalancing demonstration."""

    print("\n" + "="*80)
    print("📊 PORTFOLIO REBALANCING DEMONSTRATION")
    print("="*80 + "\n")

    # Configuration
    initial_capital = 100000
    rebalance_days = 30  # Monthly rebalancing
    rebalance_threshold = 5.0  # Rebalance if drift > 5%

    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    target_allocation = {
        "BTC/USDT": 50.0,  # 50%
        "ETH/USDT": 30.0,  # 30%
        "SOL/USDT": 20.0,  # 20%
    }

    # Generate market data
    print("📈 Generating market data (180 days, 3 assets)...")
    asset_data = generate_multi_asset_data(days=180, symbols=symbols)

    for symbol in symbols:
        data = asset_data[symbol]
        start_price = data.close[0]
        end_price = data.close[-1]
        return_pct = ((end_price / start_price) - 1) * 100
        print(f"  {symbol:12s} ${start_price:>8,.2f} → ${end_price:>8,.2f} ({return_pct:>+7.1f}%)")

    print()

    # Setup portfolio with rebalancing
    print("Portfolio Configuration:")
    print(f"  Initial Capital: ${initial_capital:,}")
    print(f"  Rebalancing: Every {rebalance_days} days (if drift > {rebalance_threshold}%)")
    print(f"  Target Allocation:")
    for symbol, pct in target_allocation.items():
        print(f"    {symbol:12s} {pct:>5.1f}%")
    print()

    # Initialize rebalanced portfolio
    rebalanced_sim = TradingSimulator(
        initial_capital=initial_capital,
        fee_rate=0.001,
        slippage_pct=0.05,
    )
    rebalanced_portfolio = Portfolio(rebalanced_sim)
    rebalanced_portfolio.set_target_allocation(target_allocation)
    rebalanced_portfolio.rebalance_threshold = rebalance_threshold

    # Initialize buy & hold portfolios (one per asset)
    buyhold_sims = {}
    for symbol in symbols:
        sim = TradingSimulator(
            initial_capital=initial_capital / len(symbols),  # Split equally
            fee_rate=0.001,
            slippage_pct=0.05,
        )
        buyhold_sims[symbol] = sim

    print("="*80)
    print("RUNNING SIMULATION...")
    print("="*80 + "\n")

    # Track rebalancing events
    rebalance_events = []
    last_rebalance_idx = 0

    # Simulation
    periods = len(asset_data["BTC/USDT"].close)

    for i in range(1, periods):
        # Get current prices
        current_prices = {
            symbol: asset_data[symbol].close[i]
            for symbol in symbols
        }

        # Update rebalanced portfolio
        rebalanced_sim.update_prices(current_prices)

        # Initial purchase (day 1)
        if i == 1:
            rebalanced_portfolio.rebalance(current_prices)

            # Buy & hold initial purchases
            for symbol in symbols:
                initial_amount = initial_capital / len(symbols)
                price = current_prices[symbol]
                quantity = (initial_amount * 0.998) / (price * 1.002)  # Account for fees
                buyhold_sims[symbol].market_order(symbol, OrderSide.BUY, quantity, price)

            print(f"📅 Day 1: Initial allocation")
            print(f"   Portfolio value: ${rebalanced_portfolio.simulator.get_equity():,.2f}\n")

        # Check for rebalancing (monthly)
        hours_since_rebalance = (i - last_rebalance_idx)
        days_since_rebalance = hours_since_rebalance / 24

        if days_since_rebalance >= rebalance_days:
            if rebalanced_portfolio.needs_rebalancing():
                # Execute rebalance
                trades = rebalanced_portfolio.rebalance(current_prices)

                current_day = i // 24
                rebalance_events.append({
                    'day': current_day,
                    'equity': rebalanced_portfolio.simulator.get_equity(),
                    'trades': len(trades),
                })

                print(f"🔄 Day {current_day}: Rebalancing triggered")
                print(f"   Executed {len(trades)} trades")
                print(f"   Portfolio value: ${rebalanced_portfolio.simulator.get_equity():,.2f}")

                # Show drift
                current_alloc = rebalanced_portfolio.get_current_allocation()
                max_drift = 0
                for symbol in symbols:
                    target = target_allocation[symbol]
                    current = current_alloc.get(symbol, 0)
                    drift = abs(current - target)
                    if drift > max_drift:
                        max_drift = drift

                print(f"   Max drift before rebalance: {max_drift:.1f}%\n")

                last_rebalance_idx = i

        # Update buy & hold portfolios
        for symbol in symbols:
            buyhold_sims[symbol].update_prices({symbol: current_prices[symbol]})

    # Final results
    print("\n" + "="*80)
    print("SIMULATION RESULTS")
    print("="*80 + "\n")

    # Rebalanced portfolio stats
    rebalanced_equity = rebalanced_portfolio.simulator.get_equity()
    rebalanced_return = ((rebalanced_equity - initial_capital) / initial_capital) * 100

    print(f"📊 Rebalanced Portfolio")
    print(f"  Final Equity: ${rebalanced_equity:,.2f}")
    print(f"  Total Return: {rebalanced_return:+.2f}%")
    print(f"  Total Fees: ${rebalanced_portfolio.simulator.total_fees_paid:,.2f}")
    print(f"  Rebalancing Events: {len(rebalance_events)}")
    print()

    # Current allocation
    final_alloc = rebalanced_portfolio.get_current_allocation()
    print("  Final Allocation:")
    for symbol in symbols:
        current_pct = final_alloc.get(symbol, 0)
        target_pct = target_allocation[symbol]
        drift = current_pct - target_pct
        print(f"    {symbol:12s} {current_pct:>5.1f}% (target: {target_pct:.1f}%, drift: {drift:+.1f}%)")
    print()

    # Buy & hold comparison
    print("📈 Buy & Hold Comparison (Equal Weight)")
    buyhold_total_equity = sum(sim.get_equity() for sim in buyhold_sims.values())
    buyhold_return = ((buyhold_total_equity - initial_capital) / initial_capital) * 100

    print(f"  Final Equity: ${buyhold_total_equity:,.2f}")
    print(f"  Total Return: {buyhold_return:+.2f}%")

    for symbol in symbols:
        equity = buyhold_sims[symbol].get_equity()
        initial = initial_capital / len(symbols)
        ret = ((equity - initial) / initial) * 100
        print(f"    {symbol:12s} ${equity:>10,.2f} ({ret:>+7.1f}%)")
    print()

    # Individual asset returns
    print("💹 Individual Asset Returns (100% allocation)")
    for symbol in symbols:
        data = asset_data[symbol]
        asset_return = ((data.close[-1] / data.close[1]) - 1) * 100
        print(f"  {symbol:12s} {asset_return:>+7.1f}%")
    print()

    # Performance comparison
    print("="*80)
    print("PERFORMANCE ANALYSIS")
    print("="*80 + "\n")

    strategies = [
        ("Rebalanced Portfolio", rebalanced_return, rebalanced_equity),
        ("Buy & Hold (Equal)", buyhold_return, buyhold_total_equity),
    ]

    # Add individual assets
    for symbol in symbols:
        data = asset_data[symbol]
        asset_return = ((data.close[-1] / data.close[1]) - 1) * 100
        asset_final = initial_capital * (1 + asset_return/100)
        strategies.append((f"{symbol} Only", asset_return, asset_final))

    # Sort by return
    strategies.sort(key=lambda x: x[1], reverse=True)

    print(f"{'Strategy':<30} {'Return':>12} {'Final Value':>15}")
    print("-" * 60)

    for rank, (name, ret, equity) in enumerate(strategies, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        print(f"{medal} {name:<27} {ret:>+10.2f}% ${equity:>13,.2f}")

    print()

    # Rebalancing statistics
    if rebalance_events:
        print("="*80)
        print("REBALANCING STATISTICS")
        print("="*80 + "\n")

        print(f"Total Rebalancing Events: {len(rebalance_events)}")
        print(f"Average Days Between Rebalances: {180 / (len(rebalance_events) + 1):.1f}")
        print()

        print("Rebalancing History:")
        for event in rebalance_events:
            print(f"  Day {event['day']:>3}: {event['trades']} trades, "
                  f"Portfolio: ${event['equity']:,.2f}")
        print()

    # Cost analysis
    rebalance_fees = rebalanced_portfolio.simulator.total_fees_paid
    buyhold_fees = sum(sim.total_fees_paid for sim in buyhold_sims.values())

    print("="*80)
    print("COST ANALYSIS")
    print("="*80 + "\n")

    print(f"Transaction Costs:")
    print(f"  Rebalanced Portfolio: ${rebalance_fees:,.2f}")
    print(f"  Buy & Hold: ${buyhold_fees:,.2f}")
    print(f"  Additional Cost: ${rebalance_fees - buyhold_fees:+,.2f}")
    print()

    print(f"Cost as % of Initial Capital:")
    print(f"  Rebalanced: {(rebalance_fees / initial_capital) * 100:.3f}%")
    print(f"  Buy & Hold: {(buyhold_fees / initial_capital) * 100:.3f}%")
    print()

    # Risk analysis
    print("="*80)
    print("RISK CONSIDERATIONS")
    print("="*80 + "\n")

    print("✅ Benefits of Rebalancing:")
    print("  • Maintains target risk/return profile")
    print("  • Automatically sells high, buys low")
    print("  • Prevents overconcentration in single asset")
    print("  • More consistent with investment objectives")
    print()

    print("⚠️  Costs of Rebalancing:")
    print("  • Transaction fees on each rebalance")
    print("  • Potential tax implications (realized gains)")
    print("  • May underperform in strong trends")
    print("  • Requires active monitoring")
    print()

    # Recommendations
    print("="*80)
    print("KEY TAKEAWAYS")
    print("="*80 + "\n")

    if rebalanced_return > buyhold_return:
        print("✅ Rebalancing outperformed buy & hold in this scenario")
    else:
        print("⚠️  Buy & hold outperformed rebalancing in this scenario")

    print()
    print("💡 Optimization Opportunities:")
    print("  • Adjust rebalancing frequency (less often = lower costs)")
    print(f"  • Increase drift threshold (current: {rebalance_threshold}%)")
    print("  • Use tax-loss harvesting during rebalancing")
    print("  • Consider volatility-weighted allocation")
    print("  • Implement corridor rebalancing (per-asset thresholds)")
    print()


async def main():
    """Run portfolio rebalancing demo."""
    try:
        await run_portfolio_demo()

        print("\n✅ Simulation complete!")
        print("\n🔬 Experiment with:")
        print("  • Different target allocations (e.g., 60/30/10)")
        print("  • Rebalancing frequency (weekly, quarterly, annually)")
        print("  • Drift thresholds (3%, 10%, 15%)")
        print("  • Adding more assets to the portfolio")
        print("  • Different market conditions (bull vs bear)")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
