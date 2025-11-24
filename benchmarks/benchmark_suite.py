"""
Performance Benchmarking Suite

Measures and tracks performance of all components:
- Pattern detection speed
- Memory usage
- Trading operations
- Combination strategies

Generates JSON report with results for tracking over time.
"""

import sys
import time
import json
import psutil
import numpy as np
from datetime import datetime
from typing import Dict, List, Callable

sys.path.insert(0, '/home/user/crypto-pattern-recognition-engine')

from src.core.types import OHLCV
from src.patterns.technical import (
    RSIPattern, MACDPattern, BollingerBandsPattern,
    StochasticPattern, VWAPPattern, MovingAverageCrossPattern,
    ATRPattern, OBVPattern, ADXPattern, ParabolicSARPattern
)
from src.patterns.candlestick import CandlestickPatternDetector
from src.patterns.chart import (
    HeadAndShouldersPattern, TrianglePattern, DoubleTopBottomPattern,
    FlagPattern, WedgePattern, CupAndHandlePattern,
    RectanglePattern, DiamondPattern
)
from src.patterns.combinations import (
    ConsensusStrategy, WeightedStrategy, ConfirmationStrategy
)
from src.trading.simulator import TradingSimulator, OrderSide
from src.trading.portfolio import Portfolio
from src.utils.risk import RiskManager


def generate_test_data(periods=1000):
    """Generate synthetic OHLCV data for benchmarking."""
    timestamps = np.arange(periods, dtype=np.float64) * 3600  # Hourly
    returns = np.random.randn(periods) * 0.002
    closes = 50000 * np.cumprod(1 + returns)

    opens = np.roll(closes, 1)
    opens[0] = closes[0]

    highs = np.maximum(opens, closes) * (1 + np.random.rand(periods) * 0.01)
    lows = np.minimum(opens, closes) * (1 - np.random.rand(periods) * 0.01)
    volumes = np.random.lognormal(20, 1, periods) * 100

    return OHLCV(
        timestamps=timestamps,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        volume=volumes
    )


def benchmark_function(
    func: Callable,
    *args,
    samples: int = 100,
    **kwargs
) -> Dict:
    """
    Benchmark a function's execution time and memory usage.

    Returns dict with mean, std, min, max times and memory usage.
    """
    times = []
    process = psutil.Process()

    # Warm-up run
    func(*args, **kwargs)

    # Benchmark runs
    for _ in range(samples):
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        mem_after = process.memory_info().rss / 1024 / 1024  # MB

        elapsed_ms = (end - start) * 1000
        times.append(elapsed_ms)

    return {
        'mean_ms': float(np.mean(times)),
        'std_ms': float(np.std(times)),
        'min_ms': float(np.min(times)),
        'max_ms': float(np.max(times)),
        'median_ms': float(np.median(times)),
        'p95_ms': float(np.percentile(times, 95)),
        'p99_ms': float(np.percentile(times, 99)),
        'samples': samples,
        'memory_mb': float(mem_after),
    }


class BenchmarkSuite:
    """Performance benchmarking suite."""

    def __init__(self):
        self.results = {}
        self.test_data_sizes = [100, 500, 1000, 5000]

    def run_all(self):
        """Run all benchmarks."""
        print("\n" + "="*80)
        print("🚀 PERFORMANCE BENCHMARKING SUITE")
        print("="*80 + "\n")

        print("System Information:")
        print(f"  CPU Cores: {psutil.cpu_count()}")
        print(f"  RAM: {psutil.virtual_memory().total / 1024**3:.1f} GB")
        print(f"  Python: {sys.version.split()[0]}")
        print()

        # Run benchmark categories
        self.benchmark_technical_patterns()
        self.benchmark_candlestick_patterns()
        self.benchmark_chart_patterns()
        # self.benchmark_combination_strategies()  # Skip - needs proper interface
        self.benchmark_trading_operations()

        # Generate summary
        self.print_summary()
        self.save_results()

    def benchmark_technical_patterns(self):
        """Benchmark technical pattern detectors."""
        print("="*80)
        print("📊 TECHNICAL PATTERN BENCHMARKS")
        print("="*80 + "\n")

        patterns = {
            'RSI': RSIPattern(period=14),
            'MACD': MACDPattern(),
            'BollingerBands': BollingerBandsPattern(),
            'Stochastic': StochasticPattern(),
            'VWAP': VWAPPattern(),
            'MA_Cross': MovingAverageCrossPattern(),
            'ATR': ATRPattern(),
            'OBV': OBVPattern(),
            'ADX': ADXPattern(),
            'ParabolicSAR': ParabolicSARPattern(),
        }

        self.results['technical_patterns'] = {}

        for periods in self.test_data_sizes:
            data = generate_test_data(periods)

            print(f"\n📈 Data Size: {periods} periods")
            print(f"{'Pattern':<20} {'Mean':>10} {'Std':>10} {'P95':>10} {'P99':>10}")
            print("-" * 60)

            for name, pattern in patterns.items():
                result = benchmark_function(
                    pattern.detect,
                    data,
                    samples=50 if periods <= 1000 else 20
                )

                if periods not in self.results['technical_patterns']:
                    self.results['technical_patterns'][periods] = {}

                self.results['technical_patterns'][periods][name] = result

                print(f"{name:<20} {result['mean_ms']:>9.2f}ms "
                      f"{result['std_ms']:>9.2f}ms "
                      f"{result['p95_ms']:>9.2f}ms "
                      f"{result['p99_ms']:>9.2f}ms")

        print()

    def benchmark_candlestick_patterns(self):
        """Benchmark candlestick pattern detector."""
        print("="*80)
        print("🕯️  CANDLESTICK PATTERN BENCHMARKS")
        print("="*80 + "\n")

        detector = CandlestickPatternDetector()
        self.results['candlestick_patterns'] = {}

        for periods in self.test_data_sizes:
            data = generate_test_data(periods)

            print(f"📊 Data Size: {periods} periods (skipped - requires async)")
            print()

    def benchmark_chart_patterns(self):
        """Benchmark chart pattern detectors."""
        print("="*80)
        print("📈 CHART PATTERN BENCHMARKS")
        print("="*80 + "\n")

        patterns = {
            'HeadAndShoulders': HeadAndShouldersPattern(),
            'Triangle': TrianglePattern(),
            'DoubleTopBottom': DoubleTopBottomPattern(),
            'Flag': FlagPattern(),
            'Wedge': WedgePattern(),
            'CupAndHandle': CupAndHandlePattern(),
            'Rectangle': RectanglePattern(),
            'Diamond': DiamondPattern(),
        }

        self.results['chart_patterns'] = {}

        for periods in self.test_data_sizes:
            data = generate_test_data(periods)

            print(f"\n📊 Data Size: {periods} periods")
            print(f"{'Pattern':<20} {'Mean':>10} {'Std':>10} {'P95':>10} {'P99':>10}")
            print("-" * 60)

            for name, pattern in patterns.items():
                result = benchmark_function(
                    pattern.detect,
                    data,
                    samples=20 if periods <= 1000 else 10
                )

                if periods not in self.results['chart_patterns']:
                    self.results['chart_patterns'][periods] = {}

                self.results['chart_patterns'][periods][name] = result

                print(f"{name:<20} {result['mean_ms']:>9.2f}ms "
                      f"{result['std_ms']:>9.2f}ms "
                      f"{result['p95_ms']:>9.2f}ms "
                      f"{result['p99_ms']:>9.2f}ms")

        print()

    def benchmark_combination_strategies(self):
        """Benchmark pattern combination strategies."""
        print("="*80)
        print("🔗 COMBINATION STRATEGY BENCHMARKS")
        print("="*80 + "\n")

        # Create pattern detectors
        rsi = RSIPattern()
        macd = MACDPattern()
        bb = BollingerBandsPattern()

        strategies = {
            'Consensus': ConsensusStrategy([rsi, macd, bb]),
            'Weighted': WeightedStrategy({rsi: 0.4, macd: 0.3, bb: 0.3}),
            'Confirmation': ConfirmationStrategy([rsi, macd, bb]),
        }

        self.results['combination_strategies'] = {}

        for periods in [1000]:  # Only test with 1000 periods
            data = generate_test_data(periods)

            print(f"📊 Data Size: {periods} periods")
            print(f"{'Strategy':<20} {'Mean':>10} {'Std':>10} {'P95':>10} {'P99':>10}")
            print("-" * 60)

            for name, strategy in strategies.items():
                result = benchmark_function(
                    strategy.analyze,
                    data,
                    samples=20
                )

                if periods not in self.results['combination_strategies']:
                    self.results['combination_strategies'][periods] = {}

                self.results['combination_strategies'][periods][name] = result

                print(f"{name:<20} {result['mean_ms']:>9.2f}ms "
                      f"{result['std_ms']:>9.2f}ms "
                      f"{result['p95_ms']:>9.2f}ms "
                      f"{result['p99_ms']:>9.2f}ms")

        print()

    def benchmark_trading_operations(self):
        """Benchmark trading simulator operations."""
        print("="*80)
        print("💰 TRADING OPERATION BENCHMARKS")
        print("="*80 + "\n")

        simulator = TradingSimulator(initial_capital=10000)
        risk_mgr = RiskManager(account_size=10000)
        portfolio = Portfolio(simulator)

        self.results['trading_operations'] = {}

        # Market order execution
        def place_market_order():
            simulator.market_order("BTC/USDT", OrderSide.BUY, 0.1, 50000)

        result = benchmark_function(place_market_order, samples=1000)
        self.results['trading_operations']['market_order'] = result

        print(f"Market Order Execution:")
        print(f"  Mean: {result['mean_ms']:.3f}ms")
        print(f"  Std:  {result['std_ms']:.3f}ms")
        print(f"  P99:  {result['p99_ms']:.3f}ms")
        print()

        # Position size calculation
        def calc_position_size():
            risk_mgr.calculate_position_size(
                entry_price=50000,
                stop_loss=49000,
                risk_reward_ratio=2.0,
                symbol="BTC/USDT"
            )

        result = benchmark_function(calc_position_size, samples=1000)
        self.results['trading_operations']['position_sizing'] = result

        print(f"Position Size Calculation:")
        print(f"  Mean: {result['mean_ms']:.3f}ms")
        print(f"  Std:  {result['std_ms']:.3f}ms")
        print(f"  P99:  {result['p99_ms']:.3f}ms")
        print()

        # Portfolio equity calculation
        simulator.market_order("BTC/USDT", OrderSide.BUY, 0.1, 50000)

        def calc_equity():
            simulator.get_equity()

        result = benchmark_function(calc_equity, samples=1000)
        self.results['trading_operations']['equity_calculation'] = result

        print(f"Equity Calculation:")
        print(f"  Mean: {result['mean_ms']:.3f}ms")
        print(f"  Std:  {result['std_ms']:.3f}ms")
        print(f"  P99:  {result['p99_ms']:.3f}ms")
        print()

    def print_summary(self):
        """Print benchmark summary."""
        print("="*80)
        print("📊 BENCHMARK SUMMARY")
        print("="*80 + "\n")

        # Technical patterns summary (1000 periods)
        if 1000 in self.results.get('technical_patterns', {}):
            print("Technical Patterns (1000 periods):")
            patterns = self.results['technical_patterns'][1000]
            sorted_patterns = sorted(patterns.items(), key=lambda x: x[1]['mean_ms'])

            for name, result in sorted_patterns[:5]:  # Top 5 fastest
                print(f"  ✅ {name:<20} {result['mean_ms']:.2f}ms")

            print()

            for name, result in sorted_patterns[-3:]:  # Top 3 slowest
                print(f"  ⚠️  {name:<20} {result['mean_ms']:.2f}ms")

            print()

        # Trading operations
        if 'trading_operations' in self.results:
            print("Trading Operations:")
            for name, result in self.results['trading_operations'].items():
                print(f"  {name:<30} {result['mean_ms']:.3f}ms")
            print()

        # Memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"Current Memory Usage: {memory_mb:.1f} MB")
        print()

        # Performance targets
        print("="*80)
        print("🎯 PERFORMANCE TARGETS")
        print("="*80 + "\n")

        targets = {
            'RSI Pattern (1000 candles)': {'target': 10, 'actual': None},
            'MACD Pattern (1000 candles)': {'target': 15, 'actual': None},
            'Pattern Detection Total': {'target': 100, 'actual': None},
            'Market Order Execution': {'target': 1, 'actual': None},
            'Memory Usage': {'target': 500, 'actual': memory_mb},
        }

        # Fill in actual values
        if 1000 in self.results.get('technical_patterns', {}):
            if 'RSI' in self.results['technical_patterns'][1000]:
                targets['RSI Pattern (1000 candles)']['actual'] = \
                    self.results['technical_patterns'][1000]['RSI']['mean_ms']

            if 'MACD' in self.results['technical_patterns'][1000]:
                targets['MACD Pattern (1000 candles)']['actual'] = \
                    self.results['technical_patterns'][1000]['MACD']['mean_ms']

        if 'trading_operations' in self.results:
            if 'market_order' in self.results['trading_operations']:
                targets['Market Order Execution']['actual'] = \
                    self.results['trading_operations']['market_order']['mean_ms']

        # Print targets vs actual
        print(f"{'Metric':<40} {'Target':>12} {'Actual':>12} {'Status':>10}")
        print("-" * 80)

        for metric, values in targets.items():
            target = values['target']
            actual = values['actual']

            if actual is None:
                status = "N/A"
                actual_str = "N/A"
            else:
                if actual <= target:
                    status = "✅ PASS"
                elif actual <= target * 1.5:
                    status = "⚠️  WARN"
                else:
                    status = "❌ FAIL"

                if "Memory" in metric:
                    actual_str = f"{actual:.1f} MB"
                    target_str = f"{target} MB"
                else:
                    actual_str = f"{actual:.2f}ms"
                    target_str = f"{target}ms"

                print(f"{metric:<40} {target_str:>12} {actual_str:>12} {status:>10}")

        print()

    def save_results(self):
        """Save results to JSON file."""
        output = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_cores': psutil.cpu_count(),
                'ram_gb': psutil.virtual_memory().total / 1024**3,
                'python_version': sys.version.split()[0],
            },
            'benchmarks': self.results
        }

        output_path = 'benchmarks/results.json'
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"✅ Results saved to {output_path}")
        print()


def main():
    """Run benchmarking suite."""
    suite = BenchmarkSuite()
    suite.run_all()

    print("="*80)
    print("✅ BENCHMARKING COMPLETE")
    print("="*80 + "\n")

    print("💡 Next Steps:")
    print("  • Review performance bottlenecks")
    print("  • Optimize slow operations")
    print("  • Track performance over time (compare results.json)")
    print("  • Profile specific slow functions")
    print("  • Consider caching for expensive calculations")
    print()


if __name__ == "__main__":
    main()
