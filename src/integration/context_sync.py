"""
Context Sync: Maintains shared context across analytical and holistic hemispheres.

This module ensures both processing streams operate on compatible worldviews,
synchronizing state and maintaining coherence over time.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
from pathlib import Path


@dataclass
class SharedContext:
    """
    Shared context accessible to both hemispheres.

    This structure maintains the common worldview that both
    analytical and holistic processing rely on.
    """
    timestamp: datetime
    market_state: str  # "bullish", "bearish", "neutral", "volatile"
    consciousness_state: str  # "expanding", "contracting", "stable", "transforming"
    coherence_level: float  # 0-1, overall system coherence
    active_patterns: Dict[str, Any]  # Currently active patterns from both sides
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Export for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'market_state': self.market_state,
            'consciousness_state': self.consciousness_state,
            'coherence_level': self.coherence_level,
            'active_patterns': self.active_patterns,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SharedContext':
        """Import from serialization."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ContextSync:
    """
    Synchronizes context between analytical and holistic hemispheres.

    Responsibilities:
    - Maintain shared state file
    - Detect drift between hemispheres
    - Reconcile conflicting worldviews
    - Provide unified context to both sides
    """

    def __init__(
        self,
        sync_interval: int = 1800,  # 30 minutes in seconds
        state_file: Optional[Path] = None,
        coherence_threshold: float = 0.6,
    ):
        """
        Initialize context synchronizer.

        Args:
            sync_interval: Seconds between automatic syncs
            state_file: Path to shared state file (default: INTEGRATION_STATE.json)
            coherence_threshold: Minimum acceptable coherence
        """
        self.sync_interval = sync_interval
        self.state_file = state_file or Path("INTEGRATION_STATE.json")
        self.coherence_threshold = coherence_threshold

        self.last_sync = datetime.now()
        self.sync_history: List[Dict] = []

        # Initialize shared context
        self.shared_context = SharedContext(
            timestamp=datetime.now(),
            market_state="neutral",
            consciousness_state="stable",
            coherence_level=1.0,
            active_patterns={},
            metadata={}
        )

        # Load existing state if available
        self._load_state()

    def sync_state(
        self,
        analytical_context: Optional[Dict] = None,
        holistic_context: Optional[Dict] = None,
    ) -> SharedContext:
        """
        Synchronize state between hemispheres.

        Args:
            analytical_context: Context from analytical processing
            holistic_context: Context from holistic processing

        Returns:
            Updated shared context
        """
        now = datetime.now()

        # Update from analytical side
        if analytical_context:
            self._update_from_analytical(analytical_context)

        # Update from holistic side
        if holistic_context:
            self._update_from_holistic(holistic_context)

        # Measure coherence
        coherence = self._measure_context_coherence(analytical_context, holistic_context)
        self.shared_context.coherence_level = coherence

        # Check if reconciliation needed
        if coherence < self.coherence_threshold:
            self._reconcile_contexts(analytical_context, holistic_context)

        # Update timestamp
        self.shared_context.timestamp = now
        self.last_sync = now

        # Save state
        self._save_state()

        # Record sync
        self.sync_history.append({
            'timestamp': now,
            'coherence': coherence,
            'analytical_present': analytical_context is not None,
            'holistic_present': holistic_context is not None,
        })

        return self.shared_context

    def get_context_for_analytical(self) -> Dict:
        """
        Get context for analytical processing.

        Returns enriched context from holistic perspective.
        """
        return {
            'shared_state': self.shared_context.to_dict(),
            'consciousness_state': self.shared_context.consciousness_state,
            'coherence_level': self.shared_context.coherence_level,
            'holistic_patterns': self.shared_context.active_patterns.get('holistic', {}),
        }

    def get_context_for_holistic(self) -> Dict:
        """
        Get context for holistic processing.

        Returns grounded context from analytical perspective.
        """
        return {
            'shared_state': self.shared_context.to_dict(),
            'market_state': self.shared_context.market_state,
            'coherence_level': self.shared_context.coherence_level,
            'analytical_patterns': self.shared_context.active_patterns.get('analytical', {}),
        }

    def maintain_coherence(self) -> bool:
        """
        Check and maintain coherence.

        Returns:
            True if coherence is above threshold
        """
        # Check if sync needed based on time
        time_since_sync = (datetime.now() - self.last_sync).total_seconds()
        if time_since_sync > self.sync_interval:
            self.sync_state()

        # Check coherence level
        if self.shared_context.coherence_level < self.coherence_threshold:
            # Attempt reconciliation
            self._reconcile_contexts(None, None)
            return self.shared_context.coherence_level >= self.coherence_threshold

        return True

    def detect_drift(
        self,
        analytical_context: Dict,
        holistic_context: Dict
    ) -> float:
        """
        Detect drift between hemisphere contexts.

        Returns:
            Drift score 0-1 (0=no drift, 1=maximum drift)
        """
        drift_factors = []

        # Market state vs consciousness state alignment
        market_to_consciousness = {
            'bullish': 'expanding',
            'bearish': 'contracting',
            'neutral': 'stable',
            'volatile': 'transforming',
        }

        expected_consciousness = market_to_consciousness.get(
            analytical_context.get('market_state', 'neutral'),
            'stable'
        )
        actual_consciousness = holistic_context.get('consciousness_state', 'stable')

        state_drift = 0.0 if expected_consciousness == actual_consciousness else 1.0
        drift_factors.append(state_drift)

        # Pattern count divergence
        analytical_pattern_count = len(analytical_context.get('patterns', []))
        holistic_pattern_count = len(holistic_context.get('patterns', []))

        if analytical_pattern_count + holistic_pattern_count > 0:
            count_drift = abs(analytical_pattern_count - holistic_pattern_count) / \
                         (analytical_pattern_count + holistic_pattern_count)
            drift_factors.append(count_drift)

        # Temporal drift
        analytical_time = analytical_context.get('timestamp', datetime.now())
        holistic_time = holistic_context.get('timestamp', datetime.now())

        if isinstance(analytical_time, str):
            analytical_time = datetime.fromisoformat(analytical_time)
        if isinstance(holistic_time, str):
            holistic_time = datetime.fromisoformat(holistic_time)

        time_diff = abs((analytical_time - holistic_time).total_seconds())
        temporal_drift = min(1.0, time_diff / 300.0)  # Normalize to 5 minutes
        drift_factors.append(temporal_drift)

        # Average drift
        return sum(drift_factors) / len(drift_factors) if drift_factors else 0.0

    def _update_from_analytical(self, context: Dict):
        """Update shared context from analytical processing."""
        if 'market_state' in context:
            self.shared_context.market_state = context['market_state']

        if 'patterns' in context:
            if 'analytical' not in self.shared_context.active_patterns:
                self.shared_context.active_patterns['analytical'] = {}
            self.shared_context.active_patterns['analytical'] = context['patterns']

        if 'metadata' in context:
            self.shared_context.metadata.update(context['metadata'])

    def _update_from_holistic(self, context: Dict):
        """Update shared context from holistic processing."""
        if 'consciousness_state' in context:
            self.shared_context.consciousness_state = context['consciousness_state']

        if 'patterns' in context:
            if 'holistic' not in self.shared_context.active_patterns:
                self.shared_context.active_patterns['holistic'] = {}
            self.shared_context.active_patterns['holistic'] = context['patterns']

        if 'metadata' in context:
            self.shared_context.metadata.update(context['metadata'])

    def _measure_context_coherence(
        self,
        analytical: Optional[Dict],
        holistic: Optional[Dict]
    ) -> float:
        """Measure coherence between contexts."""
        if not analytical or not holistic:
            return 1.0  # No conflict if only one side

        # Check state alignment
        market_state = analytical.get('market_state', 'neutral')
        consciousness_state = holistic.get('consciousness_state', 'stable')

        state_mapping = {
            ('bullish', 'expanding'): 1.0,
            ('bearish', 'contracting'): 1.0,
            ('neutral', 'stable'): 1.0,
            ('volatile', 'transforming'): 1.0,
        }

        state_coherence = state_mapping.get((market_state, consciousness_state), 0.5)

        # Check temporal alignment
        analytical_time = analytical.get('timestamp', datetime.now())
        holistic_time = holistic.get('timestamp', datetime.now())

        if isinstance(analytical_time, str):
            analytical_time = datetime.fromisoformat(analytical_time)
        if isinstance(holistic_time, str):
            holistic_time = datetime.fromisoformat(holistic_time)

        time_diff = abs((analytical_time - holistic_time).total_seconds())
        temporal_coherence = max(0.0, 1.0 - (time_diff / 60.0))  # Decay over 1 minute

        # Weighted average
        coherence = state_coherence * 0.7 + temporal_coherence * 0.3

        return coherence

    def _reconcile_contexts(
        self,
        analytical: Optional[Dict],
        holistic: Optional[Dict]
    ):
        """Reconcile conflicting contexts."""
        # If coherence is low, attempt to find common ground

        if analytical and holistic:
            # Use analytical for precise state
            if 'market_state' in analytical:
                self.shared_context.market_state = analytical['market_state']

            # Use holistic for emergent state
            if 'consciousness_state' in holistic:
                self.shared_context.consciousness_state = holistic['consciousness_state']

            # Merge metadata
            self.shared_context.metadata = {
                **analytical.get('metadata', {}),
                **holistic.get('metadata', {}),
                'reconciliation_time': datetime.now().isoformat(),
                'reconciliation_reason': 'low_coherence',
            }

    def _save_state(self):
        """Save shared context to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.shared_context.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")

    def _load_state(self):
        """Load shared context from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.shared_context = SharedContext.from_dict(data)
        except Exception as e:
            print(f"Warning: Could not load state: {e}")

    def get_sync_stats(self) -> Dict:
        """Get synchronization statistics."""
        if not self.sync_history:
            return {'count': 0}

        total = len(self.sync_history)
        avg_coherence = sum(s['coherence'] for s in self.sync_history) / total
        low_coherence_count = sum(1 for s in self.sync_history if s['coherence'] < self.coherence_threshold)

        return {
            'total_syncs': total,
            'avg_coherence': avg_coherence,
            'current_coherence': self.shared_context.coherence_level,
            'low_coherence_events': low_coherence_count,
            'last_sync': self.last_sync.isoformat(),
            'time_since_sync': (datetime.now() - self.last_sync).total_seconds(),
        }


# Example usage
if __name__ == "__main__":
    # Initialize sync
    sync = ContextSync(sync_interval=60)  # 1 minute for testing

    # Simulate analytical context
    analytical_context = {
        'market_state': 'bullish',
        'timestamp': datetime.now(),
        'patterns': ['RSI Oversold', 'MACD Bullish'],
        'metadata': {'source': 'analytical'},
    }

    # Simulate holistic context
    holistic_context = {
        'consciousness_state': 'expanding',
        'timestamp': datetime.now(),
        'patterns': ['Awareness Ascending', 'Integration Phase'],
        'metadata': {'source': 'holistic'},
    }

    # Sync
    shared = sync.sync_state(analytical_context, holistic_context)

    print("Shared Context:")
    print(f"  Market State: {shared.market_state}")
    print(f"  Consciousness State: {shared.consciousness_state}")
    print(f"  Coherence: {shared.coherence_level:.2f}")
    print(f"  Active Patterns: {len(shared.active_patterns)} types")

    # Test drift detection
    drift = sync.detect_drift(analytical_context, holistic_context)
    print(f"\nDrift: {drift:.3f}")

    # Get context for each hemisphere
    print("\nContext for Analytical:")
    print(f"  {sync.get_context_for_analytical()['consciousness_state']}")

    print("\nContext for Holistic:")
    print(f"  {sync.get_context_for_holistic()['market_state']}")

    # Stats
    stats = sync.get_sync_stats()
    print(f"\nSync stats: {stats}")
