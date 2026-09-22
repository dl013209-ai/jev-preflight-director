# Jev Preflight Director 2.0

High-speed, zero-overhead preflight director, dynamic skill/tool router, and context compaction orchestrator for LLM Agent systems.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Latency](https://img.shields.io/badge/Preflight%20Latency-%3C%201ms-brightgreen.svg)](#performance)
[![Context Compaction](https://img.shields.io/badge/Context%20Pruning-Adaptive-orange.svg)](#features)

## What It Does

`Jev Preflight Director 2.0` intercepts inbound user requests before heavy model inference, executing deterministic local heuristics and structured classification in `< 1ms`:

1. **Stage 0: Input Debouncing & Pivot Interruption**  
   Detects user overrides (`"stop"`, `"wait"`, `"recalculate"`) and drops obsolete branches instantly.
2. **Stage 1: Intent Gating & Address Scoping**  
   Routes domains with strict 3-tier confidence gating (`>=0.85` high auto-gate, `0.70-0.84` soft recommendation, `<0.70` fail-open).
3. **Stage 2: Memory Gating & File Radar**  
   Prevents full-database memory scanning on casual chat; extracts domain-specific entity anchors.
4. **Stage 3: Dynamic Skill & MCP Scoping**  
   Limits loaded tools to `<= 2` per turn (< 1,000 tool payload tokens), eliminating model hallucination.
5. **Stage 4: Adaptive Context Compaction & Skeleton Preservation**  
   Implements 3-tier context management (<30k lightweight pruning, 30k-80k structured summarization, >80k session splitting) with hard-locking for statutory IDs, exact prices, and overriding directives.

## Architecture

```
User Message
   │
   ▼
[Stage 0: Debounce & Pivot Interruption] (0.01ms)
   │
   ▼
[Stage 1: Domain Intent & Memory Addressing] (0.50ms)
   │
   ▼
[Stage 2: Memory Gating & Fact Anchors] (0.20ms)
   │
   ▼
[Stage 3: Dynamic Skill & MCP Scoping] (0.20ms)
   │
   ▼
[Stage 4: Session Compaction & Skeleton Locking] (0.10ms)
   │
   ▼
To Execution LLM (Gemini / Claude / DeepSeek)
```

## Quick Start

```python
from jev.orchestrator import JevFullOrchestrator

orchestrator = JevFullOrchestrator()
res = orchestrator.orchestrate_turn("Draft a formal contract counter-argument", history_len=5, current_tokens=15000)

print("Domain:", res["stage_1_preflight"]["domain"])
print("Active Skills:", res["stage_3_skills_and_tools"]["activated_skills"])
print("Prune Decision:", res["stage_4_compression"]["action"], "Keep turns:", res["stage_4_compression"]["keep_turns"])
```

## License

MIT License.
