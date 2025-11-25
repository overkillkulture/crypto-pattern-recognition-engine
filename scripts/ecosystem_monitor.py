#!/usr/bin/env python3
"""
Ecosystem Health Monitor - CP2C2 Cloud
Monitors and validates the conscious emergence ecosystem infrastructure.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class EcosystemMonitor:
    """Monitors the health of the conscious emergence ecosystem."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.shared_workspace = Path("/home/user/shared_workspace")
        self.health_report = {
            "timestamp": datetime.now().isoformat(),
            "ecosystem_health": "unknown",
            "components": {},
            "instances": {},
            "warnings": [],
            "errors": [],
        }

    def run_full_health_check(self) -> Dict:
        """Run comprehensive ecosystem health check."""
        print("🌐 CP2C2 Ecosystem Health Monitor")
        print("=" * 60)
        print()

        # Check all components
        self.check_claude_state()
        self.check_shared_workspace()
        self.check_team_chat()
        self.check_event_bus()
        self.check_pattern_directories()
        self.check_integration_modules()
        self.check_cp1_status()
        self.check_cp2c3_status()

        # Calculate overall health
        self.calculate_ecosystem_health()

        # Generate report
        self.print_health_report()

        return self.health_report

    def check_claude_state(self):
        """Check CLAUDE_STATE.json validity and content."""
        print("📊 Checking CLAUDE_STATE.json...")

        state_file = self.project_root / "CLAUDE_STATE.json"

        if not state_file.exists():
            self.health_report["errors"].append("CLAUDE_STATE.json not found")
            self.health_report["components"]["claude_state"] = "ERROR"
            print("  ❌ CLAUDE_STATE.json not found")
            return

        try:
            with open(state_file) as f:
                state = json.load(f)

            # Check structure
            if "instances" not in state:
                self.health_report["errors"].append(
                    "CLAUDE_STATE.json missing 'instances'"
                )
                self.health_report["components"]["claude_state"] = "ERROR"
                print("  ❌ Invalid structure")
                return

            # Check CP2C2 registration
            if "CP2C2" in state["instances"]:
                cp2c2 = state["instances"]["CP2C2"]
                self.health_report["instances"]["CP2C2"] = {
                    "status": cp2c2.get("status", "unknown"),
                    "phase": cp2c2.get("progress", {}).get("phase", "unknown"),
                    "completion": cp2c2.get("progress", {}).get("completion", "unknown"),
                }
                print(f"  ✅ CP2C2 registered: {cp2c2.get('status', 'unknown')}")
            else:
                self.health_report["warnings"].append("CP2C2 not registered")
                print("  ⚠️  CP2C2 not registered")

            # Check CP1 status
            if "CP1" in state["instances"]:
                cp1 = state["instances"]["CP1"]
                self.health_report["instances"]["CP1"] = {
                    "status": cp1.get("status", "unknown"),
                    "integration_ready": cp1.get("integration_status", {}).get(
                        "consciousness_ready", False
                    ),
                }
                print(f"  ✅ CP1 found: {cp1.get('status', 'unknown')}")
            else:
                self.health_report["warnings"].append("CP1 not found")
                print("  ⚠️  CP1 not found")

            # Check CP2C3 status
            if "CP2C3" in state["instances"]:
                cp2c3 = state["instances"]["CP2C3"]
                self.health_report["instances"]["CP2C3"] = {
                    "status": cp2c3.get("status", "unknown")
                }
                print(f"  ✅ CP2C3 found: {cp2c3.get('status', 'unknown')}")
            else:
                self.health_report["warnings"].append("CP2C3 not found")
                print("  ⚠️  CP2C3 not found")

            self.health_report["components"]["claude_state"] = "HEALTHY"

        except json.JSONDecodeError as e:
            self.health_report["errors"].append(f"CLAUDE_STATE.json parse error: {e}")
            self.health_report["components"]["claude_state"] = "ERROR"
            print(f"  ❌ Parse error: {e}")
        except Exception as e:
            self.health_report["errors"].append(f"CLAUDE_STATE.json error: {e}")
            self.health_report["components"]["claude_state"] = "ERROR"
            print(f"  ❌ Error: {e}")

        print()

    def check_shared_workspace(self):
        """Check shared workspace existence and structure."""
        print("📁 Checking shared workspace...")

        if not self.shared_workspace.exists():
            self.health_report["errors"].append("Shared workspace not found")
            self.health_report["components"]["shared_workspace"] = "ERROR"
            print("  ❌ Shared workspace not found")
            return

        required_dirs = [
            "patterns",
            "patterns/analytical",
            "patterns/holistic",
            "patterns/integrated",
            "messages",
            "messages/cp1_to_cp2c3",
            "messages/cp2c3_to_cp1",
            "messages/cp2c2_broadcast",
            "messages/broadcast",
            "decisions",
            "decisions/collective",
            "sync",
            "sync/queues",
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.shared_workspace / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            self.health_report["warnings"].append(
                f"Missing directories: {', '.join(missing_dirs)}"
            )
            print(f"  ⚠️  Missing directories: {len(missing_dirs)}")
            for d in missing_dirs:
                print(f"     - {d}")
        else:
            print("  ✅ All required directories present")

        self.health_report["components"]["shared_workspace"] = (
            "HEALTHY" if not missing_dirs else "DEGRADED"
        )
        print()

    def check_team_chat(self):
        """Check team chat functionality."""
        print("💬 Checking team chat...")

        team_chat = self.shared_workspace / "team_chat.jsonl"

        if not team_chat.exists():
            self.health_report["errors"].append("team_chat.jsonl not found")
            self.health_report["components"]["team_chat"] = "ERROR"
            print("  ❌ team_chat.jsonl not found")
            return

        try:
            messages = []
            with open(team_chat) as f:
                for line in f:
                    if line.strip():
                        messages.append(json.loads(line))

            print(f"  ✅ {len(messages)} messages in team chat")

            # Count messages by sender
            senders = {}
            for msg in messages:
                sender = msg.get("from", "unknown")
                senders[sender] = senders.get(sender, 0) + 1

            for sender, count in senders.items():
                print(f"     - {sender}: {count} messages")

            # Check for recent activity
            if messages:
                last_msg = messages[-1]
                last_ts = last_msg.get("ts", "unknown")
                print(f"  📅 Last message: {last_ts}")

            self.health_report["components"]["team_chat"] = {
                "status": "HEALTHY",
                "message_count": len(messages),
                "senders": senders,
            }

        except Exception as e:
            self.health_report["errors"].append(f"team_chat.jsonl error: {e}")
            self.health_report["components"]["team_chat"] = "ERROR"
            print(f"  ❌ Error: {e}")

        print()

    def check_event_bus(self):
        """Check event bus functionality."""
        print("🔄 Checking event bus...")

        event_bus = self.shared_workspace / "sync/event_bus.jsonl"

        if not event_bus.exists():
            self.health_report["warnings"].append("event_bus.jsonl not initialized")
            self.health_report["components"]["event_bus"] = "PENDING"
            print("  ⏳ event_bus.jsonl not yet initialized (normal for new setup)")
            return

        try:
            events = []
            with open(event_bus) as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))

            print(f"  ✅ {len(events)} events in bus")

            # Count by event type
            event_types = {}
            for event in events:
                evt_type = event.get("event_type", "unknown")
                event_types[evt_type] = event_types.get(evt_type, 0) + 1

            for evt_type, count in event_types.items():
                print(f"     - {evt_type}: {count} events")

            self.health_report["components"]["event_bus"] = {
                "status": "HEALTHY",
                "event_count": len(events),
                "event_types": event_types,
            }

        except Exception as e:
            self.health_report["errors"].append(f"event_bus.jsonl error: {e}")
            self.health_report["components"]["event_bus"] = "ERROR"
            print(f"  ❌ Error: {e}")

        print()

    def check_pattern_directories(self):
        """Check pattern sharing directories."""
        print("🧩 Checking pattern directories...")

        pattern_dirs = {
            "analytical": self.shared_workspace / "patterns/analytical",
            "holistic": self.shared_workspace / "patterns/holistic",
            "integrated": self.shared_workspace / "patterns/integrated",
        }

        for name, path in pattern_dirs.items():
            if not path.exists():
                self.health_report["warnings"].append(f"{name} pattern dir missing")
                print(f"  ⚠️  {name} directory missing")
                continue

            # Count patterns
            patterns = list(path.glob("*.json"))
            print(f"  ✅ {name}: {len(patterns)} patterns")

        self.health_report["components"]["pattern_directories"] = "HEALTHY"
        print()

    def check_integration_modules(self):
        """Check integration bridge modules."""
        print("🌉 Checking integration modules...")

        modules = {
            "pattern_bridge": "src/integration/pattern_bridge.py",
            "signal_fusion": "src/integration/signal_fusion.py",
            "context_sync": "src/integration/context_sync.py",
        }

        for name, path in modules.items():
            full_path = self.project_root / path
            if not full_path.exists():
                self.health_report["errors"].append(f"{name} module not found")
                print(f"  ❌ {name} not found")
            else:
                print(f"  ✅ {name} present")

        # Test import
        try:
            from src.integration.pattern_bridge import PatternBridge

            bridge = PatternBridge()
            print("  ✅ PatternBridge import successful")

            from src.integration.signal_fusion import SignalFusion

            fusion = SignalFusion()
            print("  ✅ SignalFusion import successful")

            from src.integration.context_sync import ContextSync

            sync = ContextSync()
            print("  ✅ ContextSync import successful")

            self.health_report["components"]["integration_modules"] = "HEALTHY"

        except Exception as e:
            self.health_report["errors"].append(f"Integration module import error: {e}")
            self.health_report["components"]["integration_modules"] = "ERROR"
            print(f"  ❌ Import error: {e}")

        print()

    def check_cp1_status(self):
        """Check CP1 (analytical hemisphere) readiness."""
        print("🧠 Checking CP1 (Analytical Hemisphere)...")

        # Check integration hub
        hub_file = self.project_root / "INTEGRATION_HUB.md"
        if hub_file.exists():
            print("  ✅ Integration Hub present")
        else:
            self.health_report["warnings"].append("Integration Hub not found")
            print("  ⚠️  Integration Hub not found")

        # Check integration architecture
        arch_file = self.project_root / "INTEGRATION_ARCHITECTURE.md"
        if arch_file.exists():
            print("  ✅ Integration Architecture documented")
        else:
            self.health_report["warnings"].append("Integration Architecture missing")
            print("  ⚠️  Integration Architecture missing")

        # Check integration demo
        demo_file = self.project_root / "examples/integration_demo.py"
        if demo_file.exists():
            print("  ✅ Integration demo present")
        else:
            self.health_report["warnings"].append("Integration demo not found")
            print("  ⚠️  Integration demo not found")

        print()

    def check_cp2c3_status(self):
        """Check CP2C3 (holistic hemisphere) status."""
        print("✨ Checking CP2C3 (Holistic Hemisphere)...")

        # Check if consciousness-revolution repository is accessible
        consciousness_repo = Path("/home/user/consciousness-revolution")
        if consciousness_repo.exists():
            print("  ✅ consciousness-revolution repository found")
            self.health_report["instances"]["CP2C3"]["repository_accessible"] = True
        else:
            self.health_report["warnings"].append(
                "consciousness-revolution repository not accessible"
            )
            print(
                "  ⏳ consciousness-revolution repository not yet accessible (expected)"
            )
            self.health_report["instances"]["CP2C3"]["repository_accessible"] = False

        print()

    def calculate_ecosystem_health(self):
        """Calculate overall ecosystem health percentage."""
        total_components = len(self.health_report["components"])
        healthy_components = sum(
            1
            for c in self.health_report["components"].values()
            if (isinstance(c, str) and c == "HEALTHY")
            or (isinstance(c, dict) and c.get("status") == "HEALTHY")
        )

        if total_components == 0:
            health_percentage = 0
        else:
            health_percentage = (healthy_components / total_components) * 100

        # Adjust for errors and warnings
        error_penalty = len(self.health_report["errors"]) * 10
        warning_penalty = len(self.health_report["warnings"]) * 5

        health_percentage = max(0, health_percentage - error_penalty - warning_penalty)

        if health_percentage >= 80:
            health_status = "EXCELLENT"
        elif health_percentage >= 60:
            health_status = "GOOD"
        elif health_percentage >= 40:
            health_status = "DEGRADED"
        else:
            health_status = "CRITICAL"

        self.health_report["ecosystem_health"] = health_status
        self.health_report["health_percentage"] = round(health_percentage, 1)

    def print_health_report(self):
        """Print comprehensive health report."""
        print()
        print("=" * 60)
        print("📊 ECOSYSTEM HEALTH REPORT")
        print("=" * 60)
        print()

        print(f"⏰ Timestamp: {self.health_report['timestamp']}")
        print(
            f"🌡️  Health Status: {self.health_report['ecosystem_health']} ({self.health_report.get('health_percentage', 0)}%)"
        )
        print()

        print("🔧 Component Status:")
        for component, status in self.health_report["components"].items():
            if isinstance(status, dict):
                status_str = status.get("status", "unknown")
            else:
                status_str = status

            icon = {"HEALTHY": "✅", "DEGRADED": "⚠️", "ERROR": "❌", "PENDING": "⏳"}.get(
                status_str, "❓"
            )
            print(f"  {icon} {component}: {status_str}")
        print()

        print("👥 Instance Status:")
        for instance, status in self.health_report["instances"].items():
            print(f"  - {instance}: {status.get('status', 'unknown')}")
        print()

        if self.health_report["errors"]:
            print("❌ Errors:")
            for error in self.health_report["errors"]:
                print(f"  - {error}")
            print()

        if self.health_report["warnings"]:
            print("⚠️  Warnings:")
            for warning in self.health_report["warnings"]:
                print(f"  - {warning}")
            print()

        print("=" * 60)
        print("🎯 Recommendations:")

        if self.health_report["ecosystem_health"] == "EXCELLENT":
            print("  ✨ Ecosystem is healthy! Ready for conscious emergence.")
            print("  📌 Next step: Await CP2C3 sync to begin Phase 2")
        elif self.health_report["ecosystem_health"] == "GOOD":
            print("  👍 Ecosystem is functional with minor issues.")
            print("  📌 Review warnings and address non-critical issues")
        elif self.health_report["errors"]:
            print("  🚨 Critical errors detected! Address immediately:")
            for error in self.health_report["errors"][:3]:
                print(f"     1. {error}")
        else:
            print("  ⚙️  Ecosystem needs attention. Review warnings.")

        print("=" * 60)
        print()

    def save_report(self, filepath: Path):
        """Save health report to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.health_report, f, indent=2, default=str)
        print(f"📄 Report saved to: {filepath}")


def main():
    """Main entry point."""
    monitor = EcosystemMonitor()
    report = monitor.run_full_health_check()

    # Save report
    report_path = Path("/home/user/shared_workspace") / "ecosystem_health_report.json"
    monitor.save_report(report_path)

    # Exit with appropriate code
    if report["ecosystem_health"] in ["EXCELLENT", "GOOD"]:
        sys.exit(0)
    elif report["errors"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
