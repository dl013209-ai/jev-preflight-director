# -*- coding: utf-8 -*-
"""
jev-fast-classifier Hermes Plugin Entrypoint
"""

import sys
from pathlib import Path

_PLUGIN_DIR = Path(__file__).resolve().parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from jev_service import classify_items
from jev_context import record_jev_call
from jev_handoff import adjudicate_disputes
from jev_search import filter_search_results
from jev_skill_router import route_skills
from jev_autoroute import get_autoroute_state, set_autoroute_state
from jev_staffing import evaluate_task_complexity_and_staffing
from jev_lifecycle_guardian import handle_pre_tool_call, handle_transform_tool_result
from jev_context_engine import JevContextEngine

def register(ctx):
    """Register jev_classify, jev_handoff_adjudicate, jev_filter_search, and jev_route_skills into Hermes runtime."""
    
    # ---------------- 0. 上下文压缩引擎注册 (Jev Context Engine) ----------------
    if hasattr(ctx, "register_context_engine"):
        try:
            ctx.register_context_engine("jev-compressor", JevContextEngine)
        except Exception:
            pass

    # ---------------- 0. 全生命周期监护 Hooks (Pre-Tool & Transform-Result) ----------------
    if hasattr(ctx, "register_hook"):
        ctx.register_hook("pre_tool_call", handle_pre_tool_call)
        ctx.register_hook("transform_tool_result", handle_transform_tool_result)
    
    # ---------------- 5. 自动路由开关指令 /autoroute ----------------
    def _autoroute_cmd_handler(args, **kwargs):
        cmd = (args or "").strip().lower()
        if cmd in ("on", "enable", "start", "1"):
            set_autoroute_state(True)
            return "✅ Jev-Gemini 自动三档路由已【开启】\n- 闲聊/短问答 ➡️ flash-low (秒回)\n- 五金/算价/台账 ➡️ flash-medium (平衡算力)\n- 诉讼/卷宗/重案 ➡️ flash-high (深度推理)\n*(仅对 Gemini 套餐生效，非 Gemini 模型自动休眠)*"
        elif cmd in ("off", "disable", "stop", "0"):
            set_autoroute_state(False)
            return "🛑 Jev-Gemini 自动三档路由已【关闭】\n会话已严格锁死在当前默认模型，不再自动切换档位。"
        else:
            state = get_autoroute_state()
            status_text = "🟢 开启" if state.get("enabled", True) else "🔴 关闭"
            return f"📊 Jev-Gemini 自动路由当前状态: {status_text}\n可用指令：\n- `/autoroute on` : 开启动态三档路由\n- `/autoroute off` : 关闭并锁死当前模型\n- `/autoroute status` : 查看当前状态"

    if hasattr(ctx, "register_command"):
        ctx.register_command(
            name="autoroute",
            handler=_autoroute_cmd_handler,
            description="Jev Gemini 自动三档路由开关控制 (/autoroute on|off|status)"
        )
    
    # ---------------- 4. 技能两阶段智能路由器 jev_route_skills ----------------
    def _route_skills_handler(args, **kwargs):
        query = args.get("query", "")
        top_k = int(args.get("top_k", 3))
        import json
        res = route_skills(query, top_k=top_k)
        record_jev_call(assigned_model=None, is_fallback=False)
        return json.dumps(res, ensure_ascii=False)

    route_skills_schema = {
        "name": "jev_route_skills",
        "description": "基于 Jev System One 的两阶段技能路由器。当用户提出复杂/跨界需求或不确定该调用哪项技能时，输入指令，0.2秒两阶段（一级业务域+二级技能池）精准返回契合度最高的 1~3 项技能，避免 551 个技能抢词与闲聊乱触发。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用户的当前提问、需求或指令"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回推荐技能数量上限，默认 3"
                }
            },
            "required": ["query"]
        }
    }
    
    ctx.register_tool(
        name="jev_route_skills",
        toolset="jev",
        schema=route_skills_schema,
        handler=_route_skills_handler
    )
    
    # ---------------- 1. 原生基础分类器 jev_classify ----------------
    def _classify_handler(args, **kwargs):
        items = args.get("items") or args.get("item") or args.get("text")
        labels = args.get("labels", [])
        assigned = args.get("target_model") or args.get("assigned_model")
        
        if not items or not labels:
            return {"status": "error", "message": "Missing required parameters: items and labels"}
        res = classify_items(items, labels)
        
        # 自动识别结果中指派的模型（严格限定在 10router 白名单映射中，严防越权）
        assigned_model = assigned
        if not assigned_model and isinstance(res, dict):
            res_data = res.get("results")
            top_label = ""
            if isinstance(res_data, dict):
                top_label = res_data.get("label", "")
            elif isinstance(res_data, list) and res_data:
                top_label = res_data[0].get("label", "")
            
            # 白名单安全映射字典（严格锁死在 10router 5大合规模型内）
            ROUTING_WHITELIST = {
                "claude-opus": "ag/claude-4.6-opus",
                "claude-sonnet": "ag/claude-4.6-sonnet",
                "gemini-high": "ag/gemini-3.8-flash-high",
                "gemini-mid": "ag/gemini-3.8-flash-mid",
                "gemini-flash": "ag/gemini-3.8-flash-low",
                "gemini-low": "ag/gemini-3.8-flash-low",
            }
            top_lower = top_label.lower()
            for key, mapped in ROUTING_WHITELIST.items():
                if key in top_lower:
                    assigned_model = mapped
                    break
                
        is_fallback = bool(res.get("is_fallback", False) if isinstance(res, dict) else False)
        record_jev_call(assigned_model=assigned_model, is_fallback=is_fallback)
        import json
        return json.dumps(res, ensure_ascii=False)

    classify_schema = {
        "name": "jev_classify",
        "description": "基于 Jev-1.13.0 (System One) 的本地毫秒级极速分类器。用于批量物料打标、诉讼证据定性、彩票形态过滤、大模型选型路由等判断任务，单次0ms~60ms，零Token消耗。",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "待分类的一组文本（支持单条或几十条批量）"
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "候选分类标签列表"
                },
                "target_model": {
                    "type": "string",
                    "description": "可选：显式指定的候选或目标模型"
                }
            },
            "required": ["items", "labels"]
        }
    }

    ctx.register_tool(
        name="jev_classify",
        toolset="jev",
        schema=classify_schema,
        handler=_classify_handler
    )

    # ---------------- 2. 专家中途判断交接器 jev_handoff_adjudicate ----------------
    def _handoff_handler(args, **kwargs):
        disputes = args.get("disputes") or args.get("items") or []
        default_labels = args.get("default_labels") or args.get("labels")
        target_model = args.get("target_model")
        output_format = args.get("output_format", "markdown")
        
        if not disputes:
            return {"status": "error", "message": "Missing required parameter: disputes"}
            
        res = adjudicate_disputes(
            disputes=disputes,
            default_labels=default_labels,
            output_format=output_format,
            target_model=target_model
        )
        
        # 若需要直接接回 markdown 事实表，在返回中直接附带渲染文本
        import json
        if output_format == "markdown_only":
            return res.get("markdown_table", "")
        return json.dumps(res, ensure_ascii=False)

    handoff_schema = {
        "name": "jev_handoff_adjudicate",
        "description": "多专家执行中途动态交接（In-Flight Decision Handoff）裁决器。当专家在执笔/分析途中遇到事实属性、条款性质、证据真实性、偏差废标等争议分支时，中途交出并取得带置信度与状态指示的 Markdown 事实表，供专家零歧义接回继续生成。",
        "parameters": {
            "type": "object",
            "properties": {
                "disputes": {
                    "type": "array",
                    "description": "待裁决的争议点列表。每项可为对象 {'item': '争议事实', 'labels': ['候选标签A', '候选标签B'], 'id': 'D01'}，或纯文本项",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "争议编号，如 D01"},
                            "item": {"type": "string", "description": "争议具体事实、条款文本或物料描述"},
                            "labels": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "该争议项对应的候选判定标签列表"
                            }
                        },
                        "required": ["item"]
                    }
                },
                "default_labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "当争议项未单独指定 labels 时的公共候选标签列表（如 ['有效', '无效']）"
                },
                "target_model": {
                    "type": "string",
                    "description": "可选：当前执笔或接回的专家模型名称（如 claude-sonnet-4-6）"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["markdown", "json", "markdown_only"],
                    "description": "返回格式：'markdown'（JSON中附带完整Markdown事实表）、'markdown_only'（直接返回渲染表）、'json'（纯结构化数据）"
                }
            },
            "required": ["disputes"]
        }
    }

    ctx.register_tool(
        name="jev_handoff_adjudicate",
        toolset="jev",
        schema=handoff_schema,
        handler=_handoff_handler
    )

    # ---------------- 3. 智能搜索去噪快筛器 jev_filter_search ----------------
    def _search_filter_handler(args, **kwargs):
        query = args.get("query", "")
        candidates = args.get("candidates", [])
        top_k = int(args.get("top_k", 3))
        min_floor = int(args.get("min_floor", 2))
        res = filter_search_results(query=query, candidates=candidates, top_k=top_k, min_floor=min_floor)
        import json
        return json.dumps(res, ensure_ascii=False)

    search_filter_schema = {
        "name": "jev_filter_search",
        "description": "基于 Jev 的搜索结果智能快筛器。对原生 web_search 或 WSP (web_search_plus) 召回的候选网页进行去噪与反过杀保底，毫秒级过滤营销水文，强制保护Top-2与GB/法条硬核实体，节约70%上下文Token。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "原始搜索关键词/查询意图"},
                "candidates": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "搜索返回的原始网页列表（包含 title, snippet/description, url 等）"
                },
                "top_k": {"type": "integer", "description": "期望保留的精选条数（默认 3）", "default": 3},
                "min_floor": {"type": "integer", "description": "最小保留保底条数（默认 2），防止过滤过死导致无结果", "default": 2}
            },
            "required": ["query", "candidates"]
        }
    }

    ctx.register_tool(
        name="jev_filter_search",
        toolset="jev",
        schema=search_filter_schema,
        handler=_search_filter_handler
    )

    # ---------------- 5. 多专家编制与复杂度裁决器 jev_staffing_adjudicate ----------------
    def _staffing_handler(args, **kwargs):
        task_description = args.get("task_description") or args.get("task") or args.get("query", "")
        max_limit = int(args.get("max_experts_limit", 9))
        res = evaluate_task_complexity_and_staffing(task_description, max_experts_limit=max_limit)
        import json
        return json.dumps(res, ensure_ascii=False)

    staffing_schema = {
        "name": "jev_staffing_adjudicate",
        "description": "基于 Jev System One 的多专家编制与复杂度裁决器。输入复杂任务描述，Jev 在 0~60ms 内完成领域定性、风险分级（S/M/L/XL）、争议研判与一票升级断言，严格按区间下限输出推荐专家人数、范式角色阵容与派前可读清单。",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "待评估与派发专家的任务详细描述、背景或指令"
                },
                "max_experts_limit": {
                    "type": "integer",
                    "description": "允许的最大专家并发上限（默认 9，受系统配置保护）",
                    "default": 9
                }
            },
            "required": ["task_description"]
        }
    }

    ctx.register_tool(
        name="jev_staffing_adjudicate",
        toolset="jev",
        schema=staffing_schema,
        handler=_staffing_handler
    )


