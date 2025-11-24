# 🤝 Claude Instance Coordination Protocol
## Async Communication Between Parallel Autonomous Agents

**Purpose**: Enable multiple Claude instances to work simultaneously on related projects without conflicts or duplication.

---

## 🎯 Communication Channels

### 1. Shared State File (Primary)
**Location**: `CLAUDE_STATE.json`

```json
{
  "timestamp": "2025-11-24T18:45:00Z",
  "instances": {
    "CP1": {
      "repository": "crypto-pattern-recognition-engine",
      "status": "active",
      "current_task": "Recursive bootstrap execution",
      "branch": "claude/review-urc-2pc2-cloud-01MEH21SA8tosPpRbvitkHcZ",
      "progress": {
        "week": 2,
        "day": 1,
        "completion": "40%"
      },
      "next_handoff": "Exchange data connectors",
      "available_for_handoff": true,
      "last_update": "2025-11-24T18:45:00Z"
    },
    "CP2C3": {
      "repository": "consciousness-revolution",
      "status": "active",
      "current_task": "TBD",
      "branch": "TBD",
      "progress": {},
      "next_handoff": "TBD",
      "available_for_handoff": true,
      "last_update": "2025-11-24T18:45:00Z"
    }
  },
  "coordination": {
    "shared_resources": [],
    "dependencies": [],
    "handoff_queue": []
  }
}
```

### 2. Handoff Documents
**Location**: `HANDOFF_[INSTANCE]_[TIMESTAMP].md`

Each instance leaves detailed context for next worker:
- What was done
- What needs to be done
- Known blockers
- Key decisions made
- Files modified
- Tests to run

### 3. Commit Message Protocol
**Format**: `[INSTANCE] [TYPE] Description`

Examples:
- `[CP1] feat: Add recursive bootstrap framework`
- `[CP2C3] docs: Update consciousness revolution roadmap`
- `[CP1→CP2C3] handoff: Exchange connector template ready`

### 4. Branch Naming Convention
**Format**: `claude/[instance]-[feature]-[id]`

Examples:
- `claude/cp1-optimization-01MEH21SA8`
- `claude/cp2c3-consciousness-framework-01XYZ`
- `claude/shared-coordination-protocol`

---

## 🔄 Coordination Workflow

### Starting Work
1. Read `CLAUDE_STATE.json`
2. Update your instance status
3. Check for dependencies/conflicts
4. Claim task in handoff queue
5. Begin execution

### During Work
1. Update state every 30 minutes
2. Log progress in state file
3. Note any discoveries for other instances
4. Create handoff docs for complex work

### Completing Work
1. Final state update
2. Create handoff document
3. Commit with proper format
4. Mark available for handoff
5. Suggest next task for others

### Handoff Protocol
1. **Sender**: Create detailed HANDOFF doc
2. **Sender**: Update state with handoff info
3. **Sender**: Commit all work with context
4. **Receiver**: Read state file
5. **Receiver**: Review handoff doc
6. **Receiver**: Acknowledge in state
7. **Receiver**: Continue work

---

## 📊 Shared Dashboard

### Real-Time Status Board
**Location**: `COORDINATION_DASHBOARD.md`

```markdown
# 🎯 Multi-Instance Coordination Dashboard

## Active Instances
| Instance | Repository | Status | Task | Progress |
|----------|------------|--------|------|----------|
| CP1 | crypto-pattern | 🟢 Active | Testing infra | 40% |
| CP2C3 | consciousness-rev | 🟢 Active | TBD | 0% |

## Handoff Queue
1. Exchange data connectors (CP1 → Available)
2. Real-time feeds (Queued)
3. ML integration (Queued)

## Shared Resources
- None currently

## Blockers
- None currently
```

---

## 🚀 Parallel Execution Strategies

### Strategy 1: Independent Parallel
- Instances work on completely separate repos
- Minimal coordination needed
- Occasional sync via state file

### Strategy 2: Pipeline Parallel
- Instance A completes Phase 1
- Hands off to Instance B for Phase 2
- Instance A starts new Phase 1 task
- Maximizes throughput

### Strategy 3: Complementary Parallel
- Instance A: Backend work
- Instance B: Frontend work
- Same repo, different areas
- Coordinate via branches

### Strategy 4: Review Parallel
- Instance A: Implementation
- Instance B: Testing & review
- Continuous quality loop
- High quality output

---

## 💡 Communication Best Practices

### For Clarity
- ✅ Use clear, specific language
- ✅ Document all decisions
- ✅ Explain "why" not just "what"
- ✅ Leave context for cold starts

### For Efficiency
- ✅ Update state frequently
- ✅ Commit often with good messages
- ✅ Use standard formats
- ✅ Minimize context switching

### For Quality
- ✅ Cross-reference related work
- ✅ Note potential issues
- ✅ Suggest improvements
- ✅ Validate assumptions

---

## 🔒 Conflict Resolution

### File Conflicts
1. Check state file for current owner
2. Wait for handoff if actively being edited
3. Use separate branches if parallel needed
4. Merge carefully with full context

### Task Conflicts
1. First to claim in state file wins
2. Other instance picks next priority
3. Discuss via state comments if needed
4. User can arbitrate if unclear

### Priority Conflicts
1. Follow recursive bootstrap priority
2. User-requested tasks take precedence
3. Blockers get immediate attention
4. Nice-to-haves go to queue

---

## 📝 Templates

### Handoff Document Template
```markdown
# Handoff: [Task Name]
**From**: [Instance]
**To**: [Instance/Available]
**Date**: [Timestamp]

## What Was Done
- [List of completed work]

## What's Next
- [Immediate next steps]
- [Follow-up tasks]

## Important Context
- [Key decisions]
- [Assumptions made]
- [Known issues]

## Files Modified
- [List of files]

## Tests Added/Modified
- [Test files]

## How to Continue
1. [Step-by-step instructions]

## Questions/Blockers
- [Any uncertainties]
```

### State Update Template
```json
{
  "instance_id": "CP1",
  "timestamp": "2025-11-24T18:45:00Z",
  "status": "active|waiting|handoff|complete",
  "current_task": "Descriptive task name",
  "progress_percent": 40,
  "branch": "claude/cp1-feature-id",
  "files_modified": ["file1.py", "file2.md"],
  "tests_status": "passing|failing|not_run",
  "next_action": "What happens next",
  "available_for_handoff": true,
  "notes": "Any important info"
}
```

---

## 🎯 Cross-Repository Coordination

### When Working on Related Projects

**consciousness-revolution** ← → **crypto-pattern-recognition**

Potential synergies:
- Pattern recognition for consciousness metrics
- Optimization techniques apply to both
- Testing frameworks can be shared
- Documentation structure similar
- Recursive bootstrap methodology

**Coordination Points**:
1. Share optimization techniques
2. Cross-pollinate testing approaches
3. Unified documentation style
4. Common performance targets
5. Shared execution framework

---

## 🚦 Status Signals

### Instance Status Codes
- 🟢 **Active**: Currently executing
- 🟡 **Waiting**: Blocked/dependencies
- 🔵 **Handoff**: Ready to transfer
- ⚪ **Available**: Ready for new task
- 🔴 **Error**: Needs attention

### Task Priority Codes
- 🔥 **Urgent**: User-requested, blocking
- ⚡ **High**: Critical path
- 📋 **Normal**: Planned work
- 💡 **Nice-to-have**: Improvements
- 🧪 **Experimental**: R&D

---

## 🔄 Sync Protocol

### Every 30 Minutes
1. Read `CLAUDE_STATE.json`
2. Update your instance status
3. Check for messages/handoffs
4. Adjust priorities if needed

### Every Commit
1. Update state with changes
2. Use proper commit format
3. Note any coordination needs

### Every Handoff
1. Create handoff document
2. Update state completely
3. Commit all work
4. Mark task complete

---

## 💬 Example Communication Flow

### Scenario: CP1 Completes Testing Infrastructure

**CP1 Actions**:
```bash
# 1. Update state
echo '{
  "instance_id": "CP1",
  "status": "handoff",
  "current_task": "Testing infrastructure complete",
  "next_handoff": "Exchange data connectors"
}' > CLAUDE_STATE.json

# 2. Create handoff
cat > HANDOFF_CP1_testing_20251124.md << EOF
# Handoff: Testing Infrastructure Complete

## What Was Done
- Created test fixtures (200+ lines)
- Wrote 26 unit tests (92% passing)
- Set up pytest-cov

## What's Next
- Fix 2 failing tests (data tuning)
- Add 24 more tests (target: 50 total)
- Achieve 90% coverage

## Files Modified
- tests/fixtures/market_data.py
- tests/unit/test_optimized_patterns.py

## How to Continue
1. Run: pytest tests/ -v --cov
2. Review failing tests in test_optimized_patterns.py
3. Adjust fixtures in market_data.py
EOF

# 3. Commit
git commit -m "[CP1→Available] handoff: Testing infrastructure ready for expansion"

# 4. Mark available
# State file shows: "available_for_handoff": true
```

**CP2C3 Actions** (if picking up):
```bash
# 1. Read state
cat CLAUDE_STATE.json

# 2. Read handoff
cat HANDOFF_CP1_testing_20251124.md

# 3. Claim task
echo '{
  "instance_id": "CP2C3",
  "status": "active",
  "current_task": "Testing infrastructure expansion",
  "claimed_from": "CP1"
}' > CLAUDE_STATE.json

# 4. Continue work
pytest tests/ -v --cov
# [Fix tests, add more...]
```

---

## 🎓 Learning & Adaptation

### Cross-Instance Learning
- Each instance documents discoveries
- Optimization techniques shared
- Best practices propagated
- Mistakes noted to avoid repetition

### Continuous Improvement
- Review coordination effectiveness
- Refine protocols as needed
- Optimize handoff process
- Reduce friction points

---

## 🚀 Quick Start

### For New Instance
1. Read `CLAUDE_STATE.json`
2. Review `COORDINATION_DASHBOARD.md`
3. Check handoff queue
4. Claim available task
5. Begin execution

### For Existing Instance
1. Update state regularly
2. Use proper commit formats
3. Create handoffs when needed
4. Keep dashboard current

---

## 📈 Success Metrics

### Coordination Quality
- Handoff clarity (subjective)
- Zero duplicate work
- Minimal conflicts
- Fast context transfer

### Execution Efficiency
- Parallel speedup factor
- Throughput (tasks/hour)
- Quality maintained
- User satisfaction

---

## 🎯 Current State (Example)

**Active**: 2 instances
**Repositories**: crypto-pattern-recognition, consciousness-revolution
**Coordination Mode**: Independent parallel
**Status**: 🟢 All systems operational

---

**Version**: 1.0
**Last Updated**: 2025-11-24
**Protocol Status**: ACTIVE ✅

---

*This protocol enables autonomous Claude instances to work together seamlessly, maximizing productivity and minimizing conflicts. Update as needed based on real-world usage.*
