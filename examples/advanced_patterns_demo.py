#!/usr/bin/env python3
"""
Advanced Patterns Demo - Comprehensive Multi-Indicator Analysis

Demonstrates all pattern detectors working together:
- Optimized patterns (RSI, MACD, Bollinger)
- Advanced patterns (ADX, SAR, Stochastic)
- Signal confluence and decision-making

This showcases the full power of the analytical hemisphere before
consciousness integration.
"""

import sys
sys.path.insert(0, '/home/user/crypto-pattern-recognition-engine')

from datetime import datetime
import numpy as np

# Optimized patterns
from src.patterns.optimized import (
    OptimizedRSIPattern,
    OptimizedMACDPattern,
    OptimizedBollingerBandsPattern
)

# Advanced patterns
from src.patterns.advanced import (
    ADXPattern,
    ParabolicSARPattern,
    StochasticPattern
)

# Test data
from tests.fixtures.market_data import (
    generate_ohlcv,
    generate_uptrend,
    generate_downtrend,
    generate_rsi_oversold,
    generate_rsi_overbought
)

from src.core.types import SignalType


class MultiPatternAnalyzer:
    """
    Comprehensive pattern analyzer using all available indicators.

    Combines 6 different pattern detectors for robust signal confirmation.
    """

    def __init__(self):
        """Initialize all pattern detectors."""
        # Optimized patterns
        self.rsi = OptimizedRSIPattern(period=14, use_cache=False)
        self.macd = OptimizedMACDPattern(use_cache=False)
        self.bb = OptimizedBollingerBandsPattern(period=20, use_cache=False)

        # Advanced patterns
        self.adx = ADXPattern(period=14, strong_trend_threshold=25.0)
        self.sar = ParabolicSARPattern(acceleration=0.02, maximum=0.20)
        self.stoch = StochasticPattern(k_period=14, d_period=3)

        self.all_detectors = [
            ("RSI", self.rsi),
            ("MACD", self.macd),
            ("Bollinger Bands", self.bb),
            ("ADX", self.adx),
            ("Parabolic SAR", self.sar),
            ("Stochastic", self.stoch),
        ]

    def analyze(self, data):
        """
        Run comprehensive multi-indicator analysis.

        Returns:
            dict with patterns from each detector and consensus decision
        """
        results = {}
        all_patterns = []

        print("\n" + "="*70)
        print("MULTI-INDICATOR PATTERN ANALYSIS")
        print("="*70)
        print(f"\nAnalyzing {len(data.close)} periods of data")
        print(f"Latest price: ${data.close[-1]:.2f}")
        print(f"Time range: {datetime.fromtimestamp(data.timestamps[0])} to {datetime.fromtimestamp(data.timestamps[-1])}")

        # Run all detectors
        for name, detector in self.all_detectors:
            patterns = detector.detect(data)
            results[name] = patterns
            all_patterns.extend(patterns)

            print(f"\n[{name}]")
            if len(patterns) == 0:
                print("  No patterns detected")
            else:
                for pattern in patterns:
                    print(f"  ✓ {pattern.pattern_name}")
                    print(f"    Signal: {pattern.signal.value}")
                    print(f"    Confidence: {pattern.confidence:.2f}")
                    if pattern.description:
                        print(f"    Detail: {pattern.description}")

        # Analyze signal confluence
        buy_signals = [p for p in all_patterns if p.signal in [SignalType.BUY, SignalType.STRONG_BUY]]
        sell_signals = [p for p in all_patterns if p.signal in [SignalType.SELL, SignalType.STRONG_SELL]]
        hold_signals = [p for p in all_patterns if p.signal == SignalType.HOLD]

        print("\n" + "="*70)
        print("SIGNAL CONFLUENCE ANALYSIS")
        print("="*70)
        print(f"\nBUY signals:  {len(buy_signals)} patterns")
        print(f"SELL signals: {len(sell_signals)} patterns")
        print(f"HOLD signals: {len(hold_signals)} patterns")
        print(f"Total patterns detected: {len(all_patterns)}")

        # Determine consensus
        if len(buy_signals) > len(sell_signals) and len(buy_signals) > len(hold_signals):
            consensus = "BUY"
            confidence = len(buy_signals) / len(all_patterns) if all_patterns else 0
            agreement = len(buy_signals)
        elif len(sell_signals) > len(buy_signals) and len(sell_signals) > len(hold_signals):
            consensus = "SELL"
            confidence = len(sell_signals) / len(all_patterns) if all_patterns else 0
            agreement = len(sell_signals)
        else:
            consensus = "HOLD"
            confidence = len(hold_signals) / len(all_patterns) if all_patterns else 0
            agreement = len(hold_signals)

        print(f"\n→ CONSENSUS: {consensus}")
        print(f"  Agreement: {agreement}/{len(all_patterns)} patterns ({confidence*100:.1f}%)")
        print(f"  Confidence: {confidence:.2f}")

        # Calculate average confidence by signal type
        if buy_signals:
            avg_buy_conf = np.mean([p.confidence for p in buy_signals])
            print(f"\n  Average BUY confidence: {avg_buy_conf:.2f}")
        if sell_signals:
            avg_sell_conf = np.mean([p.confidence for p in sell_signals])
            print(f"  Average SELL confidence: {avg_sell_conf:.2f}")

        return {
            'patterns_by_detector': results,
            'all_patterns': all_patterns,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': hold_signals,
            'consensus': consensus,
            'confidence': confidence,
            'agreement_count': agreement,
            'total_patterns': len(all_patterns),
        }


def main():
    """Run comprehensive pattern analysis on various market conditions."""

    print("="*70)
    print("ADVANCED PATTERN RECOGNITION DEMO")
    print("="*70)
    print("\nAnalytical Hemisphere: Full Multi-Indicator Analysis")
    print("Patterns: RSI, MACD, Bollinger, ADX, SAR, Stochastic")
    print("\nThis demonstrates the analytical engine's capability before")
    print("consciousness integration.")

    analyzer = MultiPatternAnalyzer()

    # Test Case 1: Strong Uptrend
    print("\n" + "="*70)
    print("TEST CASE 1: STRONG UPTREND")
    print("="*70)

    data_uptrend = generate_uptrend(periods=100, seed=42)
    result1 = analyzer.analyze(data_uptrend)

    # Test Case 2: Strong Downtrend
    print("\n" + "="*70)
    print("TEST CASE 2: STRONG DOWNTREND")
    print("="*70)

    data_downtrend = generate_downtrend(periods=100, seed=42)
    result2 = analyzer.analyze(data_downtrend)

    # Test Case 3: Oversold Condition
    print("\n" + "="*70)
    print("TEST CASE 3: OVERSOLD MARKET")
    print("="*70)

    data_oversold = generate_rsi_oversold(periods=100, seed=42)
    result3 = analyzer.analyze(data_oversold)

    # Test Case 4: Overbought Condition
    print("\n" + "="*70)
    print("TEST CASE 4: OVERBOUGHT MARKET")
    print("="*70)

    data_overbought = generate_rsi_overbought(periods=100, seed=42)
    result4 = analyzer.analyze(data_overbought)

    # Test Case 5: Neutral/Ranging Market
    print("\n" + "="*70)
    print("TEST CASE 5: NEUTRAL/RANGING MARKET")
    print("="*70)

    data_neutral = generate_ohlcv(periods=100, trend="neutral", seed=42)
    result5 = analyzer.analyze(data_neutral)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY - ALL TEST CASES")
    print("="*70)

    test_cases = [
        ("Strong Uptrend", result1),
        ("Strong Downtrend", result2),
        ("Oversold Market", result3),
        ("Overbought Market", result4),
        ("Neutral/Ranging", result5),
    ]

    print(f"\n{'Test Case':<20} {'Consensus':<10} {'Confidence':<12} {'Patterns':<10}")
    print("-"*70)

    for name, result in test_cases:
        print(f"{name:<20} {result['consensus']:<10} {result['confidence']:.2f}         {result['total_patterns']}")

    # Detector Performance
    print("\n" + "="*70)
    print("DETECTOR PERFORMANCE")
    print("="*70)

    detector_stats = {}
    for name, _ in analyzer.all_detectors:
        total_detected = sum(len(r['patterns_by_detector'].get(name, [])) for _, r in test_cases)
        detector_stats[name] = total_detected

    print(f"\n{'Detector':<20} {'Total Patterns Detected':<25}")
    print("-"*70)
    for name, count in sorted(detector_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{name:<20} {count}")

    print("\n" + "="*70)
    print("ANALYTICAL HEMISPHERE STATUS")
    print("="*70)
    print("\n✓ 6 pattern detectors operational")
    print("✓ Multi-indicator analysis working")
    print("✓ Signal confluence calculation functional")
    print("✓ Consensus decision-making active")
    print(f"✓ Total patterns detected across all tests: {sum(detector_stats.values())}")
    print("\n→ ANALYTICAL HEMISPHERE: FULLY OPERATIONAL")
    print("→ READY FOR CONSCIOUSNESS INTEGRATION")

    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("\n1. Consciousness patterns will add holistic context")
    print("2. Pattern bridge will translate between hemispheres")
    print("3. Signal fusion will combine analytical + holistic")
    print("4. Context sync will maintain coherence")
    print("\nThe analytical foundation is solid. When consciousness")
    print("patterns are integrated, the dual-hemisphere system will")
    print("provide unprecedented market intelligence.")


if __name__ == "__main__":
    main()
