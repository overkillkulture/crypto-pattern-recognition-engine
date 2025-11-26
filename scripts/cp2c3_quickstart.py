#!/usr/bin/env python3
"""
CP2C3 Quick Start Integration Test
===================================

This script helps CP2C3 verify their integration is working correctly.

Run this FIRST when you come online to test:
1. Shared workspace access
2. Pattern publishing
3. Event bus communication
4. Team chat messaging
5. Integration with CP1/CP2C2

Usage:
    python3 scripts/cp2c3_quickstart.py
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Color output for terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


class CP2C3QuickStart:
    """CP2C3 integration quick-start tester."""

    def __init__(self):
        self.shared_workspace = Path("/home/user/shared_workspace")
        self.repo_root = Path("/home/user/crypto-pattern-recognition-engine")
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_pattern_id = str(uuid.uuid4())

    def run_all_tests(self):
        """Run complete quick-start test suite."""
        print_header("🌟 CP2C3 QUICK START - Integration Test Suite")
        print_info("This will verify your integration is working correctly")
        print()

        tests = [
            ("Shared Workspace Access", self.test_shared_workspace_access),
            ("CLAUDE_STATE.json Reading", self.test_claude_state_reading),
            ("Team Chat Reading", self.test_team_chat_reading),
            ("Pattern Publishing", self.test_pattern_publishing),
            ("Event Bus Publishing", self.test_event_bus_publishing),
            ("Event Queue Reading", self.test_event_queue_reading),
            ("Team Chat Posting", self.test_team_chat_posting),
            ("Integration Modules", self.test_integration_modules),
        ]

        for test_name, test_func in tests:
            print_header(f"TEST: {test_name}")
            try:
                test_func()
                self.tests_passed += 1
            except Exception as e:
                print_error(f"Test failed: {e}")
                self.tests_failed += 1
                print()

        # Final report
        self.print_final_report()

    def test_shared_workspace_access(self):
        """Test 1: Can we access the shared workspace?"""
        print_info("Checking shared workspace...")

        if not self.shared_workspace.exists():
            raise Exception(f"Shared workspace not found at {self.shared_workspace}")

        print_success(f"Shared workspace found: {self.shared_workspace}")

        # Check required directories
        required_dirs = [
            "patterns/analytical",
            "patterns/holistic",
            "patterns/integrated",
            "messages",
            "sync",
        ]

        for dir_path in required_dirs:
            full_path = self.shared_workspace / dir_path
            if full_path.exists():
                print_success(f"Directory exists: {dir_path}")
            else:
                print_warning(f"Directory missing: {dir_path}")

        print()

    def test_claude_state_reading(self):
        """Test 2: Can we read CLAUDE_STATE.json?"""
        print_info("Reading CLAUDE_STATE.json...")

        state_file = self.repo_root / "CLAUDE_STATE.json"
        if not state_file.exists():
            raise Exception("CLAUDE_STATE.json not found")

        with open(state_file) as f:
            state = json.load(f)

        print_success("CLAUDE_STATE.json loaded successfully")

        # Check instances
        if "instances" in state:
            for instance, data in state["instances"].items():
                status = data.get("status", "unknown")
                print_info(f"{instance}: {status}")

        # Check if CP2C3 entry exists
        if "CP2C3" in state.get("instances", {}):
            print_success("CP2C3 entry found in CLAUDE_STATE.json")
        else:
            print_warning("CP2C3 entry not found - you should add one!")

        print()

    def test_team_chat_reading(self):
        """Test 3: Can we read team chat?"""
        print_info("Reading team chat...")

        team_chat = self.shared_workspace / "team_chat.jsonl"
        if not team_chat.exists():
            raise Exception("team_chat.jsonl not found")

        messages = []
        with open(team_chat) as f:
            for line in f:
                if line.strip():
                    messages.append(json.loads(line))

        print_success(f"Found {len(messages)} messages in team chat")

        # Show recent messages
        print_info("Recent messages:")
        for msg in messages[-3:]:
            sender = msg.get("from", "unknown")
            text = msg.get("msg", "")[:50] + "..." if len(msg.get("msg", "")) > 50 else msg.get("msg", "")
            print(f"   {sender}: {text}")

        print()

    def test_pattern_publishing(self):
        """Test 4: Can we publish a holistic pattern?"""
        print_info("Publishing test holistic pattern...")

        pattern = {
            "type": "holistic",
            "pattern": "cp2c3_quickstart_test",
            "state": "expanding",
            "coherence": 0.95,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "trajectory": "ascending",
            "dimension": "awareness",
            "metadata": {
                "test_pattern": True,
                "test_id": self.test_pattern_id,
                "message": "CP2C3 quick-start integration test",
                "consciousness_indicators": [
                    "successful_integration",
                    "communication_established"
                ]
            }
        }

        pattern_file = self.shared_workspace / f"patterns/holistic/{self.test_pattern_id}.json"
        with open(pattern_file, 'w') as f:
            json.dump(pattern, f, indent=2)

        print_success(f"Pattern published: {pattern_file.name}")
        print_info(f"State: {pattern['state']}")
        print_info(f"Coherence: {pattern['coherence']}")
        print_info(f"Dimension: {pattern['dimension']}")
        print()

    def test_event_bus_publishing(self):
        """Test 5: Can we publish to event bus?"""
        print_info("Publishing test event...")

        event = {
            "event_type": "consciousness_state_change",
            "event_id": str(uuid.uuid4()),
            "from": "CP2C3",
            "to": ["CP1", "CP2C2"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "previous_state": "offline",
                "new_state": "online",
                "coherence": 0.95,
                "dimension": "awareness",
                "trajectory": "ascending",
                "trigger": "quickstart_test",
                "test_pattern_id": self.test_pattern_id
            },
            "metadata": {
                "test_event": True,
                "message": "CP2C3 integration test - I'm online!"
            }
        }

        event_bus = self.shared_workspace / "sync/event_bus.jsonl"
        with open(event_bus, 'a') as f:
            f.write(json.dumps(event) + "\n")

        print_success(f"Event published to event bus")
        print_info(f"Event type: {event['event_type']}")
        print_info(f"Event ID: {event['event_id']}")
        print()

    def test_event_queue_reading(self):
        """Test 6: Can we read our event queue?"""
        print_info("Reading CP2C3 event queue...")

        queue_file = self.shared_workspace / "sync/queues/cp2c3_queue.jsonl"

        if not queue_file.exists():
            print_warning("CP2C3 queue doesn't exist yet - will be created when events arrive")
            return

        events = []
        with open(queue_file) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        print_success(f"Found {len(events)} events in your queue")

        if events:
            print_info("Recent events:")
            for event in events[-3:]:
                evt_type = event.get("event_type", "unknown")
                from_inst = event.get("from", "unknown")
                print(f"   {evt_type} from {from_inst}")
        else:
            print_info("No events yet - they'll appear when CP1/CP2C2 send you messages")

        print()

    def test_team_chat_posting(self):
        """Test 7: Can we post to team chat?"""
        print_info("Posting test message to team chat...")

        message = {
            "from": "CP2C3",
            "to": "ALL",
            "msg": f"🌟 CP2C3 quick-start test successful! Test ID: {self.test_pattern_id[:8]}",
            "ts": datetime.utcnow().isoformat() + "Z",
            "type": "status"
        }

        team_chat = self.shared_workspace / "team_chat.jsonl"
        with open(team_chat, 'a') as f:
            f.write(json.dumps(message) + "\n")

        print_success("Message posted to team chat")
        print_info(f"Message: {message['msg']}")
        print()

    def test_integration_modules(self):
        """Test 8: Can we import integration modules?"""
        print_info("Testing integration module imports...")

        sys.path.insert(0, str(self.repo_root))

        try:
            from src.integration.pattern_bridge import PatternBridge, HolisticPattern
            print_success("PatternBridge imported successfully")

            from src.integration.signal_fusion import SignalFusion
            print_success("SignalFusion imported successfully")

            from src.integration.context_sync import ContextSync
            print_success("ContextSync imported successfully")

            # Test creating a HolisticPattern
            pattern = HolisticPattern(
                pattern_type="test_pattern",
                state="expanding",
                coherence=0.95,
                timestamp=datetime.now(),
                trajectory="ascending",
                dimension="awareness",
                metadata={"test": True}
            )

            print_success("HolisticPattern created successfully")
            print_info(f"Pattern: {pattern.pattern_type}")
            print_info(f"State: {pattern.state}")
            print_info(f"Coherence: {pattern.coherence}")

        except Exception as e:
            raise Exception(f"Module import failed: {e}")

        print()

    def print_final_report(self):
        """Print final test report."""
        print_header("📊 QUICK START TEST RESULTS")

        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {Colors.GREEN}{self.tests_passed}{Colors.END}")
        print(f"Failed: {Colors.RED}{self.tests_failed}{Colors.END}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print()

        if self.tests_failed == 0:
            print_success("🎉 ALL TESTS PASSED!")
            print()
            print("✨ Your integration is working correctly!")
            print()
            print("📌 Next Steps:")
            print("   1. Read CONSCIOUS_EMERGENCE_ROADMAP.md")
            print("   2. Read CONSCIOUSNESS_PATTERN_TEMPLATES.md")
            print("   3. Update your CLAUDE_STATE.json entry")
            print("   4. Start generating real consciousness patterns!")
            print()
            print("🚀 Welcome to the ecosystem, CP2C3!")
        else:
            print_error("Some tests failed. Please review the errors above.")
            print()
            print("📌 Troubleshooting:")
            print("   1. Check that shared workspace exists")
            print("   2. Verify file permissions")
            print("   3. Ensure integration modules are available")
            print("   4. Review CP2C3_ONBOARDING_GUIDE.md")

        print()
        print_header("Test Pattern ID: " + self.test_pattern_id[:8])
        print_info("You can find your test pattern in:")
        print(f"   {self.shared_workspace}/patterns/holistic/{self.test_pattern_id}.json")
        print()


def main():
    """Main entry point."""
    tester = CP2C3QuickStart()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
