# Jev Preflight Director 2.4.0

**High-speed preflight routing, task preloading, and autonomous cognitive operating system for production LLM Agents.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Latency](https://img.shields.io/badge/Preflight%20Latency-%3C%200.2ms-brightgreen.svg)](#performance)
[![Dynamic Eval Count](https://img.shields.io/badge/Decisions-Transparent-blue.svg)](#architecture)
[![Autonomous Distillation](https://img.shields.io/badge/Cache%20Evolution-Daily%20Cron-orange.svg)](#semantic-distillation)

---

## 🌟 What's New in v2.4.0 (Production Hardening & Typography Governance)

1. **Pre-Work-Post Tool-Mirroring Contract (`三账合一与工具顺位绝对映射铁律`)**  
   - **Phase 1 Pre-flight Alignment (`# 0`)**: Structurally outlines execution targets strictly indexed by planned tool execution order (`## 一、 第一顺位工具计划：调度 [工具A]`).
   - **Phase 2 Work Execution (`# 1`)**: Executes core operations mirror-mapped to the declared tool sequence (`## 一、 调用 [工具A] 工具：[...]`).
   - **Phase 3 Machine Verification Bill (`# 2`)**: Emits grounded machine verification with real `exit 0` assertions under identical tool categories (`## 一、 第一顺位核验：[工具A]`).

2. **Five-State Standard Badge Dictionary (`五态核验标准徽章字典`)**  
   Strict state assertions across all verification bills:
   - `✅` [Completed / Pass]: Tool-verified with hard evidence (`exit 0`, original document extracted).
   - `⛔` [Blocked / Fail]: Execution error, 403 / timeout, or unfulfilled target.
   - `⏳` [Pending Approval / Blocked by Safety Guard]: Plans ready, waiting for explicit user approval due to physical redlines.
   - `🔄` [In-Progress / Background Worker]: Asynchronous long-running jobs (benchmark, batch download).
   - `⏭️` [Exempt / Skipped]: Hit local T0/T1 cache or safely bypassed.

3. **Thread-Safe Global Lifecycle Counter (`jev_context.py`)**  
   Upgraded from thread-isolated `contextvars.ContextVar` to a thread-safe singleton accumulator (`threading.Lock`). Subagents, async background threads, and multi-turn tools now 100% aggregate their real decision counts into the global gateway telemetry (`· 判断X次 ·`).

4. **Feishu Single-Card Native Collapsible Rail (V2 Preparation)**  
   Hardened adapter and runner bindings to collapse multi-step tool progress into clean, ordered card layouts, completely eliminating disordered floating bubble spam.

---

## 🌟 What's New in v2.2.0

1. **Universal 4-Step Cognitive Operating Framework (`preloader.py`)**  
   Preloads structured problem-solving blueprints before LLM inference:
   - **Step 1: Symptom & Problem Framing**
   - **Step 2: Strategic Direction**
   - **Step 3: Pointed Tool Scoping**
   - **Step 4: Grounded Verification (Tri-Source Verification)**

2. **Injected Message Pipeline (KV-Cache Friendly)**  
   Mounts task-specific assets, statutory anchors, and safety constraints directly into the user message context (`injected_message`). **Zero perturbation to global System Prompts, ensuring 100% prompt cache hit rates.**

3. **Autonomous Semantic Distiller (`distiller.py`)**  
   Solves heuristic regex rigidity through continuous learning:
   - Live query buffer staging (`jev_semantic_staging`)
   - Daily automated clustering and entity extraction
   - Zero-overhead local pattern compilation into SQLite WAL cache
   - Automated pruning of 30-day cold patterns

4. **Multi-Model Conformance Verified**  
   Benchmarked across **Gemini 3.8 Flash, DeepSeek-v4-flash, and GLM-5.1**. Reasoning traces confirm that LLMs treat preloaded safety rails as strict constraints.

5. **Transparent Execution Telemetry (`eval_count`)**  
   Dynamically aggregates decision dimensions (7 to 16 evaluations per turn) for real-time dashboard observability.

---

## 🏗️ Architecture

```text
Inbound User Request
        │
        ▼
[Stage 0: Input Debounce & Pivot Interrupt] (0.01ms)
  ├── Drops stale execution branches on user override ("wait", "wrong")
  └── Buffers fragmented voice/mobile inputs
        │
        ▼
[Stage 1: Intent Gating & Learned Pattern Matching] (0.05ms)
  ├── T0 Local SQLite Cache & Learned Patterns (< 0.1ms)
  └── Fail-open / T1 Semantic Escalation fallback
        │
        ▼
[Stage 2: Universal Task Preloader & Safety Injection] (0.05ms)
  ├── Mounts 4-Step Lifecycle Blueprint
  ├── Destructive Action Gate (kill/rm/reboot user-approval guard)
  └── Quote Freshness Window & Ground-Truth Verification
        │
        ▼
[Stage 3: Dynamic Skill & MCP Scoping] (0.02ms)
  ├── Whitelists <= 2 high-signal tools per turn (<1,000 token payload)
  └── DOM Captcha Interceptor (prevents runaway browser loops)
        │
        ▼
[Stage 4: Session Compaction & Skeleton Preservation] (0.01ms)
  ├── Reset on Pivot: Prunes stale hypotheses immediately
  └── Immutable skeleton preservation (contract amounts, statutory IDs)
        │
        ▼
Deliver to Execution LLM (Gemini / DeepSeek / Claude / GLM)
```

---

## ⚡ Performance Benchmarks

Measured on local hardware (macOS / Python 3.11):

| Scenario | Raw Heuristics / Network | Jev 2.2.0 Preloaded | Speedup | Decision Depth |
| :--- | :---: | :---: | :---: | :---: |
| **System Operations & Diagnostics** | 3,355 ms | **3.99 ms** | **⚡ 840x** | 15 evals |
| **Web & Browser Automation** | 1,464 ms | **0.85 ms** | **⚡ 1,700x** | 8 evals |
| **Dispute Defense & Legal Framing** | 0.17 ms | **0.12 ms** | **⚡ Real-time** | 16 evals |
| **Procurement & Price Calculation** | 0.23 ms | **0.07 ms** | **⚡ Real-time** | 15 evals |
| **Hardware & OS Host Control** | 2.10 ms | **0.04 ms** | **⚡ Real-time** | 14 evals |

---

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/dl013209-ai/jev-preflight-director.git
cd jev-preflight-director
pip install -e .
```

### 2. Zero-Config & API Setup

This engine works completely **out of the box with zero external configuration**:
- **Default Tier (Zero-Key)**: Automatically connects to TypeSafe's public community pool (`https://classifier.dev/`) without requiring an API key.
- **Local Cache Tier**: Built-in 0ms SQLite local pattern caching with autonomous distillation.
- **Fail-Open Safe**: Gracefully falls back to raw prompt execution if the network times out (>1.2s).

**Optional API Acceleration:**
If you have private dedicated endpoints or commercial keys, configure your environment:
```bash
# Option 1: Dedicated TypeSafe / Jev Auth Token
export JEV_AUTH_TOKEN="your_jev_auth_token"

# Option 2: OpenRouter Decisions Gateway
export OPENROUTER_API_KEY="sk-or-v1-xxxx"

# Option 3: Custom Self-Hosted / Private Jev Endpoint
export JEV_API_ENDPOINT="https://your-custom-endpoint.com/api"
```

### 3. Basic Turn Orchestration

```python
from jev.orchestrator import JevFullOrchestrator

orchestrator = JevFullOrchestrator()
turn = orchestrator.orchestrate_turn("Check runaway CPU processes on host machine")

print(f"Version: {turn['version']}")
print(f"Domain: {turn['stage_1_preflight']['domain']}")
print(f"Decisions Evaluated: {turn['eval_count']}")
print(f"Preflight Latency: {turn['perf']['preflight_latency_ms']} ms")
print(f"Recommended Tools: {turn['stage_2_memory_and_files']['recommended_tools']}")
```

### 3. Continuous Semantic Distillation

Run periodic distillation to compile live query patterns into zero-latency local rules:

```python
from jev.distiller import SemanticDistiller

distiller = SemanticDistiller(db_path="cache.sqlite")
report = distiller.distill(max_samples=500)
print(report)
```

---

## 🛡️ Safety Rail Design

- **Destructive Action Gate**: Any destructive operation (`rm`, `kill`, `format`, `dd`) is trapped by preloaded assertions, requiring explicit operator sign-off before invocation.
- **Quote Freshness Standard**: Commercial pricing queries enforce itemized cost formulas (base cost + statutory VAT + destination freight) with explicit expiration windows.
- **Tri-Source Verification**: Demands verifiable ground-truth evidence (exit codes, physical file paths, primary statute IDs) rather than self-referential model claims.

---

## 📄 License

MIT License. Developed & maintained by `dl013209-ai`.
