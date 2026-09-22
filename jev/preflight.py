#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jev Preflight Director - Core Engine (Sanitized for Open-Source Release)
"""

import os
import re
import time
import json
import sqlite3
from typing import Dict, List, Any, Optional

PRUNING_PASS_REGEX = re.compile(
    r"(刚才|上面|这个|那个|接着|继续|按照|第二条|上文|之前|他说的|按这个|那笔|那项|这笔|重新算|加上去|算进去|that|previous|above|continue)"
)

TOPIC_PATTERNS = {
    "procurement": {
        "regex": re.compile(r"(五金|螺栓|螺母|镀锌|法兰|采购|专票|报价|单价|运费|清单|询价|procurement|rfq|quote|hardware)"),
        "domain": "商贸采购 (B2B)",
        "topic": "核算与报价"
    },
    "litigation": {
        "regex": re.compile(r"(法官|起诉|答辩|质证|和解|征信|自认|管辖|法条|开庭|合同纠纷|law|court|litigation|case)"),
        "domain": "法律合规 (Legal)",
        "topic": "维权与诉讼攻防"
    },
    "analytics": {
        "regex": re.compile(r"(概率|走势|大盘|注单|形态|冷热|遗漏|数据分析|统计|analytics|statistics|lottery)"),
        "domain": "数据推演 (Analytics)",
        "topic": "形态与矩阵分析"
    },
    "devops": {
        "regex": re.compile(r"(mac|xray|vps|router|token|api|补丁|插件|网关|运维|部署|报错|devops|infra|gateway)"),
        "domain": "系统运维 (DevOps)",
        "topic": "架构与环境治理"
    }
}

class JevPreflightDirector:
    def __init__(self, cache_db_path: Optional[str] = None):
        self.cache_db = cache_db_path or os.path.expanduser("~/.jev_cache.sqlite")
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.cache_db)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS preflight_cache (
                    query_hash TEXT PRIMARY KEY,
                    domain TEXT,
                    topic TEXT,
                    keep_turns INTEGER,
                    created_at REAL
                )
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass

    def classify_turn(self, query: str, history_len: int = 0) -> Dict[str, Any]:
        """Preflight classification in < 1ms"""
        t0 = time.time()
        q = query.strip()

        # Collision detection
        if re.search(r"^(不对|别算了|换成|算错了|不是这个|先不要|stop|cancel|wait)", q):
            collision = "PIVOT_INTERRUPT"
        elif re.search(r"(顺便|另外|再查一下|格式改成|排成表格|对了|also|by the way)", q):
            collision = "SOFT_APPEND"
        elif len(q) < 8 and not re.search(r"[。？！?!]$", q):
            collision = "DEBOUNCE_BUFFER"
        else:
            collision = "NORMAL_PROCEED"

        # Domain classification
        matched_domain = "日常闲聊 (Chat)"
        matched_topic = "通用问答"
        for k, v in TOPIC_PATTERNS.items():
            if v["regex"].search(q):
                matched_domain = v["domain"]
                matched_topic = v["topic"]
                break

        # Context pruning logic
        if PRUNING_PASS_REGEX.search(q):
            keep_turns = 2
            prune_reason = "Pronoun or context dependency detected"
        elif matched_domain in ["商贸采购 (B2B)", "法律合规 (Legal)"] and history_len > 0:
            keep_turns = 2
            prune_reason = "Domain requires contextual consistency"
        elif matched_domain == "日常闲聊 (Chat)":
            keep_turns = 0
            prune_reason = "Independent chat, history pruned to save tokens"
        else:
            keep_turns = 1
            prune_reason = "Standard step transition"

        # Search planning
        need_search = False
        search_origin = "none"
        search_queries = []
        if re.search(r"(查一下|搜一下|最新|出来了没有|价格多少|法条|是多少|search|lookup|latest)", q):
            need_search = True
            search_origin = "general_web"
            search_queries = [q[:30]]

        elapsed_ms = (time.time() - t0) * 1000

        return {
            "elapsed_ms": round(elapsed_ms, 2),
            "collision": collision,
            "domain": matched_domain,
            "topic": matched_topic,
            "keep_turns": keep_turns,
            "prune_reason": prune_reason,
            "need_search": need_search,
            "search_origin": search_origin,
            "search_queries": search_queries[:3],
            "mcp_quota": []
        }
