#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jev_orchestrator.py - Jev 2.0 终极全链路调度中枢与会话压缩决策器
实现 Stage 0 ~ Stage 4 的完整全链路闭环，并对 Stage 5/6 输出标准化上下文参数。

核心能力：
1. Stage 0: 颠覆打断 / 增量追加 / 碎片防抖 (Local Debounce)
2. Stage 1: 前置门卫 1（意图粗定 + 记忆寻址器 + 三级置信度门禁）
3. Stage 2: 记忆提取门卫 (Hindsight Memory Gating) + 本地案卷雷达 (Local File Radar)
4. Stage 3: 后置校准 2（技能点将 Skill Gating + 工具精简 MCP Scoping + DOM 状态门卫）
5. Stage 4: 会话状态与智能压缩裁决 (Session Compression Gate + 骨架红线锁定)
"""

import os
import re
import time
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from .jev_task_preloader import (
        calculate_dynamic_confidence,
        prefetch_task_assets,
        is_system_generated_message,
    )
except ImportError:
    from jev_task_preloader import (
        calculate_dynamic_confidence,
        prefetch_task_assets,
        is_system_generated_message,
    )

logger = logging.getLogger("hermes.jev.orchestrator")

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
_CATALOG_PATH = os.path.join(_PLUGIN_DIR, "data", "skill_catalog.json")

# 本地案卷路径静态雷达映射表（无需调大模型，0ms 直接秒出真实路径）
LOCAL_FILE_RADAR_MAP = {
    "webank": {
        "keywords": ["微众", "7969", "朱继平", "质证点", "核实函"],
        "paths": [
            "/Users/xia/Desktop/诉讼案件/微众银行",
            "/Users/xia/Desktop/微众",
            "/Users/xia/.hermes/webank-7969-case.md"
        ]
    },
    "citic": {
        "keywords": ["中信", "37023", "信用卡", "西山法院", "管辖异议"],
        "paths": [
            "/Users/xia/Desktop/诉讼案件/中信银行",
            "/Users/xia/Desktop/中信"
        ]
    },
    "hardware_procurement": {
        "keywords": ["平米商贸", "专票", "法兰", "螺栓", "镀锌", "昆明运费", "五金", "报价"],
        "paths": [
            "/Users/xia/Desktop/投标报价",
            "/Users/xia/Desktop/平米商贸"
        ]
    },
    "lottery_data": {
        "keywords": ["大乐透", "双色球", "快乐8", "kl8", "前区", "后区", "开奖", "冷号"],
        "paths": [
            "/Users/xia/Desktop/彩票/大乐透",
            "/Users/xia/Desktop/彩票/双色球",
            "/Users/xia/Desktop/彩票/快乐8"
        ]
    }
}

class JevFullOrchestrator:
    def __init__(self):
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        if os.path.exists(_CATALOG_PATH):
            try:
                with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def orchestrate_turn(self, query: str, history_len: int = 0, current_tokens: int = 0) -> Dict[str, Any]:
        """
        全链路调度中枢总入口
        """
        t0 = time.time()
        q = str(query or "").strip()

        # ==========================================
        # Stage 0: 入站防抖与连续对话冲突判定 (Local Debounce)
        # ==========================================
        collision_action = "NORMAL_PROCEED"
        collision_desc = "正常业务流进"

        if re.search(r"^(不对|别算了|算错了|换成|先不要|停一下|重来|撤回|有问题|这不对|有错误)", q):
            collision_action = "PIVOT_INTERRUPT"
            collision_desc = "主人纠偏与打断，废弃旧推理并归零打捞物理证据"
        elif re.search(r"^(顺便|另外|再查一下|格式改成|对了|还有个事)", q):
            collision_action = "SOFT_APPEND"
            collision_desc = "增量追加指令，平滑合并任务"
        elif len(q) < 8 and not re.search(r"[。？！\?!]$", q) and re.search(r"(然后|还有|那个|就是)", q):
            collision_action = "DEBOUNCE_BUFFER"
            collision_desc = "检测到碎片半句，防抖缓冲合并"

        # ==========================================
        # Stage 1: 前置门卫 1（意图判定：全面砍掉死板 T0，直接直通 T1 官方免费池）
        # ==========================================
        domain = "日常闲聊"
        topic = "通用交流"
        confidence = 0.95
        memory_tags = []
        is_t0 = False

        if is_system_generated_message(q):
            domain = "系统通知"
            topic = "系统回执与告警（非主人业务指令）"
            confidence = 0.99
            memory_tags = []
        else:
            # 彻底废除本地死板 T0 规则与正则盲猜，全量直接调用 T1 官方公益池（每天 20,000 次免费）
            try:
                try:
                    from .jev_service import classify_items
                except ImportError:
                    from jev_service import classify_items
                labels = ["四案诉讼", "商贸投标", "彩票推演", "邮件资产", "电脑控制", "系统运维", "硬件与AI选型", "购物比价与平台寻找", "日常闲聊"]
                t1_res = classify_items(q, labels)
                if t1_res.get("status") == "success":
                    t1_label = t1_res.get("results", {}).get("label")
                    t1_conf = t1_res.get("results", {}).get("confidence", 0.90)
                    if t1_label:
                        domain = t1_label
                        topic = f"T1意图定性-{t1_label}"
                        confidence = t1_conf
                        if domain == "硬件与AI选型":
                            memory_tags = ["设备与软硬件", "模型选型", "本地大模型", "Mac配置"]
                        elif domain == "四案诉讼":
                            memory_tags = ["四案诉讼", "司法证据", "法官心证"]
                        elif domain == "商贸投标":
                            memory_tags = ["云南平米商贸", "五金报价打法", "13%专票运昆明"]
                        elif domain == "系统运维":
                            memory_tags = ["老Mac核显调优", "补丁治理", "10router路由"]
                        elif domain == "邮件资产":
                            memory_tags = ["邮件资产", "发票附件", "双邮箱轮询"]
                        elif domain == "电脑控制":
                            memory_tags = ["macOS宿主控制", "macctl工具链", "老Mac硬件守卫"]
                        elif domain == "彩票推演":
                            memory_tags = ["生活彩票", "18码矩阵"]
                        else:
                            memory_tags = [domain]
            except Exception as e:
                # 容灾兜底：仅在网络完全熔断时快速降级
                domain = "日常闲聊"
                topic = "轻量通用问答"
                confidence = 0.80

            # 自动沉淀入待整理池 (供夜间定时蒸馏反刍)
            try:
                db_file = Path("/Users/xia/.hermes/plugins/jev-fast-classifier/data/cache.sqlite")
                conn_stg = sqlite3.connect(db_file, timeout=1.0)
                cur_stg = conn_stg.cursor()
                cur_stg.execute(
                    "INSERT INTO jev_semantic_staging (raw_text, domain, topic, confidence, source, status, created_at) VALUES (?, ?, ?, ?, 't1_live', 'pending', ?)",
                    (q, domain, topic, confidence, time.time())
                )
                conn_stg.commit()
                conn_stg.close()
            except Exception:
                pass
            if not memory_tags:
                memory_tags = []

        # 动态置信度算法计算（替代生硬写死的 0.95/0.98）
        dyn_conf_info = calculate_dynamic_confidence(q, domain)
        confidence = dyn_conf_info["confidence"]
        gate_status = dyn_conf_info["tier"]

        # ==========================================
        # Stage 2: 任务先锋官资产预装 (Task Asset Prefetch) + 本地案卷雷达
        # ==========================================
        # 预取本地物理资产、真实目录与执行蓝图
        preload_res = prefetch_task_assets(q, domain, dyn_conf_info)
        discovered_paths = preload_res.get("discovered_paths", [])
        prompt_injection = preload_res.get("prompt_injection", "")
        recommended_tools = preload_res.get("recommended_tools", [])

        # 如果触发了主人的反悔/纠偏，强制注入归零复位与事实打捞指令
        if collision_action == "PIVOT_INTERRUPT":
            pivot_reset_notice = """
【Jev 2.0 归零复查熔断指令 (Reset on Pivot)】
- 触发原因：主人指出之前的内容存在疑问/错误/需要推倒重来；
- 行为纪律：严禁输出任何客套道歉、借口辩解与长篇自述；
- 执行动作：彻底抛弃上一轮推演假设，直接调取物理原文件/底层命令重新取证，出具【疑问点 vs 真实原件出处】的客观对账表！
"""
            prompt_injection = pivot_reset_notice + prompt_injection

        # 记忆提取门卫：仅对非闲聊且有记忆标签时放行记忆检索
        need_memory_recall = bool(memory_tags and domain != "日常闲聊")
        
        # 补充本地静态雷达
        if domain in ["四案诉讼", "商贸投标", "彩票推演"]:
            for key, radar_item in LOCAL_FILE_RADAR_MAP.items():
                if any(kw in q for kw in radar_item["keywords"]):
                    for p in radar_item["paths"]:
                        if os.path.exists(p) and p not in discovered_paths:
                            discovered_paths.append(p)

        # ==========================================
        # Stage 3: 后置校准 2（技能点将 Skill Gating + 工具精简 MCP Scoping）
        # ==========================================
        # A. 专属技能点将（闲聊 0 技能激活，彻底避免抢词）
        activated_skills = []
        if domain == "四案诉讼":
            activated_skills = ["case-citic-37023", "legal-issue-research", "xiachangmin-self"]
        elif domain == "商贸投标":
            activated_skills = ["hardware-quote-item-analysis", "xiachangmin-self"]
        elif domain == "彩票推演":
            activated_skills = ["dlt-v5-nexus", "lottery-matrix"]
        elif domain == "系统运维":
            activated_skills = ["google-account-ops", "mac-performance-tuning"]
        elif domain == "电脑控制":
            activated_skills = ["macos-host-control"]
        else:
            activated_skills = []

        # B. 工具白名单精简 (MCP Tool Scoping) —— 单轮不超过 2 个，定义控制在 1000 Token 内
        allowed_mcps = []
        if domain == "四案诉讼":
            allowed_mcps = ["legal-hub"]
        elif domain == "系统运维":
            allowed_mcps = ["macctl"]
        elif domain == "电脑控制":
            allowed_mcps = ["macctl"]
        else:
            allowed_mcps = []

        # C. 浏览器 DOM 状态门卫（防验证码卡死）
        browser_gate = {
            "enabled": True,
            "captcha_intercept": True,
            "rule": "DOM出现验证码/扫码登录立即0.01ms弹卡挂起，杜绝大模型盲目自旋与核显发热"
        }

        # ==========================================
        # Stage 4: 会话状态与智能压缩裁决 (Session Compressor Gate)
        # ==========================================
        compression_action = "PASS_THROUGH"
        keep_turns = 2
        prune_reason = "常规上下文保留"

        if collision_action == "PIVOT_INTERRUPT":
            keep_turns = 0
            prune_reason = "颠覆打断，清空历史分支"
        elif domain == "日常闲聊":
            keep_turns = 0
            prune_reason = "日常闲聊零历史，极致降耗"
        elif re.search(r"(刚才|上面|按照这个|再算|接着|那笔|那条)", q):
            keep_turns = 3
            prune_reason = "强保留关键指代词与案件数值"
        else:
            keep_turns = 2
            prune_reason = "标准业务双轮上下文"

        # 压缩阶梯判定
        if current_tokens > 80000:
            compression_action = "FORCE_SESSION_SPLIT" # 硬性分卷
        elif current_tokens > 30000:
            compression_action = "STRUCTURED_SUMMARY"  # 骨架提纯
        else:
            compression_action = "LIGHTWEIGHT_PRUNING" # 动态微修剪

        # 骨架红线约束（绝不压缩抹除）
        skeleton_preservation = [
            "涉案准确金额/投标单价/13%专票",
            "法定案号(7969/37023)与当事人姓名",
            "主人最新反悔与打断指令",
            "物料硬规格与参数"
        ]

        elapsed_ms = round((time.time() - t0) * 1000, 2)

        # 真实计算 Jev 全链路判定的具体问题与决策点总数 (Dynamic Decision Points)
        eval_count = 5  # 基础 5 维：防抖/领域/议题/置信度/门禁
        if memory_tags:
            eval_count += len(memory_tags)
        if discovered_paths:
            eval_count += len(discovered_paths)
        if recommended_tools:
            eval_count += len(recommended_tools)
        if prompt_injection:
            eval_count += 2  # 包含交付蓝图与安全红线核验
        if collision_action != "NORMAL_PROCEED":
            eval_count += 1  # 额外判定了策略碰撞/反悔打断
        if not is_t0:
            eval_count += 2  # 触发了 T1 深度语义多标签多维度辨析

        return {
            "elapsed_ms": elapsed_ms,
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
                "need_memory_recall": need_memory_recall,
                "memory_tags": memory_tags,
                "discovered_paths": discovered_paths[:3],
                "prompt_injection": prompt_injection
            },
            "stage_3_skills_and_tools": {
                "activated_skills": activated_skills[:2],
                "allowed_mcps": allowed_mcps[:2],
                "recommended_tools": recommended_tools,
                "browser_gate": browser_gate
            },
            "stage_4_compression": {
                "action": compression_action,
                "keep_turns": keep_turns,
                "prune_reason": prune_reason,
                "skeleton_preservation": skeleton_preservation
            }
        }

if __name__ == "__main__":
    orch = JevFullOrchestrator()
    sample_queries = [
        ("微众银行7969案，朱继平说的那个5万块钱方案拒绝答辩词起草一下", 12000),
        ("平米商贸报价：M12*30镀锌螺栓，带13%专票送昆明", 5000),
        ("不对，别算了，先看中信信用卡37023案", 35000),
        ("大乐透26095期，根据前区冷号打一组18码方案", 18000),
        ("今天昆明天气怎么样？", 1200),
        ("查一下Mac系统风扇转速和磁盘", 4000)
    ]
    print("=== Jev 2.0 终极全链路 Orchestrator 冒烟测试 ===")
    for sq, tokens in sample_queries:
        res = orch.orchestrate_turn(sq, history_len=3, current_tokens=tokens)
        print(f"\n[Query] {sq}")
        print(f"  -> 耗时: {res['elapsed_ms']}ms | 领域: {res['stage_1_preflight']['domain']} | 置信: {res['stage_1_preflight']['confidence']}")
        print(f"  -> 动作: {res['stage_0_debounce']['action']} | 技能: {res['stage_3_skills_and_tools']['activated_skills']} | MCP: {res['stage_3_skills_and_tools']['allowed_mcps']}")
        print(f"  -> 记忆标签: {res['stage_2_memory_and_files']['memory_tags']} | 案卷路径: {res['stage_2_memory_and_files']['discovered_paths']}")
        print(f"  -> 压缩决策: {res['stage_4_compression']['action']} (保留{res['stage_4_compression']['keep_turns']}轮, {res['stage_4_compression']['prune_reason']})")
