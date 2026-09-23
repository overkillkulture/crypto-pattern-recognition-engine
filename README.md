# Crypto Pattern Recognition Engine

A Python library for detecting technical-analysis patterns in cryptocurrency
OHLCV price data. Experimental / educational project.

## What it does

- Technical indicators: RSI, MACD, Bollinger Bands, Stochastic, VWAP, moving-average
  cross (SMA/EMA), ATR, OBV, ADX, Parabolic SAR.
- Chart patterns: head & shoulders, triangles, double top/bottom, flags, pennants,
  wedges, cup & handle, rectangle, diamond.
- Candlestick patterns: doji, hammer/hanging man, engulfing, morning/evening star,
  three soldiers/crows, shooting star.
- Combination strategies (consensus / weighted / confirmation voting).
- A paper-trading simulator with position sizing and basic risk metrics
  (Sharpe, Sortino, VaR) and a simple portfolio rebalancer.

## Quick start

```bash
git clone https://github.com/overkillkulture/crypto-pattern-recognition-engine.git
cd crypto-pattern-recognition-engine
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

python examples/demo_patterns_offline.py
```

```python
from src.patterns.optimized import OptimizedRSIPattern

rsi = OptimizedRSIPattern(use_cache=True)
patterns = rsi.detect(your_ohlcv_data)
for p in patterns:
    print(p.pattern_name, p.signal, round(p.confidence, 2))
```

See `examples/` for the trading simulator, multi-strategy backtest, and portfolio demos.

## Status

Early-stage and not actively maintained. Indicators, chart/candlestick patterns, the
paper-trading simulator, and the benchmark suite are implemented. Live data feeds,
exchange connectors, and ML classification are not.

## Disclaimer

For educational and research purposes only. This is not financial advice. Cryptocurrency
trading carries significant risk; test thoroughly and do your own research before risking
capital.

## License

MIT License - see the [LICENSE](LICENSE) file.
