"""Main pattern recognition engine."""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger

from src.core.interfaces import (
    PatternDetector,
    DataProvider,
    Analyzer,
    AlertHandler,
    MLModel,
)
from src.core.types import (
    Exchange,
    Timeframe,
    PatternResult,
    AnalysisResult,
    Alert,
    Priority,
)


class PatternRecognitionEngine:
    """
    Main engine for cryptocurrency pattern recognition.

    Orchestrates data ingestion, pattern detection, ML analysis,
    and alert generation across multiple exchanges and timeframes.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the engine.

        Args:
            config: Engine configuration
        """
        self.config = config
        self.running = False

        # Core components (to be injected)
        self.data_provider: Optional[DataProvider] = None
        self.pattern_detectors: List[PatternDetector] = []
        self.analyzers: List[Analyzer] = []
        self.alert_handlers: List[AlertHandler] = []
        self.ml_models: List[MLModel] = []

        # State
        self.active_symbols: List[str] = []
        self.active_timeframes: List[Timeframe] = []
        self.active_exchanges: List[Exchange] = []

        # Cache and buffers
        self._pattern_cache: Dict[str, List[PatternResult]] = {}
        self._analysis_cache: Dict[str, AnalysisResult] = {}

        logger.info("Pattern Recognition Engine initialized")

    def set_data_provider(self, provider: DataProvider) -> None:
        """Set the data provider."""
        self.data_provider = provider
        logger.info(f"Data provider registered: {type(provider).__name__}")

    def add_pattern_detector(self, detector: PatternDetector) -> None:
        """Add a pattern detector."""
        self.pattern_detectors.append(detector)
        logger.info(f"Pattern detector registered: {type(detector).__name__}")

    def add_analyzer(self, analyzer: Analyzer) -> None:
        """Add an analyzer."""
        self.analyzers.append(analyzer)
        logger.info(f"Analyzer registered: {type(analyzer).__name__}")

    def add_alert_handler(self, handler: AlertHandler) -> None:
        """Add an alert handler."""
        self.alert_handlers.append(handler)
        logger.info(f"Alert handler registered: {type(handler).__name__}")

    def add_ml_model(self, model: MLModel) -> None:
        """Add a machine learning model."""
        self.ml_models.append(model)
        logger.info(f"ML model registered: {model.model_name}")

    def configure(
        self,
        symbols: List[str],
        timeframes: List[Timeframe],
        exchanges: List[Exchange],
    ) -> None:
        """
        Configure active symbols, timeframes, and exchanges.

        Args:
            symbols: List of trading pairs
            timeframes: List of timeframes to analyze
            exchanges: List of exchanges to monitor
        """
        self.active_symbols = symbols
        self.active_timeframes = timeframes
        self.active_exchanges = exchanges

        logger.info(f"Configured: {len(symbols)} symbols, "
                   f"{len(timeframes)} timeframes, "
                   f"{len(exchanges)} exchanges")

    async def start(self) -> None:
        """Start the pattern recognition engine."""
        if not self.data_provider:
            raise ValueError("Data provider not set")

        if not self.pattern_detectors:
            logger.warning("No pattern detectors registered")

        self.running = True
        logger.info("🚀 Pattern Recognition Engine started")

        # Start monitoring all configured pairs
        tasks = []
        for exchange in self.active_exchanges:
            for symbol in self.active_symbols:
                for timeframe in self.active_timeframes:
                    task = asyncio.create_task(
                        self._monitor_symbol(exchange, symbol, timeframe)
                    )
                    tasks.append(task)

        # Wait for all monitoring tasks
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop(self) -> None:
        """Stop the engine."""
        self.running = False
        logger.info("Pattern Recognition Engine stopped")

    async def analyze_symbol(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 500,
    ) -> AnalysisResult:
        """
        Analyze a single symbol.

        Args:
            exchange: Exchange to analyze
            symbol: Trading pair
            timeframe: Analysis timeframe
            limit: Number of candles to analyze

        Returns:
            Analysis result
        """
        logger.debug(f"Analyzing {symbol} on {exchange} ({timeframe})")

        # Fetch data
        data = await self.data_provider.get_ohlcv(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        # Detect patterns
        all_patterns = []
        for detector in self.pattern_detectors:
            patterns = await detector.detect_patterns(symbol, timeframe, data)
            all_patterns.extend(patterns)

        logger.info(f"Detected {len(all_patterns)} patterns for {symbol}")

        # Run analyzers
        analysis_results = []
        for analyzer in self.analyzers:
            result = await analyzer.analyze(symbol, timeframe, data, all_patterns)
            analysis_results.append(result)

        # Use the first analyzer's result (or combine multiple)
        final_analysis = analysis_results[0] if analysis_results else None

        # Run ML predictions
        for model in self.ml_models:
            if model.trained:
                prediction = await model.predict(data)
                logger.debug(f"ML prediction: {prediction}")

        # Generate alerts for high-confidence patterns
        await self._process_alerts(all_patterns)

        # Cache results
        cache_key = f"{exchange}:{symbol}:{timeframe}"
        self._pattern_cache[cache_key] = all_patterns
        if final_analysis:
            self._analysis_cache[cache_key] = final_analysis

        return final_analysis

    async def _monitor_symbol(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
    ) -> None:
        """Monitor a symbol continuously."""
        logger.info(f"Monitoring {symbol} on {exchange} ({timeframe})")

        while self.running:
            try:
                await self.analyze_symbol(exchange, symbol, timeframe)

                # Wait based on timeframe
                interval = self._get_update_interval(timeframe)
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _process_alerts(self, patterns: List[PatternResult]) -> None:
        """Process patterns and generate alerts."""
        min_confidence = self.config.get('alerts', {}).get('filters', {}).get('min_confidence', 0.75)

        for pattern in patterns:
            if pattern.confidence >= min_confidence:
                alert = Alert(
                    alert_id=f"alert_{pattern.pattern_id}_{int(datetime.now().timestamp())}",
                    timestamp=datetime.now(),
                    pattern_result=pattern,
                    priority=self._calculate_priority(pattern),
                    message=self._format_alert_message(pattern),
                    triggered_by="pattern_detection",
                    conditions={"confidence": pattern.confidence},
                )

                # Send to all alert handlers
                for handler in self.alert_handlers:
                    try:
                        await handler.send_alert(alert)
                    except Exception as e:
                        logger.error(f"Error sending alert: {e}")

    def _calculate_priority(self, pattern: PatternResult) -> Priority:
        """Calculate alert priority based on pattern characteristics."""
        if pattern.confidence >= 0.95:
            return Priority.CRITICAL
        elif pattern.confidence >= 0.85:
            return Priority.HIGH
        elif pattern.confidence >= 0.75:
            return Priority.MEDIUM
        else:
            return Priority.LOW

    def _format_alert_message(self, pattern: PatternResult) -> str:
        """Format alert message."""
        return (
            f"🎯 {pattern.pattern_name} detected on {pattern.symbol} ({pattern.timeframe})\n"
            f"Signal: {pattern.signal.value.upper()}\n"
            f"Confidence: {pattern.confidence:.2%}\n"
            f"Time: {pattern.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def _get_update_interval(self, timeframe: Timeframe) -> int:
        """Get update interval in seconds based on timeframe."""
        intervals = {
            Timeframe.ONE_MINUTE: 60,
            Timeframe.FIVE_MINUTES: 300,
            Timeframe.FIFTEEN_MINUTES: 900,
            Timeframe.THIRTY_MINUTES: 1800,
            Timeframe.ONE_HOUR: 3600,
            Timeframe.FOUR_HOURS: 14400,
            Timeframe.ONE_DAY: 86400,
        }
        return intervals.get(timeframe, 60)

    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "running": self.running,
            "symbols_monitored": len(self.active_symbols),
            "timeframes": len(self.active_timeframes),
            "exchanges": len(self.active_exchanges),
            "pattern_detectors": len(self.pattern_detectors),
            "analyzers": len(self.analyzers),
            "alert_handlers": len(self.alert_handlers),
            "ml_models": len(self.ml_models),
            "cached_patterns": len(self._pattern_cache),
            "cached_analyses": len(self._analysis_cache),
        }
