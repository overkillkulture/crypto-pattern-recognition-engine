# Examples

This directory contains comprehensive examples demonstrating the features of the Crypto Pattern Recognition Engine.

## Quick Start

All examples use synthetic data and can be run without external API dependencies:

```bash
# Activate virtual environment
source venv/bin/activate

# Run any example
python examples/demo_patterns_offline.py
python examples/trading_simulator_demo.py
python examples/multi_strategy_backtest.py
python examples/portfolio_rebalancing_demo.py
```

---

## 📊 Pattern Detection Examples

### demo_patterns_offline.py

**What it demonstrates:**
- Pattern detection on synthetic market data
- Three market scenarios: uptrend, downtrend, breakout
- Multiple technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Candlestick pattern recognition
- Signal interpretation

**Run time:** ~5 seconds

**Output:**
- Detected patterns for each scenario
- Signal types (BUY, SELL, HOLD)
- Pattern confidence scores
- Market analysis summary

**Example output:**
```
📊 SCENARIO 1: Uptrend Market
  Generated 200 periods

Pattern Detection Results:
  Buy signals: 3
  Sell signals: 0
  Hold signals: 2

Patterns detected:
  • RSI Pattern: BUY (confidence: 0.85)
    RSI Oversold condition at 28.5
  • MACD Pattern: BUY (confidence: 0.90)
    Bullish crossover detected
  • Bollinger Bands: HOLD (confidence: 0.70)
    Price near lower band
```

**Key learnings:**
- How pattern detectors work with OHLCV data
- Interpreting pattern signals
- Understanding pattern confidence
- Comparing different market conditions

---

### demo_combinations.py

**What it demonstrates:**
- Advanced pattern combination strategies
- Consensus voting among multiple patterns
- Weighted pattern scoring
- Confirmation strategies (require N confirmations)
- Metadata and pattern agreement tracking

**Run time:** ~10 seconds

**Output:**
- Combined signal from multiple patterns
- Strategy-specific analysis
- Agreement metrics
- Confidence aggregation

**Example output:**
```
🔗 CONSENSUS STRATEGY
  Final Signal: BUY (confidence: 0.78)

  Contributing patterns:
    ✓ RSI Pattern: BUY (0.85)
    ✓ MACD Pattern: BUY (0.90)
    ✗ Bollinger Bands: HOLD (0.70)

  Consensus: 2/3 patterns agree (66.7%)
```

**Key learnings:**
- Combining multiple indicators reduces false signals
- Different combination strategies for different use cases
- Balancing sensitivity vs specificity

---

## 💹 Trading Simulation Examples

### trading_simulator_demo.py

**What it demonstrates:**
- Paper trading with pattern-based signals
- Risk management integration (2% per trade)
- Position sizing with stop loss/take profit
- Entry logic (requires 2+ buy signals)
- Exit logic (stop loss, take profit, sell signals)
- Performance tracking vs buy & hold

**Run time:** ~10 seconds

**Data:** 30 days of hourly synthetic data (720 periods)

**Output:**
```
📈 PATTERN-BASED TRADING STRATEGY SIMULATION

Strategy Configuration:
  Initial Capital: $10,000
  Risk Per Trade: 2.0%
  Max Portfolio Risk: 10.0%

🟢 BUY at $50,120 (2 signals)
   Quantity: 0.1987
   Stop Loss: $49,118
   Take Profit: $52,125
   Risk: $200.00

🔴 SELL at $50,025 (Sell Signals)
   Entry: $50,120
   P&L: $-18.95 (-0.19%)

BACKTEST RESULTS:
  Final Equity: $9,951.20
  Total Return: -0.49%
  Win Rate: 0.0%
  Benchmark (Buy & Hold): +16.82%
```

**Key learnings:**
- Pattern-based trading with real position sizing
- Risk management prevents catastrophic losses
- Transaction costs impact returns
- Not all strategies work in all market conditions
- Importance of backtesting before live trading

---

### multi_strategy_backtest.py

**What it demonstrates:**
- Side-by-side comparison of multiple strategies
- Strategy performance ranking
- Different trading approaches:
  - RSI Strategy (oversold/overbought)
  - MACD Strategy (crossovers)
  - Bollinger Bands Strategy (breakouts)
  - Combined Strategy (2+ confirmations)
- Performance metrics (Sharpe ratio, win rate, etc.)

**Run time:** ~15 seconds

**Data:** 90 days with 4 market regimes (720 periods)

**Output:**
```
BACKTEST RESULTS

Strategy                       Return       Trades     Win Rate
----------------------------------------------------------------
RSI Strategy                    -28.09%       66        18.2%
MACD Strategy                   -22.43%      178        14.0%
Bollinger Bands Strategy        -31.90%      122        13.1%
Combined Strategy               -31.06%       84        14.3%

Benchmark (Buy & Hold): -1.07%

STRATEGY RANKING:
🥇 #1: MACD Strategy           -22.43%
🥈 #2: RSI Strategy            -28.09%
🥉 #3: Combined Strategy       -31.06%
   #4: Bollinger Bands         -31.90%

💡 Key Insights:
  • Combined strategies tend to be more conservative
  • Single-indicator strategies may overtrade
  • Market regime significantly impacts performance
  • Transaction costs can erode returns
```

**Key learnings:**
- No single strategy works all the time
- Overtrading increases costs
- Combined strategies reduce trades but not always profitable
- Strategy selection depends on market conditions
- Importance of strategy comparison

---

### portfolio_rebalancing_demo.py

**What it demonstrates:**
- Multi-asset portfolio management
- Target allocation (BTC 50%, ETH 30%, SOL 20%)
- Automatic rebalancing (monthly, if drift > 5%)
- Rebalancing cost analysis
- Performance vs buy & hold
- Individual asset comparison

**Run time:** ~20 seconds

**Data:** 180 days, 3 assets with different characteristics

**Output:**
```
PORTFOLIO REBALANCING DEMONSTRATION

📊 Rebalanced Portfolio
  Final Equity: $104,855.50
  Total Return: +4.86%
  Rebalancing Events: 5

📈 Buy & Hold (Equal Weight)
  Final Equity: $126,408.34
  Total Return: +26.41%

💹 Individual Asset Returns:
  BTC/USDT       +68.8%
  ETH/USDT      +168.0%
  SOL/USDT      +143.7%

🔄 Day 30: Rebalancing triggered
   Executed 3 trades
   Max drift before rebalance: 31.1%

COST ANALYSIS:
  Rebalanced Portfolio: $340.20
  Buy & Hold: $99.65
  Additional Cost: $+240.55

✅ Benefits of Rebalancing:
  • Maintains target risk/return profile
  • Automatically sells high, buys low
  • Prevents overconcentration

⚠️  Costs of Rebalancing:
  • Transaction fees
  • May underperform in strong trends
```

**Key learnings:**
- Rebalancing maintains consistent risk exposure
- Rebalancing underperforms in strong trends
- Transaction costs add up with frequent rebalancing
- Drift threshold affects rebalancing frequency
- Trade-off between risk management and returns

---

## ⚙️ Customization

### Modifying Market Data

All examples use `generate_market_data()` functions. Customize:

```python
# Change market characteristics
def generate_market_data(days=30, initial_price=50000):
    # Adjust drift (trend strength)
    trend1 = np.linspace(0, 0.001, periods//2)  # Stronger uptrend

    # Adjust volatility
    volatility = np.random.randn(periods) * 0.005  # More volatile

    # Create different regimes
    # ... customize as needed
```

### Adjusting Strategy Parameters

```python
# RSI thresholds
rsi = RSIPattern(period=14, oversold=25, overbought=75)

# Risk management
risk_mgr = RiskManager(
    account_size=10000,
    risk_per_trade_pct=1.0,  # More conservative (1% vs 2%)
    max_risk_pct=5.0,        # Lower max risk (5% vs 10%)
)

# Rebalancing frequency
rebalance_days = 7  # Weekly instead of monthly
rebalance_threshold = 10.0  # Less frequent (10% drift vs 5%)
```

### Adding Custom Patterns

```python
from src.patterns.technical import CustomPattern

# Create custom pattern detector
class MyCustomPattern(Pattern):
    def detect(self, data: OHLCV) -> List[PatternResult]:
        # Your detection logic
        pass

# Use in strategies
custom = MyCustomPattern()
patterns = custom.detect(data)
```

---

## 🎯 Learning Path

Recommended order for learning:

1. **Start here:** `demo_patterns_offline.py`
   - Understand basic pattern detection
   - Learn about different patterns
   - See how patterns work on different market conditions

2. **Next:** `demo_combinations.py`
   - Learn to combine multiple patterns
   - Understand consensus and confirmation
   - See how to reduce false signals

3. **Then:** `trading_simulator_demo.py`
   - Apply patterns to actual trading
   - Learn about risk management
   - Understand position sizing

4. **Advanced:** `multi_strategy_backtest.py`
   - Compare different strategies
   - Learn about strategy selection
   - Understand performance metrics

5. **Portfolio:** `portfolio_rebalancing_demo.py`
   - Multi-asset management
   - Rebalancing strategies
   - Risk/return trade-offs

---

## 🔬 Experimentation Ideas

### Beginner Level
- Change RSI thresholds (oversold/overbought levels)
- Adjust stop loss percentages (2%, 5%, 10%)
- Modify initial capital amounts
- Try different risk per trade (1%, 2%, 5%)

### Intermediate Level
- Create new pattern combinations
- Implement custom entry/exit rules
- Test different rebalancing frequencies
- Add more assets to portfolios

### Advanced Level
- Implement new pattern detectors
- Create ML-enhanced signal generation
- Optimize strategy parameters
- Build custom risk management systems
- Implement portfolio optimization algorithms

---

## 📈 Performance Considerations

### Runtime
- Pattern detection: <100ms for 1000 periods
- Trading simulation: <1s for 1000 trades
- Portfolio rebalancing: <5s for 180 days

### Memory Usage
- Typical: ~100MB for standard runs
- Large datasets (10k+ periods): ~500MB

### Optimization Tips
- Cache pattern calculations when possible
- Use vectorized NumPy operations
- Limit historical data to what's needed
- Profile slow sections with benchmarks

---

## 🐛 Troubleshooting

### "Insufficient capital" errors
```python
# Ensure position sizing accounts for fees/slippage
max_position_value = current_equity * 0.998  # 0.2% buffer
max_qty = max_position_value / (current_price * 1.002)
actual_quantity = min(desired_quantity, max_qty)
```

### Unrealistic price data
```python
# Use realistic hourly returns (not daily)
hourly_drift = 0.0005  # ~1.2% per day
hourly_vol = 0.002     # ~4.8% per day
returns = hourly_drift + np.random.randn(periods) * hourly_vol
```

### No patterns detected
- Check data size (some patterns need 50+ periods)
- Verify OHLCV data quality
- Adjust pattern sensitivity thresholds
- Try different market conditions

### Import errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 📚 Related Documentation

- [Main README](../README.md) - Project overview
- [API Reference](../docs/API_REFERENCE.md) - Detailed API docs
- [Pattern Library](../docs/PATTERNS.md) - All available patterns
- [Trading Guide](../docs/TRADING.md) - Trading system docs
- [Benchmarks](../benchmarks/README.md) - Performance benchmarks

---

## 💡 Tips

### Best Practices
✅ Always backtest strategies before live use
✅ Use risk management (stop losses, position sizing)
✅ Test on different market conditions
✅ Compare to buy & hold benchmark
✅ Account for transaction costs
✅ Start with small position sizes

### Common Mistakes
❌ Overfitting to historical data
❌ Ignoring transaction costs
❌ Not using stop losses
❌ Risking too much per trade
❌ Not testing different market regimes
❌ Assuming past performance = future results

---

## 🤝 Contributing

Have a cool example idea? Contributions welcome!

1. Create your example following the existing format
2. Add comprehensive comments
3. Include sample output in docstring
4. Update this README
5. Submit a pull request

---

## 📞 Support

- Issues: [GitHub Issues](https://github.com/overkillkulture/crypto-pattern-recognition-engine/issues)
- Discussions: [GitHub Discussions](https://github.com/overkillkulture/crypto-pattern-recognition-engine/discussions)
- Documentation: [Full Docs](../docs/)

---

## ⚖️ Disclaimer

**These examples are for educational purposes only.**

- Not financial advice
- Use at your own risk
- Past performance ≠ future results
- Crypto trading is highly risky
- Always do your own research

---

*Last updated: 2025-11-24*
*Version: 1.0.0*
