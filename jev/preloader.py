"""
Jev Universal Preloader (Task Preloader & 4-Step Cognitive Framework)
Open Source Core Module for Task Framing, Safety Rails & Dynamic Confidence Scoring.
"""

import re
from typing import Dict, Any, List

def calculate_dynamic_confidence(query: str, domain: str) -> Dict[str, Any]:
    """
    Calculate dynamic confidence score based on entity density, action structure,
    and pronoun fragment penalties.
    """
    if not query or not query.strip():
        return {"confidence": 0.0, "tier": "LOW", "breakdown": "Empty query"}

    q = query.strip()
    score = 0.50

    # 1. Action structure detection (+0.25)
    action_match = re.search(r"(起草|拟写|编写|核算|报价|查询|检查|排查|优化|提取|分析|对比|草拟|审核|调小|调大|启动|关闭)", q)
    if action_match:
        score += 0.25

    # 2. Domain-specific entities (+0.25)
    if domain == "Legal":
        if re.search(r"(案|合同|起诉|答辩|管辖|借款|利息|违约金|判决|裁定|证据|举证|法条)", q):
            score += 0.25
    elif domain == "Commerce":
        if re.search(r"(单价|现货|税|专票|运费|到手价|采购|套|吨|米|件|个|支|台|批|现款)", q):
            score += 0.25
    elif domain == "SystemOps":
        if re.search(r"(cpu|内存|进程|负载|温度|发热|卡顿|端口|服务|网卡|磁盘|自愈|重启)", q.lower()):
            score += 0.25
    elif domain == "BrowserAutomation":
        if re.search(r"(网页|浏览器|登录|抓取|爬虫|dom|cookie|验证码|弹窗|点击)", q):
            score += 0.25
    else:
        if len(q) > 6:
            score += 0.15

    # 3. Pronoun fragment penalty (-0.20)
    if re.search(r"^(那个|这|接着|按这个|那件事|刚才说的|搞一下)$", q):
        score -= 0.20

    score = max(0.10, min(0.99, score))

    if score >= 0.85:
        tier = "HIGH"
    elif score >= 0.70:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return {
        "confidence": round(score, 2),
        "tier": tier,
        "length": len(q),
        "domain": domain
    }

def prefetch_task_assets(domain: str, query: str) -> Dict[str, Any]:
    """
    Assemble Universal 4-Step Blueprint, Safety Guards & Asset Injection without polluting system KV cache.
    """
    q = query.strip()
    is_interrupt = bool(re.search(r"(不对|算错了|有问题|重新来|推翻|停止|改一下)", q))

    if domain == "SystemOps":
        return {
            "category": "SystemOps",
            "recommended_tools": ["terminal (read-only: ps/top/sysctl)", "read_file", "process_manage"],
            "blueprint": (
                "=== [Universal 4-Step Lifecycle · System Operations] ===\n"
                "1. Symptom Identification: Inspect exact PID, resource metrics, read-only diagnostic first;\n"
                "2. Direction Strategy: Minimal intervention first (isolate rogue process), optimize thermal load;\n"
                "3. Targeted Tools: Native lightweight commands only, no invasive 3rd-party bloatware;\n"
                "4. Resolution & Verification: Re-probe system metrics post-action, deliver ground-truth readings."
            ),
            "safety_guards": [
                "Rail 1: Read-only probes first before any state modification.",
                "Rail 2: Never modify protected root filesystems or core kernel extensions.",
                "Rail 3: Destructive Action Gate - Mandatory explicit user approval for kill/rm/reboot commands."
            ],
            "verification_standard": "Check process exit code (exit 0) and compare physical sensor readings before/after."
        }

    elif domain == "Commerce":
        return {
            "category": "Commerce",
            "recommended_tools": ["web_search", "web_extract", "read_file", "calculator"],
            "blueprint": (
                "=== [Universal 4-Step Lifecycle · Procurement & Quotation] ===\n"
                "1. Specification Scope: Clarify exact material standard, quantity, and logistics destination;\n"
                "2. Cost Breakdown: Factory cost + Tax rate (e.g. 13% VAT) + Freight to site;\n"
                "3. Verified Channels: Target manufacturer wholesale benchmarks, bypass broker clickbaits;\n"
                "4. Cross-Verification: Cross-check per-unit and tonnage metrics, explicit freshness window."
            ),
            "safety_guards": [
                "Rail 1: Explicit Tax Rate - Always state VAT status (13% VAT invoice / pre-tax).",
                "Rail 2: Delivered Logistics - Clear destination freight inclusion.",
                "Rail 3: Quote Freshness Window - Mandatory validity period and raw material fluctuation clause."
            ],
            "verification_standard": "Itemized table calculation: Base Cost + Tax + Freight = Final Delivered Total."
        }

    elif domain == "Legal":
        return {
            "category": "Legal",
            "recommended_tools": ["legal_search_laws", "legal_search_cases", "legal_hit_display"],
            "blueprint": (
                "=== [Universal 4-Step Lifecycle · Dispute Defense & Legal Drafting] ===\n"
                "1. Dispute Focus: Isolate core legal relationship, burden of proof allocation, statutory limitations;\n"
                "2. Defense Strategy: Focus on procedural defects and formal evidentiary standards;\n"
                "3. Authority Hierarchy: Supreme Court interpretations, formal statutes, authoritative database items;\n"
                "4. Judicial Alignment: Deliver concise, judicial-ready findings directly quotable by courts."
            ),
            "safety_guards": [
                "Rail 1: No Concession Trap - Prohibit self-incriminating terms ('helpless', 'forced', 'insolvent').",
                "Rail 2: Verbatim Citations - Statute titles, article numbers, and effective dates must be cited accurately.",
                "Rail 3: Reset on Pivot - If user signals error, immediately drop stale premises and re-anchor to primary evidence."
            ],
            "verification_standard": "All cited statutes must verify verbatim against authoritative legal databases."
        }

    else:
        return {
            "category": "General",
            "recommended_tools": ["web_search", "read_file"],
            "blueprint": (
                "=== [Universal 4-Step Lifecycle · General Problem Solving] ===\n"
                "1. Problem Definition: Clarify core question and objective constraints;\n"
                "2. Strategic Path: Step-by-step verifiable path;\n"
                "3. Tool Pointing: Call minimum required tools;\n"
                "4. Verification: Deliver factual artifact with citation and zero hallucination."
            ),
            "safety_guards": ["Deliver concise, verified, actionable outputs."],
            "verification_standard": "Direct answer with verified source references."
        }
