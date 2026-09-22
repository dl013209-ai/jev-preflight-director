#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jev_orchestrator.py - Jev 2.0 Full-Lifecycle Preflight Orchestrator
Open-Source Edition (Strictly Desensitized)
"""

import os
import re
import time
from typing import Dict, Any, List, Optional

class JevFullOrchestrator:
    """
    Lightweight, low-latency preflight orchestrator for LLM Agent workflows.
    Executes Stage 0 to Stage 4 in under 1ms on local hardware.
    """
    def __init__(self):
        pass

    def orchestrate_turn(self, query: str, history_len: int = 0, current_tokens: int = 0) -> Dict[str, Any]:
        t0 = time.time()
        q = str(query or "").strip()

        # Stage 0: Input Debounce & Pivot Interrupt
        collision_action = "NORMAL_PROCEED"
        collision_desc = "Standard forward request"

        if re.search(r"^(不对|别算了|算错了|换成|先不要|停一下|重来|撤回|stop|wait|cancel)", q, re.I):
            collision_action = "PIVOT_INTERRUPT"
            collision_desc = "User override / pivot interrupt: prune obsolete branches immediately"
        elif re.search(r"^(顺便|另外|再查一下|格式改成|对了|还有个事|by the way|also)", q, re.I):
            collision_action = "SOFT_APPEND"
            collision_desc = "Incremental task append: merge without context disruption"
        elif len(q) < 8 and not re.search(r"[。？！\?!]$", q) and re.search(r"(然后|还有|那个|就是)", q):
            collision_action = "DEBOUNCE_BUFFER"
            collision_desc = "Fragment buffering detected: awaiting complete input"

        # Stage 1: Domain Intent & Pre-Memory Address Scope
        domain = "general_chat"
        topic = "general_qa"
        confidence = 0.90
        memory_tags = []

        if re.search(r"(诉讼|答辩|起诉|质证|法官|开庭|利息|息费|违约金|案号|合规|传票|调解|legal|law|court)", q, re.I):
            domain = "legal_defense"
            topic = "litigation_and_advocacy"
            confidence = 0.96
            memory_tags = ["legal_evidence", "court_records", "statutory_defense"]
        elif re.search(r"(报价|单价|专票|运费|螺栓|螺母|法兰|镀锌|投标|对账|供应商|采购|procurement|rfq|hardware)", q, re.I):
            domain = "procurement_bid"
            topic = "commercial_pricing_and_rfq"
            confidence = 0.95
            memory_tags = ["vendor_catalog", "tax_and_shipping", "commercial_profile"]
        elif re.search(r"(大乐透|双色球|快乐8|彩票|前区|后区|冷号|遗漏|旋转矩阵|lottery|probability)", q, re.I):
            domain = "data_probability"
            topic = "number_matrix_analysis"
            confidence = 0.98
            memory_tags = ["matrix_coverage", "historical_stats"]
        elif re.search(r"(mac|cpu|gpu|memory|gateway|patch|plugin|proxy|script|cron|port|ops|docker)", q, re.I):
            domain = "system_ops"
            topic = "infrastructure_and_runtime"
            confidence = 0.92
            memory_tags = ["runtime_telemetry", "host_performance", "routing_policy"]
        else:
            if re.search(r"(那个|上面的|刚才|接着|按这个|那笔|这件事|that|above|previous)", q, re.I):
                domain = "context_trace"
                topic = "anaphora_resolution"
                confidence = 0.75
                memory_tags = ["recent_business_context"]

        # Confidence Gate
        if confidence >= 0.85:
            gate_status = "HIGH_CONFIDENCE_AUTO"
        elif 0.70 <= confidence < 0.85:
            gate_status = "MEDIUM_CONFIDENCE_SOFT"
        else:
            gate_status = "LOW_CONFIDENCE_FAIL_OPEN"
            domain = "general_chat"

        # Stage 2: Memory Gating
        need_memory_recall = bool(memory_tags and domain != "general_chat")

        # Stage 3: Dynamic Skill & MCP Scoping
        activated_skills = []
        allowed_mcps = []
        if domain == "legal_defense":
            activated_skills = ["legal-issue-research", "statutory-brief"]
            allowed_mcps = ["legal-hub"]
        elif domain == "procurement_bid":
            activated_skills = ["hardware-quote-analysis", "commercial-profile"]
            allowed_mcps = []
        elif domain == "data_probability":
            activated_skills = ["lottery-matrix", "probability-stepped-filter"]
            allowed_mcps = []
        elif domain == "system_ops":
            activated_skills = ["system-performance-tuning", "account-ops"]
            allowed_mcps = ["macctl"]

        # Stage 4: Session Compaction & Context Pruning
        if collision_action == "PIVOT_INTERRUPT":
            keep_turns = 0
            prune_reason = "Pivot interrupt: drop obsolete conversation branches"
        elif domain == "general_chat":
            keep_turns = 0
            prune_reason = "Zero conversation history needed for casual chat"
        elif re.search(r"(刚才|上面|按照这个|再算|接着|那笔|that|previous)", q, re.I):
            keep_turns = 3
            prune_reason = "Preserve historical facts and pronouns"
        else:
            keep_turns = 2
            prune_reason = "Standard two-turn business context"

        if current_tokens > 80000:
            compression_action = "FORCE_SESSION_SPLIT"
        elif current_tokens > 30000:
            compression_action = "STRUCTURED_SUMMARY"
        else:
            compression_action = "LIGHTWEIGHT_PRUNING"

        skeleton_preservation = [
            "Exact numerical amounts, unit prices, and tax rates",
            "Statutory case IDs and legal party names",
            "User pivot/override instructions",
            "Hardware/material engineering specifications"
        ]

        elapsed_ms = round((time.time() - t0) * 1000, 2)

        return {
            "elapsed_ms": elapsed_ms,
            "stage_0_debounce": {
                "action": collision_action,
                "desc": collision_desc
            },
            "stage_1_preflight": {
                "domain": domain,
                "topic": topic,
                "confidence": confidence,
                "gate_status": gate_status
            },
            "stage_2_memory_and_files": {
                "need_memory_recall": need_memory_recall,
                "memory_tags": memory_tags
            },
            "stage_3_skills_and_tools": {
                "activated_skills": activated_skills,
                "allowed_mcps": allowed_mcps
            },
            "stage_4_compression": {
                "action": compression_action,
                "keep_turns": keep_turns,
                "prune_reason": prune_reason,
                "skeleton_preservation": skeleton_preservation
            }
        }
