#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jev 2.0 网关转接中继层 (jev_gateway_bridge.py)
无缝桥接 JevFullOrchestrator 到 run_turn_runner.py
负责：
1. 提取飞书最新消息内容进行 0ms 全链路预检与编排
2. 动态调度记忆标签、专属技能、MCP 白名单、案卷路径
3. 裁决会话修剪与智能压缩策略
4. 记录日志与底栏遥测指标
"""

import sys
import os
import logging

logger = logging.getLogger("hermes.jev.gateway")

PLUGIN_DIR = "/Users/xia/.hermes/plugins/jev-fast-classifier"
if PLUGIN_DIR not in sys.path:
    sys.path.append(PLUGIN_DIR)

try:
    from jev_orchestrator import JevFullOrchestrator
    _ORCHESTRATOR = JevFullOrchestrator()
except Exception as e:
    _ORCHESTRATOR = None
    logger.error(f"[Jev2.0 Bridge] Failed to load JevFullOrchestrator: {e}")

def run_gateway_preflight(agent, api_message: str) -> dict:
    """在 agent.run_conversation 之前被网关调用"""
    if not _ORCHESTRATOR:
        return {"status": "skipped", "reason": "orchestrator_not_available"}

    try:
        # 获取当前会话的历史轮数与 Token 水位
        history_len = 0
        current_tokens = 0
        if hasattr(agent, "messages") and agent.messages:
            history_len = len(agent.messages)
            # 粗估 Token 水位用于压缩分级判定
            current_tokens = sum(len(str(m)) for m in agent.messages) // 2

        # 执行 1ms 终极全链路调度编排
        res = _ORCHESTRATOR.orchestrate_turn(api_message, history_len=history_len, current_tokens=current_tokens)

        stage0 = res.get("stage_0_debounce", {})
        stage1 = res.get("stage_1_preflight", {})
        stage2 = res.get("stage_2_memory_and_files", {})
        stage3 = res.get("stage_3_skills_and_tools", {})
        stage4 = res.get("stage_4_compression", {})

        prompt_injection = stage2.get("prompt_injection", "")
        setattr(agent, "_jev2_prompt_injection", prompt_injection)

        # 将预检编排指标全量挂载到 agent 对象供系统与底栏读取
        eval_count = res.get("eval_count", 6)
        setattr(agent, "_jev2_eval_count", eval_count)
        setattr(agent, "_jev2_domain", stage1.get("domain", "日常闲聊"))
        setattr(agent, "_jev2_topic", stage1.get("topic", "通用问答"))
        setattr(agent, "_jev2_confidence", stage1.get("confidence", 0.90))
        setattr(agent, "_jev2_collision", stage0.get("action", "NORMAL_PROCEED"))
        setattr(agent, "_jev2_memory_tags", stage2.get("memory_tags", []))
        setattr(agent, "_jev2_discovered_paths", stage2.get("discovered_paths", []))
        setattr(agent, "_jev2_activated_skills", stage3.get("activated_skills", []))
        setattr(agent, "_jev2_mcp_quota", stage3.get("allowed_mcps", []))
        setattr(agent, "_jev2_keep_turns", stage4.get("keep_turns", 2))
        setattr(agent, "_jev2_compression_action", stage4.get("action", "LIGHTWEIGHT_PRUNING"))

        is_t0 = stage1.get("is_t0", False)
        # 统计 Jev 分流呈现：即使 T0 秒读，也是 Jev 全链完成的 0ms 判定
        setattr(agent, "_jev_turn_calls", 1)
        setattr(agent, "_jev_assigned_model", stage1.get("domain", "全链编排"))
        setattr(agent, "_jev_is_t0", is_t0)

        try:
            from jev_context import record_jev_call
            record_jev_call(assigned_model=stage1.get("domain", "全链编排"), eval_count=eval_count)
        except Exception:
            pass

        # 结构化业务日志记录
        logger.info(
            f"[Jev2.0 Orchestrator] 耗时:{res['elapsed_ms']}ms 领域:{stage1.get('domain')} "
            f"置信:{stage1.get('confidence')} 动作:{stage0.get('action')} "
            f"技能:{stage3.get('activated_skills')} MCP:{stage3.get('allowed_mcps')} "
            f"压缩:{stage4.get('action')}(保{stage4.get('keep_turns')}轮)"
        )

        # 如果有 Jev 生成的四步资产包，拼装入站增强指令送入大模型视野
        if prompt_injection and prompt_injection.strip():
            res["injected_message"] = f"{prompt_injection.strip()}\n\n[用户当前实际指令]:\n{api_message}"
        else:
            res["injected_message"] = api_message

        # 构建高水准【📋 前置理解对账单】（方案 A+ 黄金标准：三主干加内嵌序号分点展开，紧凑占首屏约 30%）
        domain_name = stage1.get("domain", "通用运维")
        topic_name = stage1.get("topic", "通用问答")
        tools_list = stage3.get("recommended_tools", [])
        if not tools_list:
            if domain_name == "商贸投标":
                tools_list = ["web_search_plus (工业品专线)", "web_extract_plus", "execute_code (算税与运费)"]
            elif domain_name == "四案诉讼":
                tools_list = ["read_file", "search_files", "execute_code (IRR精算与利息穿透)"]
            elif domain_name == "彩票推演":
                tools_list = ["execute_code (旋转矩阵与形态检验)", "read_file"]
            else:
                tools_list = ["terminal (只读探针)", "read_file", "process_manage"]
        tools_str = " ➔ ".join(tools_list[:3])

        # 精准提炼用户真实意图（穿透 Jev 资产包外壳，提取真实指令）
        import re
        m_cmd = re.search(r'\[用户当前实际指令\]:\s*\n*(.*?)(?=\n*【Jev|\Z)', api_message, re.DOTALL)
        if m_cmd and m_cmd.group(1).strip():
            raw_cmd = m_cmd.group(1).strip()
        else:
            raw_cmd = api_message.strip()
        cmd_lines = [l.strip() for l in raw_cmd.splitlines() if l.strip() and not l.startswith("[") and not l.startswith("【Jev")]
        clean_user_q = cmd_lines[0][:100] if cmd_lines else raw_cmd[:100]

        # ----------------------------------------------------
        # Jev 智能定级：判断是简单口语穿透，还是 L/XL 级复杂任务
        # ----------------------------------------------------
        is_complex = False
        # 复杂度判定指标：长篇描述、包含多个动作标点、特定高复杂度业务关键词
        if len(raw_cmd) > 30 or len(cmd_lines) > 2:
            is_complex = True
        if any(w in raw_cmd for w in ["排查", "方案", "优化", "重构", "核算", "答辩", "多专家", "分析", "比价", "梳理", "检测", "体检", "巡检"]):
            is_complex = True
        # 短语口语判定（泛化匹配各种口语化确认与检验短语）
        is_short_test = bool(re.search(r"^(测试一下|测一下|看看|试试|测试|按这样改|按A改|可以|现在看看|对不对|看看对不对|现在看看，对不对|好不好|行不行|你看下|看下)$", clean_user_q))
        if not is_short_test and len(clean_user_q) <= 12 and any(w in clean_user_q for w in ["看看", "测试", "对不对", "行不行", "试试", "验下"]):
            is_short_test = True

        if is_short_test:
            is_complex = False

        # ----------------------------------------------------
        # Jev 智能任务分解器：生成与交付核验打勾账单 1:1 绝对镜像的任务清单
        # 彻底废除假大空套话，输出具体的待销项 tasks: [task1, task2, task3]
        # ----------------------------------------------------
        # 提取真实的业务动宾核心
        task_items = []
        if any(w in clean_user_q for w in ["改", "优化", "重构", "修复", "调整"]):
            task_items = [
                "定位核心代码/配置锚点，设计最小差异靶向修改方案",
                "实施代码与配置落盘，通过本地 Python/AST 语法校验",
                "执行真实命令与测试验收，确认退出码 exit 0 与预期读数"
            ]
        elif any(w in clean_user_q for w in ["测", "跑", "执行", "试试"]):
            task_items = [
                "检查运行环境依赖与进程状态，排除资源冲突与锁占用",
                "发起真实调用与连通性测试，捕获完整通信报文与指标",
                "复核老 Mac 内存与 CPU 负载读数，确保宿主冰凉无残留"
            ]
        elif any(w in clean_user_q for w in ["查", "看", "排查", "分析", "对比"]):
            task_items = [
                "只读穿透核心数据源与日志文件，锁定真实客观读数",
                "多维度比对技术参数与方案差异，提炼核心结论与优劣",
                "输出一页纸对账结论与可复核的出处凭据清单"
            ]
        elif domain_name == "商贸投标":
            task_items = [
                "穿透厂家直销特惠引流价，核算钢材吨价与出厂裸价",
                "计入 13% 增值税专票与落地昆明运费，测算总到手成本",
                "比对近期大宗大盘基准价，输出防买贵采购比价清单"
            ]
        elif domain_name == "四案诉讼":
            case_hit = [p for p in stage2.get("discovered_paths", []) if "民初" in p]
            c_name = os.path.basename(case_hit[0]) if case_hit else "在办金融案卷"
            task_items = [
                f"穿透「{c_name}」核心争点，核验对方举证漏洞与程序瑕疵",
                "检索 FLK 官方法规库与最高法案例库，锁定抗辩法定条号",
                "起草法官直接采信的客观裁判认定段落，严守防自认底线"
            ]
        else:
            task_items = [
                f"精准解析指令客体「{clean_user_q[:20]}」，确立技术落地路径",
                "调用轻量探针与原子工具执行作业，获取真实执行凭证",
                "完成交付前真实性自查，输出 1:1 对应的 Jev 打勾核验账单"
            ]

        tasks_md = "\n".join([f"  1. [ ] {t}" if i==0 else f"  {i+1}. [ ] {t}" for i, t in enumerate(task_items)])
        tasks_directive = "\n".join([f"{i+1}. {t}" for i, t in enumerate(task_items)])

        # 统一装配规范通栏的前置理解对账单
        card_md = (
            f"📋 **【前置理解对账单 · 任务销项航线图】**\n"
            f"- 🎯 **待核验销项清单（与交付打勾账单 1:1 绝对镜像）**：\n"
            f"{tasks_md}\n"
            f"- 💡 **多想一步**：排查连带进程依赖与配置漂移风险，提前留存安全回滚点\n"
            f"- 🧭 **作战手段**：{tools_str} ➔ 机器核验出单\n"
            f"- 🛡️ **安全边界**：严守老 Mac 减负纪律，严禁改动根卷与 OCLP 驱动，纯只读优先"
        )

        res["preflight_card_markdown"] = card_md

        # 核心纪律注入：要求末尾 Jev 打勾账单严格按 task_items 逐项打勾，实现首尾 1:1 绝对对齐！
        preflight_ban_directive = (
            "\n\n【Jev 飞书卡片单向交付硬红线】\n"
            "1. 本轮「📋 前置理解对账单」已由 Jev 外脑以独立天蓝卡片率先送达主人飞书界面！\n"
            "2. 你的最终回复正文【绝对禁止】输出任何形式的「前置理解对账单」、「任务定性」、「预告作战工具」或开篇对账套话！\n"
            "3. 你的正文必须直接从「核心分析 / 落实结果 / 实测报告」正式起步！\n"
            f"4. 交付末尾必须直接出具「Jev 机器核验打勾账单」，必须且只能对以下 3 项待销项逐一核验打勾（严禁擅自增减篡改条目名，必须 1:1 绝对呼应）：\n"
            f"{tasks_directive}\n"
            "状态严格采用 Emoji 徽章（✅ 已完成 / 🚫 未达成 / ⏳ 待确认 / 🔄 进行中 / ⏭️ 已豁免），并附上真实工具执行铁证！\n"
        )
        res["injected_message"] = res.get("injected_message", api_message) + preflight_ban_directive

        return res
    except Exception as e:
        logger.warning(f"[Jev2.0 Orchestrator Error] {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    test_msg = "把微众银行朱继平说的那个5万块钱方案拒绝答辩词起草一下"
    class DummyAgent:
        messages = ["msg1", "msg2"]
    res = run_gateway_preflight(DummyAgent(), test_msg)
    print("Bridge Full Orchestrator test:", res["stage_1_preflight"]["domain"])
