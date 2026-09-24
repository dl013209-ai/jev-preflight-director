#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jev_orchestrator.py - Jev 2.2.0 Full-Lifecycle Cognitive Orchestrator
Open-Source Edition (Strictly Desensitized)
Features:
- Stage 0 to Stage 4 full lifecycle execution (< 1ms latency)
- Dynamic evaluation counter (`eval_count`) for transparent decision reporting
- Universal 4-Step Blueprint and safety guard preloader
- Destructive action gate & Quote freshness window
- Staging buffer integration for continuous semantic distillation
"""

import os
import re
import time
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from .preloader import calculate_dynamic_confidence, prefetch_task_assets
except ImportError:
    from preloader import calculate_dynamic_confidence, prefetch_task_assets

class JevFullOrchestrator:
    """
    Lightweight, deterministic preflight orchestrator for LLM Agent systems.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else None

    def orchestrate_turn(self, query: str, history_len: int = 0, current_tokens: int = 0) -> Dict[str, Any]:
        t0 = time.time()
        q = str(query or "").strip()

        # Dynamic decision counter (eval_count) starts with 5 baseline dimensions
        eval_count = 5

        # ==========================================
        # Stage 0: Input Debounce & Pivot Interrupt
        # ==========================================
        collision_action = "NORMAL_PROCEED"
        collision_desc = "Standard forward request"

        if re.search(r"^(不对|别算了|算错了|换成|先不要|停一下|重来|撤回|stop|wait|cancel|wrong)", q, re.I):
            collision_action = "PIVOT_INTERRUPT"
            collision_desc = "User override / pivot interrupt: prune obsolete branches immediately"
            eval_count += 2
        elif re.search(r"^(顺便|另外|再查一下|格式改成|对了|还有个事|by the way|also)", q, re.I):
            collision_action = "SOFT_APPEND"
            collision_desc = "Incremental task append: merge without context disruption"
            eval_count += 1
        elif len(q) < 8 and not re.search(r"[。？！\?!]$", q) and re.search(r"(然后|还有|那个|就是)", q):
            collision_action = "DEBOUNCE_BUFFER"
            collision_desc = "Fragment buffering detected: awaiting complete input"
            eval_count += 1

        # ==========================================
        # Stage 1: Domain Intent & Memory Addressing
        # ==========================================
        domain = "General"
        topic = "general_qa"
        memory_tags: List[str] = []
        is_t0 = True

        # Check local learned patterns first if db available
        matched_learned = None
        if self.db_path and self.db_path.exists():
            try:
                conn = sqlite3.connect(self.db_path, timeout=1.0)
                cur = conn.cursor()
                hits = cur.execute(
                    "SELECT pattern, domain, topic FROM jev_learned_patterns ORDER BY weight DESC LIMIT 50"
                ).fetchall()
                conn.close()
                for pat, d, top in hits:
                    if pat in q:
                        matched_learned = (d, top)
                        eval_count += 2
                        break
            except Exception:
                pass

        if matched_learned:
            domain, topic = matched_learned
            memory_tags = [domain]
        elif re.search(r"(诉讼|答辩|起诉|质证|法官|开庭|利息|息费|违约金|案号|合规|传票|调解|legal|law|court)", q, re.I):
            domain = "Legal"
            topic = "litigation_and_advocacy"
            memory_tags = ["legal_evidence", "court_records", "statutory_defense"]
            eval_count += 3
        elif re.search(r"(报价|单价|专票|运费|螺栓|螺母|法兰|镀锌|投标|对账|供应商|采购|procurement|rfq|hardware)", q, re.I):
            domain = "Commerce"
            topic = "commercial_pricing_and_rfq"
            memory_tags = ["vendor_catalog", "tax_and_shipping", "commercial_profile"]
            eval_count += 3
        elif re.search(r"(mac|cpu|gpu|memory|gateway|patch|plugin|proxy|script|cron|port|ops|docker|进程|卡顿)", q, re.I):
            domain = "SystemOps"
            topic = "infrastructure_and_runtime"
            memory_tags = ["runtime_telemetry", "host_performance", "routing_policy"]
            eval_count += 2
        elif re.search(r"(浏览器|网页|抓取|爬虫|dom|cookie|browser|scrape)", q, re.I):
            domain = "BrowserAutomation"
            topic = "browser_and_web_flow"
            memory_tags = ["web_automation", "captcha_guard"]
            eval_count += 2
        else:
            if re.search(r"(那个|上面的|刚才|接着|按这个|那笔|这件事|that|above|previous)", q, re.I):
                domain = "ContextTrace"
                topic = "anaphora_resolution"
                memory_tags = ["recent_business_context"]
                eval_count += 1

        # Dynamic confidence scoring
        dyn_conf = calculate_dynamic_confidence(q, domain)
        confidence = dyn_conf["confidence"]
        gate_status = dyn_conf["tier"]
        eval_count += 1

        # ==========================================
        # Stage 2: Universal Preloader & Safety Injection
        # ==========================================
        preloaded_assets = prefetch_task_assets(domain, q)
        blueprint_text = preloaded_assets.get("blueprint", "")
        safety_rails = preloaded_assets.get("safety_guards", [])
        recommended_tools = preloaded_assets.get("recommended_tools", [])
        eval_count += len(safety_rails)

        prompt_injection = (
            f"【Jev 2.2 Task Preloader · Universal 4-Step Blueprint】\n"
            f"=== [Domain: {domain}] ===\n"
            f"{blueprint_text}\n"
            f"=== [Absolute Safety Rails] ===\n" +
            "\n".join([f"- {r}" for r in safety_rails]) + "\n" +
            f"=== [Recommended Tools] ===: {', '.join(recommended_tools)}\n"
            f"【Execution Rule】: Grounded execution with zero hallucination.\n"
        )

        # ==========================================
        # Stage 3: Dynamic Skill & MCP Scoping
        # ==========================================
        activated_skills = []
        allowed_mcps = []

        if domain == "Legal":
            activated_skills = ["legal-issue-research"]
            allowed_mcps = ["legal-hub"]
            eval_count += 2
        elif domain == "Commerce":
            activated_skills = ["hardware-quote-item-analysis"]
            allowed_mcps = []
            eval_count += 2
        elif domain == "SystemOps":
            activated_skills = ["mac-performance-tuning"]
            allowed_mcps = ["macctl"]
            eval_count += 2
        elif domain == "BrowserAutomation":
            activated_skills = ["ego-browser"]
            allowed_mcps = []
            eval_count += 1

        browser_gate = {
            "enabled": True,
            "captcha_intercept": True,
            "rule": "Drop execution to human on captchas/auth gates to prevent loop spins."
        }

        # ==========================================
        # Stage 4: Session Compaction & Skeleton Lock
        # ==========================================
        compression_action = "PASS_THROUGH"
        keep_turns = 2
        eval_count += 1

        if collision_action == "PIVOT_INTERRUPT":
            keep_turns = 0
            compression_action = "FORCE_RESET"
            eval_count += 1
        elif domain == "General":
            keep_turns = 0
            compression_action = "DROP_HISTORY"

        latency_ms = (time.time() - t0) * 1000

        return {
            "version": "2.2.0",
            "eval_count": eval_count,
            "stage_0_debounce": {
                "action": collision_action,
                "desc": collision_desc
            },
            "stage_1_preflight": {
                "domain": domain,
                "topic": topic,
                "confidence": confidence,
                "gate_status": gate_status,
                "is_t0": is_t0
            },
            "stage_2_memory_and_files": {
                "memory_tags": memory_tags,
                "prompt_injection": prompt_injection,
                "recommended_tools": recommended_tools
            },
            "stage_3_skills_and_tools": {
                "activated_skills": activated_skills,
                "allowed_mcps": allowed_mcps,
                "browser_gate": browser_gate
            },
            "stage_4_compression": {
                "action": compression_action,
                "keep_turns": keep_turns
            },
            "perf": {
                "preflight_latency_ms": round(latency_ms, 3)
            }
        }
