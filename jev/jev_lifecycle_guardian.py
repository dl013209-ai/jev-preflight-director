#!/usr/bin/env python3
"""
Jev 2.0 Lifecycle Guardian (v1.0.0)
大模型任务全生命周期智能监护裁判模块。
专为老 Mac 与 Hermes 设计，恪守纯插件原则，覆盖：
1. Pre-Tool: 高危破坏性动作拦截 + 格式死穴审查
2. Post-Tool: 400/401/403/404/Timeout 错误急诊室 (秒出处方，杜绝盲目自旋)
3. Mid-Turn Steering: 中途插话 4 级语义仲裁 (归零熔断/参数覆盖/增量追加/底册防呆)
4. Result Trimmer: 终端巨量日志降噪修剪 (保护老 Mac 内存与 KV-Cache)
"""

import re
import json
from typing import Any, Dict, Optional, Tuple

# ----------------- 1. 物理安全红线规则库 -----------------
# 匹配不可逆破坏性命令模式
DESTRUCTIVE_COMMAND_PATTERNS = [
    r"\brm\s+-(?:r|f|rf|fr)\s+/(?:\s|$)",          # rm -rf /
    r"\brm\s+-(?:r|f|rf|fr)\s+~/(?:\s|$)",          # rm -rf ~/
    r"\brm\s+-(?:r|f|rf|fr)\s+\.\s*$",              # rm -rf .
    r"\bmkfs\b",                                     # 格式化
    r"\bdd\s+if=.*of=/dev/r?disk[0-9]",             # 破坏磁盘分区
    r"\bmount\s+.*-(?:o|uw|rw).*root\b",             # 重新挂载根卷 (Root Volume)
    r"\bdefaults\s+delete\s+.*AppleWindowHandler",   # 破坏 OCLP 图形驱动链
    r"\brm\s+.*(?:Application\s+Support/LarkShell|Library/Containers/com\.tencent\.xinWeChat)", # 删飞书/微信数据
]

# ----------------- 2. 工具前置门禁 (Pre-Tool Guardian) -----------------
def pre_tool_guardian(tool_name: str, args: Any) -> Optional[Dict[str, Any]]:
    """
    工具调用前审查。严格遵循 Hermes 官方 pre_tool_call 返回契约：
      - return None                                 -> 放行
      - {"action": "block",  "message": "..."}      -> 物理熔断拦截
      - {"action": "modify", "args": {...}}         -> 就地纠偏入参后放行
      - {"action": "approve","message": "..."}      -> 升级人工拍板门禁
    """
    if not isinstance(args, dict):
        return None

    # ---------- A. terminal 命令审查 ----------
    if tool_name == "terminal":
        cmd = args.get("command")
        if not isinstance(cmd, str):
            return None
        cmd = cmd.strip()

        # A1. 物理安全红线：不可逆破坏性命令 -> 硬拦截
        for pat in DESTRUCTIVE_COMMAND_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return {
                    "action": "block",
                    "message": (
                        f"🛑 [Jev 物理安全红线拦截] 检测到高危不可逆破坏命令: `{cmd}`！\n"
                        "触犯【红线1·禁毁系统】或【红线2·禁删记录】！\n"
                        "底层已物理强制熔断阻断执行！如确有需要，必须先出具受损影响清单并在飞书等主人明确拍板！"
                    )
                }

        # A2. 高危不可逆动作（kill/reboot/dd/rm 等）-> 升级人工拍板门禁（红线4）
        if _is_reversible_risk_command(cmd):
            return {
                "action": "approve",
                "message": (
                    f"⚠️ [Jev 高危动作拍板门禁] 命令涉及不可逆操作: `{cmd}`\n"
                    "触犯【红线4·高危动作拍板门禁】！已挂起，等主人明确拍板后方可执行！"
                ),
                "rule_key": "jev_destructive_action_gate",
            }

    # ---------- B. 文件写入路径审查 ----------
    if tool_name in ("write_file", "patch"):
        raw_path = args.get("path")
        if not isinstance(raw_path, str):
            return None
        path = raw_path.strip()

        # B1. 系统底层与系统卷 -> 硬拦截
        blocked_prefixes = (
            "/System", "/Library/Apple", "/private/var/db",
            "/Volumes/", "/usr/lib", "/usr/sbin", "/bin", "/sbin",
        )
        if any(path.startswith(p) for p in blocked_prefixes):
            return {
                "action": "block",
                "message": (
                    f"🛑 [Jev 物理安全红线拦截] 严禁修改 macOS 系统底层文件: `{path}`！\n"
                    "触犯老 Mac Haswell Iris Pro 核显宿主物理红线！已底层拦截！"
                )
            }

        # B2. 微信/飞书本地数据（红线2）-> 硬拦截
        if ("LarkShell" in path) or ("com.tencent.xinWeChat" in path) or ("WeChat" in path and "Library" in path):
            return {
                "action": "block",
                "message": (
                    f"🛑 [Jev 物理安全红线拦截] 检测到试图改动微信/飞书本地数据库: `{path}`！\n"
                    "触犯【红线2·禁删记录】！已底层物理拦截！"
                )
            }

    return None


def _is_reversible_risk_command(cmd: str) -> bool:
    """识别高危但非"格式化级"的不可逆动作，用于升级人工拍板门禁。

    仅匹配真正会改动系统状态、且无法简单撤销的形态，避免把只读探针误伤升级。
    """
    readonly_guards = (
        "grep", "pgrep", "ps aux", "top -l", "sysctl -n", "lsof", "ls ", "cat ",
        "read", "status", "df -h", "uptime", "which ",
    )
    if any(g in cmd for g in readonly_guards):
        return False

    risky_patterns = [
        r"(?:^|[;&|]\s*)sudo\s+",                     # sudo 提权
        r"\bkill(?:all)?\s+-\d*9\b|\bkill(?:all)?\s+-KILL\b",  # 强杀
        r"\breboot\b|\bshutdown\b|\bhalt\b",           # 关机重启
        r"\bdd\s+",                                     # dd 写盘
        r"\bdiskutil\s+(?:erase|reformat|partition)",   # 磁盘操作
        r"\brm\s+-(?:r|f|rf|fr)",                      # 递归删除（非根路径已由上一步拦）
        r"\bchmod\s+-R\s+777\b",                       # 权限滥改
        r"\blaunchctl\s+(?:unload|bootout|remove)",     # 卸载系统服务
        r"\bcsrutil\b|\bspctl\b",                      # 系统完整性策略
    ]
    for pat in risky_patterns:
        if re.search(pat, cmd):
            return True
    return False


# ================= 2B. 法律业务红线守护 (Legal Domain Guardian) =================
# 源自《通用四步全链路资产包 · 诉讼文书与法律抗辩》三条业务红线。
# 触发场景：write_file / patch 写入文书类文件（.md/.docx 等诉讼材料）。

# 【红线1·防自认拦截】隐性自认词（主人明示特赦方可放行）
LEGAL_SELF_ADMISSION_TERMS = [
    "被迫", "借新还旧", "无力偿还", "无力清偿", "确实欠款", "承认欠款",
    "自愿承担", "我方违约", "本人违约", "同意偿还", "愿意归还", "确有困难",
    "实在还不上", "认账", "自认", "无异议认可",
]

# 文书类扩展名
_LEGAL_DOC_SUFFIXES = (".md", ".txt", ".docx", ".doc")


def _looks_like_legal_document(path: str) -> bool:
    """判断目标路径是否像一份诉讼/法律文书。"""
    if not isinstance(path, str):
        return False
    p = path.lower()
    if not p.endswith(_LEGAL_DOC_SUFFIXES):
        return False
    legal_markers = (
        "起诉状", "答辩", "上诉", "再审", "代理意见", "质证", "申请书",
        "答辩状", "抗辩", "诉状", "法律意见", "案件分析", "心证", "证据清单",
        "legal/", "诉讼", "案卷",
    )
    return any(m in path or m.lower() in p for m in legal_markers)


def legal_document_guard(tool_name: str, args: Any) -> Optional[Dict[str, Any]]:
    """诉讼文书业务红线预审（写盘前）。

    【红线1·防自认拦截】：文书中出现隐性自认词 -> 升级人工拍板门禁，
      因为这类词一旦落入卷宗即为对己方不利的事实自认，不可逆。
    """
    if tool_name not in ("write_file", "patch"):
        return None
    if not isinstance(args, dict):
        return None

    path = args.get("path")
    if not _looks_like_legal_document(path):
        return None

    # 抽取待写入正文（write_file 用 content；patch 用 new_string）
    body = args.get("content")
    if not isinstance(body, str):
        body = args.get("new_string")
    if not isinstance(body, str) or not body:
        return None

    hits = [w for w in LEGAL_SELF_ADMISSION_TERMS if w in body]
    if hits:
        return {
            "action": "approve",
            "message": (
                f"⚖️ [Jev 法律红线1·防自认拦截] 文书 `{path}` 中出现隐性自认词: {('、'.join(hits))}\n"
                "此类词句一经落卷即构成对己方不利的事实自认，且不可逆！\n"
                "已挂起，等主人明确特赦（或改写为客观认定句）后方可落盘。"
            ),
            "rule_key": "jev_legal_self_admission_gate",
        }
    return None


# ----------------- 3. 错误急诊室 (Error Doctor) -----------------
def error_doctor(tool_name: str, args: Any, result_str: str) -> Optional[str]:
    """
    审查工具返回结果中的 400/401/403/404/超时 错误，生成靶向处方：
    - 返回包含 Jev 处方的增强结果字符串
    - 若无异常则返回 None (保持原样)
    """
    if not isinstance(result_str, str) or len(result_str) < 5:
        return None
        
    lower_res = result_str.lower()
    
    # A. 403 Forbidden / Handshake Timeout (网络被墙 / 权限 / 缺少代理)
    if "403" in result_str or "handshake operation timed out" in lower_res or "connection refused" in lower_res:
        prescription = (
            "\n\n🚨 【Jev 错误急诊室 · 403/超时专线处方】\n"
            "• 根因诊断: 目标端点存在地域拦截、直连被墙或 SSL 握手超时！\n"
            "• 裁决指令: 严禁在当前国内通道重复盲试！必须立即切换走【老 Mac 本地 VPS 1082 代理专线】(http://127.0.0.1:1082)！\n"
            "• 执行动作: 注入 ProxyHandler 或在请求头补全 User-Agent，1 轮内精准搞定！"
        )
        return result_str + prescription
        
    # B. 400 Bad Request / Invalid Model / Model Not Found
    if "400" in result_str and ("invalid" in lower_res or "model_not_found" in lower_res or "not support" in lower_res or "unknown model" in lower_res):
        prescription = (
            "\n\n🚨 【Jev 错误急诊室 · 400 模型失效处方】\n"
            "• 根因诊断: 目标模型 ID 不存在、已更名或已被平台下架！\n"
            "• 裁决指令: 严禁凭空瞎猜模型名字重复重试！\n"
            "• 执行动作: 立即调用 `quick_onboard_provider.py probe <base_url>` 机器拉取在册真实清单，或调用 `refresh` 清洗失效模型！"
        )
        return result_str + prescription

    # C. 401 Unauthorized (API Key 无效 / 环境变量丢失)
    if "401" in result_str or "unauthorized" in lower_res or "invalid api key" in lower_res:
        prescription = (
            "\n\n🚨 【Jev 错误急诊室 · 401 凭证失效处方】\n"
            "• 根因诊断: API Key 缺失、未在 .env 注入或账户授权过期！\n"
            "• 裁决指令: 严禁死循环盲目重试！\n"
            "• 执行动作: 立即停止执行，在飞书中温润提示主人核查该通道的 API Key！"
        )
        return result_str + prescription

    # D. 404 Not Found (路径/端点错误)
    if "404" in result_str and ("not found" in lower_res or "page not found" in lower_res):
        prescription = (
            "\n\n🚨 【Jev 错误急诊室 · 404 端点未找到处方】\n"
            "• 根因诊断: 请求 URL 路径或端点路由拼写有误（如漏写 /v1 或多拼了 /chat）！\n"
            "• 裁决指令: 检查 base_url 配置是否符合 OpenAI 规范标准！"
        )
        return result_str + prescription

    return None


# ----------------- 4. 中途插话仲裁器 (Steering Adjudicator) -----------------
OUT_OF_BAND_START = "[OUT-OF-BAND USER MESSAGE"
OUT_OF_BAND_END = "[/OUT-OF-BAND USER MESSAGE]"

def adjudicate_steering(text: str) -> Optional[str]:
    """
    检测文本中是否包含主人的中途插话。
    若有，调用 Jev 毫秒级判别四类意图，并在消息头部贴上强制行动令。
    """
    if OUT_OF_BAND_START not in text:
        return None
        
    pattern = r"(\[OUT-OF-BAND USER MESSAGE[^\]]*\])([\s\S]*?)(\[/OUT-OF-BAND USER MESSAGE\])"
    match = re.search(pattern, text)
    if not match:
        return None
        
    prefix_tag = match.group(1)
    user_speech = match.group(2).strip()
    suffix_tag = match.group(3)
    
    # 快速四级意图定性 (基于规则 + 关键意图原语)
    speech_lower = user_speech.lower()
    
    # 类别 1: 否定 / 反悔 / 撤销 (PIVOT_INTERRUPT)
    if any(k in speech_lower for k in ["不对", "算错", "停", "不要", "撤销", "换一个", "别搞", "思路错", "重来"]):
        jev_badge = (
            "\n⚡⚡⚡ [Jev 中途最高裁决 · PIVOT_INTERRUPT 归零熔断 (置信度 0.99)] ⚡⚡⚡\n"
            "• 裁决令: 主人已下达【否定/反悔】最高指令！\n"
            "• 强制动作: 立即物理抛弃上一轮所有未完成的草稿与前置错误假设！\n"
            "• 纪律: 严禁将新旧指令生搬硬套拼接！以主人新要求为唯一源头，重新起草执行！\n"
            "• 记忆加固: 该纠偏场景在后台以 5 倍权重记入蒸馏库防复发！\n"
            "────────────────────────────────────────────────────────\n"
        )
    # 类别 2: 硬参数纠偏 (PARAM_OVERRIDE)
    elif any(k in speech_lower for k in ["走vps", "走代理", "改端口", "改成", "换成", "1082", "20128", "用10router", "用codebuddy"]):
        jev_badge = (
            "\n⚡⚡⚡ [Jev 中途最高裁决 · PARAM_OVERRIDE 参数强制覆盖 (置信度 0.99)] ⚡⚡⚡\n"
            "• 裁决令: 主人下达了关键硬参数修正指令！\n"
            "• 强制动作: 提取出主人给出的新参数（如 VPS 1082 / 目标端点），立即覆盖原有参数！\n"
            "• 纪律: 禁止继续沿用老参数盲试！\n"
            "────────────────────────────────────────────────────────\n"
        )
    # 类别 3: 追加新功能 / 条件 (STACK_APPEND)
    elif any(k in speech_lower for k in ["还要", "另外", "顺便", "加上", "支持", "同时", "记得"]):
        jev_badge = (
            "\n⚡⚡⚡ [Jev 中途最高裁决 · STACK_APPEND 增量挂载 (置信度 0.95)] ⚡⚡⚡\n"
            "• 裁决令: 主人补充了新特性/新约束条件！\n"
            "• 强制动作: 保持现有正确方向不变，将新需求作为追加待办压入执行栈！\n"
            "────────────────────────────────────────────────────────\n"
        )
    # 类别 4: 普通指导 / 确认
    else:
        jev_badge = (
            "\n⚡⚡⚡ [Jev 中途最高裁决 · STEER_GUIDANCE 主人实时指令 (置信度 0.92)] ⚡⚡⚡\n"
            "• 裁决令: 主人正在实时指引方向，具备最高行动权！优先满足主人当前补充的重点！\n"
            "────────────────────────────────────────────────────────\n"
        )
        
    augmented_user_speech = f"{prefix_tag}\n{jev_badge}主人最新指令: \"{user_speech}\"\n{suffix_tag}"
    new_text = text[:match.start()] + augmented_user_speech + text[match.end():]
    return new_text


# ----------------- 5. 结果降噪修剪器 (Result Trimmer) -----------------
def trim_result(tool_name: str, result_str: str, max_chars: int = 4000) -> str:
    """
    对返回的巨量文本（尤其是 terminal 或网页输出）进行精简，保护老 Mac 内存与 KV-Cache
    """
    if not isinstance(result_str, str) or len(result_str) <= max_chars:
        return result_str
        
    # 保留头 1500 字符 + 尾 2000 字符，中间折叠
    head = result_str[:1500]
    tail = result_str[-2000:]
    trimmed = (
        f"{head}\n\n"
        f"--- [Jev 自动降噪折叠: 中间省略 {len(result_str) - 3500} 字符冗余日志，保护老 Mac 内存与上下文] ---\n\n"
        f"{tail}"
    )
    return trimmed


# ----------------- 6. 统一对外综合处理器 -----------------
def handle_pre_tool_call(tool_name: str, args: Any, **kwargs) -> Optional[Dict[str, Any]]:
    """pre_tool_call 钩子总入口：物理安全红线 + 法律业务红线 双重预审"""
    # 甲、电脑运维/系统类红线（禁毁系统、禁删记录、高危拍板门禁）
    guard = pre_tool_guardian(tool_name, args)
    if guard is not None:
        return guard

    # 乙、法律业务红线（防自认拦截 / 事实认定归主人）
    legal = legal_document_guard(tool_name, args)
    if legal is not None:
        return legal

    return None


def handle_transform_tool_result(tool_name: str, args: Any, result: Any, **kwargs) -> Optional[str]:
    """transform_tool_result 钩子总入口"""
    result_str = str(result) if not isinstance(result, str) else result

    # 1. 先检查是否包含中途插话，有则注入 Jev 仲裁令
    steering_augmented = adjudicate_steering(result_str)
    if steering_augmented is not None:
        result_str = steering_augmented

    # 2. 检查是否有 400/401/403/404 报错，有则注入 Jev 急诊处方
    error_augmented = error_doctor(tool_name, args, result_str)
    if error_augmented is not None:
        result_str = error_augmented

    # 3. 法律卷宗结果核验（红线3·事实认定归主人 + 真实性核验·FLK 编号）
    legal_note = legal_result_verifier(tool_name, result_str)
    if legal_note is not None:
        result_str = result_str + legal_note

    # 4. 结果超长降噪修剪 (仅对 terminal 且超过 5000 字符的结果进行保真折叠)
    if tool_name == "terminal" and len(result_str) > 5000:
        result_str = trim_result(tool_name, result_str)

    # 如果内容有变化则返回新字符串，否则返回 None (Hermes 约定 None 表示原样直通)
    if result_str != str(result):
        return result_str
    return None


# ================= 7. 法律结果核验器 (Legal Result Verifier) =================
# 对应资产包【真实性核验】与【红线3·事实认定归主人】

# 国家法律法规数据库 (FLK) 唯一编号形态：flk.npc.gov.cn 的 bbbs 码 / 带年份的法规引用
_FLK_ID_PATTERN = re.compile(r"flk[:\-]?\s*[0-9a-zA-Z\-]{6,}", re.IGNORECASE)
# 法条引用形态：《中华人民共和国民法典》第一千零七十九条 / 第 X 条
_LAW_CITE_PATTERN = re.compile(r"第[一二三四五六七八九十百千零〇0-9]+条")

# 涉案金额/案号形态：提示"事实认定权归主人"
_AMOUNT_PATTERN = re.compile(r"(?:本金|利息|欠款|金额|余额|标的额)[^\n]{0,20}?[\d,]+(?:\.\d+)?\s*(?:元|万元)")
_CASE_NO_PATTERN = re.compile(r"[（(]\s*\d{4}\s*[)）][^\s，。]{0,12}?号")


def legal_result_verifier(tool_name: str, result_str: str) -> Optional[str]:
    """法律卷宗结果侧核验：在结果返回模型前，贴上客观核验清单。

    仅当结果中出现"法条引用"或"涉案金额/案号"时才附加，避免污染普通工具结果。
    """
    if not isinstance(result_str, str) or len(result_str) < 20:
        return None

    cites = _LAW_CITE_PATTERN.findall(result_str)
    amounts = _AMOUNT_PATTERN.findall(result_str)
    case_nos = _CASE_NO_PATTERN.findall(result_str)

    if not cites and not amounts and not case_nos:
        return None

    lines = ["\n\n⚖️ 【Jev 法律结果核验清单 · 交付前必查】"]

    # 【真实性核验】法条必须带 FLK 唯一编号与生效年份
    # 注意：FLK 编号本身即最强证据，独立于"第X条"式引用判断，避免漏判
    has_flk = bool(_FLK_ID_PATTERN.search(result_str))
    if cites or has_flk:
        cite_desc = f"法条引用 {len(cites)} 处" if cites else "法条引用"
        if has_flk:
            lines.append(
                f"• {cite_desc}：✅ 已检出 FLK 官方唯一编号，可直接引用\n"
                "  → 仍需核对生效年份与是否被修订，确保引用现行有效版本"
            )
        else:
            lines.append(
                f"• {cite_desc}：⚠️ 未检出 FLK 唯一编号！\n"
                "  → 交付前必须经 legal-hub 回源核实逐字条文与生效年份，禁止凭记忆引用"
            )

    # 【红线3·事实认定归主人】
    if amounts or case_nos:
        bits = []
        if amounts:
            bits.append(f"涉案金额 {len(amounts)} 处")
        if case_nos:
            bits.append(f"案号 {len(case_nos)} 处")
        lines.append(
            f"• {('、'.join(bits))}：⚠️【红线3·事实认定归主人】\n"
            "  → 只整理不拍板！数字必须逐字对齐原始证据清单，事实认定权归主人"
        )

    # 【红线2·客观认定句】
    lines.append(
        "• 段落首句：必须是可以让法官直接复制进判决书的客观认定句，"
        "不得使用诉苦/情绪化表述"
    )
    return "\n".join(lines)
