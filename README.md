# Jev Preflight Director (Jev 2.0)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **An ultra-fast (<1ms) System One pre-flight gateway & director for LLM Agents.**  
> Pre-classifies user intent, prunes context dynamically to save 70%~90% input tokens, arbitrates streaming interrupts, plans search decomposition, and gates vision/OCR tiers.

---

## 🌟 Key Features

1. **Sub-millisecond Intent Profiling (`< 1ms`)**: Categorizes conversation into domains (B2B, Legal, Analytics, DevOps, Chat) before invoking heavy LLMs.
2. **Selective Memory Gating**: Gates long-term memory recall and retention. Suppresses trivial chit-chat/commands to protect Prompt Cache hits and prevent memory pollution.
3. **Dynamic Context Pruning**: Eliminates up to 90% of redundant history tokens while preserving active business entity anchors and pronoun references.
4. **Turn Collision & Interrupt Arbitration**: Distinguishes between hard overrides (abort current generation immediately), soft appends (queue to end of turn), and debounced input fragments.
5. **Search Planning & Decomposition**: Determines real-time search necessity, binds search origin channels (judicial, b2b, realtime news), and splits queries concurrently.
6. **Tiered Vision & OCR Guard**: Intercepts dense document scans via local OCR (0 Vision Token consumption) and detects bounding boxes for seals/signatures.
7. **Plain English Error Triage**: Classifies 401/403/429/500 faults into actionable diagnostics instead of silent drops.

---

## 🚀 Quick Start

```python
from jev.preflight import JevPreflightDirector

director = JevPreflightDirector()

# Classify incoming turn
result = director.classify_turn(
    "Check the latest market wholesale quote for M8 galvanized hex bolts",
    history_len=3
)

print(result)
# Output:
# {
#   'elapsed_ms': 0.12,
#   'domain': 'B2B & Procurement',
#   'collision': 'NORMAL_PROCEED',
#   'keep_turns': 2,
#   'need_search': True,
#   'search_origin': 'b2b_market',
#   'search_queries': ['M8 galvanized hex bolts wholesale quote'],
#   'mcp_quota': []
# }
```

---

## 📄 Architecture Overview

```text
[Incoming Message] ──▶ [Jev Preflight (<1ms)] ──┬──▶ [Context Pruning: Keep 0/2 turns]
                                                ├──▶ [Search Planning: 1~3 concurrent queries]
                                                ├──▶ [Vision Guard: OCR vs. Vision LLM]
                                                └──▶ [Active Entity Tracking Anchor]
```

---

## 📜 License

Distributed under the MIT License.
