#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jev_task_preloader.py - Jev 2.0 通用四步全链路装配与真实度质检引擎 (Universal Pipeline Engine)
真正实现做任何事情的通用闭环：
1. 什么问题（实体解构 + 资产 0ms 秒级预装）
2. 解决方向（破局策略 + 物理/法律/商业安全硬红线）
3. 用什么工具（精准工具点将 + 脏数据脱水去噪）
4. 怎么解决与真实核验（实施执行 + 三源出处核验 + 物理落盘）

覆盖四大通用实战领域：
- 场景 A：修电脑与系统运维 (Hardware & macOS Resilience)
- 场景 B：查资料价格与五金采购 (Commercial Pricing & Sourcing)
- 场景 C：司法诉讼抗辩与文书起草 (Litigation Defense & Grounding)
- 场景 D：生活彩票与统计推演 (Lottery Statistical Pruning)
"""

import os
import re
from typing import Dict, Any, List, Optional

# ==========================================
# 1. 通用物理与业务资产底册 (Local Asset Vault)
# ==========================================

# 场景 A 资产：老 Mac 宿主硬件守护卡
MAC_HARDWARE_CARD = """【老款 Mac 宿主硬件环境与安全底册】
- 设备规格：2015 款 MacBook Pro 15 寸 (Haswell Iris Pro 核显, 16G 内存)
- 系统环境：OCLP 驱动引导的 macOS Sequoia (15.7.7)
- 物理安全红线（绝对禁止）：
  1. 严禁执行任何修改或挂载系统根卷 (Root Volume) 的命令；
  2. 严禁覆盖或改动 OCLP 图形加速补丁与驱动链；
  3. 严禁清理微信/飞书的本地聊天记录数据库与会话缓存；
  4. 遇到高负载脚本必须优先考虑 CPU 温度与核显发热，优先推荐只读轻量探针。"""

# 场景 B 资产：云南CommercialTrading开票与交付底册
PINGMI_COMMERCIAL_CARD = """【云南CommercialTrading采购与交付核价底册】
- 公司抬头：Example Commercial Co., Ltd.
- 统一税号：91530111MA6QCAJ483
- 开户银行：中国光大银行昆明分行 39680188000118256
- 商业硬红线（绝对守死）：
  1. 必须包含 13% 增值税专用发票；
  2. 必须核算运抵云南昆明的实际落地物流运费；
  3. 严禁采信未经核实的网络引流价（低于原材料大宗吨价的必须剔除）；
  4. 交付排版：强制三段式表格（规格参数、未税出厂价、13%专票含运费到手价）。"""

# 场景 C 资产：四案诉讼卷宗与法官心证底册
LITIGATION_CASES_CARD = {
    "webank": {
        "title": "Bank A 7969 案",
        "dir": "/Users/xia/Desktop/诉讼案件/Bank A",
        "keywords": ["BankA", "7969", "Party X", "质证点", "核实函"],
        "core_entities": "原告：Bank A Corp.；案号：(202X) Case No.XXXX；主张本金约5万元及高额违约金",
        "blueprint": "主攻电子存证合法性与利息畸高违规；首句必须是法官客观认定句；严禁出现自认词（被迫/借新还旧/无力偿还）。",
        "tools": ["read_file", "patch", "legal-hub"]
    },
    "citic": {
        "title": "Bank B 37023 信用卡案",
        "dir": "/Users/xia/Desktop/诉讼案件/Bank B",
        "keywords": ["BankB", "37023", "信用卡", "西山法院", "管辖异议"],
        "core_entities": "原告：Bank B股份有限公司；案号：(202X) Case No.XXXX；审理法院：昆明市西山区人民法院",
        "blueprint": "主攻管辖权异议与送达程序违法；首句法官心证认定句；重点核实账单流水利息计提基数。",
        "tools": ["read_file", "legal-hub"]
    },
    "fumin": {
        "title": "富民银行案",
        "dir": "/Users/xia/Desktop/诉讼案件/富民银行",
        "keywords": ["富民", "互联网贷款", "电子合同", "格式条款", "牟传芳"],
        "core_entities": "富民银行互联网消费贷款争议，主审法官牟传芳",
        "blueprint": "主攻格式条款未尽提示说明义务（民法典496/497条）；要求出示原始CA数字证书与Hash防篡改时间戳。",
        "tools": ["read_file", "legal-hub"]
    },
    "pingan": {
        "title": "平安普惠/借款案",
        "dir": "/Users/xia/Desktop/诉讼案件/平安普惠",
        "keywords": ["平安", "普惠", "服务费", "担保费", "综合费率"],
        "core_entities": "综合费率畸高争议，砍头息、担保费隐蔽剥削",
        "blueprint": "穿透本金真实到手金额，重核实际年化IRR综合费率（扣减不合法服务费担保费）。",
        "tools": ["read_file", "execute_code"]
    }
}

# ==========================================
# 2. 动态置信度量化算法 (Dynamic Confidence)
# ==========================================

def calculate_dynamic_confidence(query: str, domain: str) -> Dict[str, Any]:
    """
    量化动态置信度：
    1. 实体丰富度 (0.0 ~ 0.45)
    2. 动宾动作明确度 (0.0 ~ 0.45)
    3. 代词与碎片惩罚 (-0.30 ~ 0.0)
    """
    score = 0.50
    reasons = []

    # 1. 实体识别打分
    has_specific_number = bool(re.search(r"(\d{2,}|套|个|吨|批)", query))
    has_business_term = bool(re.search(r"(BankA|BankB|富民|Commercial|专票|含税|含运费|昆明|送昆明|大乐透|双色球|快乐8|Xray|VPS|10router|Mac|温度|风扇|内存)", query, re.I))
    has_spec_term = bool(re.search(r"(螺栓|法兰|衬胶|镀锌|DN\d+|M\d+|PN\d+|CPU|GPU|PID|SMC)", query, re.I))

    if has_business_term:
        score += 0.25
        reasons.append("命中核心业务/系统主体(+0.25)")
    if has_specific_number or has_spec_term:
        score += 0.15
        reasons.append("命中具体规格/编号/实体参数(+0.15)")

    # 2. 动宾明确度
    has_verb = bool(re.search(r"(修|查|分析|核价|报价|计算|整理|重启|测试|排查|比价|检修|杀掉|起草|写|归档)", query))
    if has_verb:
        score += 0.15
        reasons.append("动作意图谓词明确(+0.15)")

    # 3. 碎片与模糊代词惩罚
    if re.search(r"^(那个|这笔|它|刚才的|弄一下|看一下)$", query.strip()):
        score -= 0.30
        reasons.append("极短代词惩罚(-0.30)")
    elif len(query.strip()) < 6 and not (has_specific_number or has_spec_term):
        score -= 0.15
        reasons.append("短句缺实体轻度惩罚(-0.15)")

    final_conf = max(0.20, min(0.99, round(score, 2)))

    if final_conf >= 0.85:
        tier = "HIGH_CONFIDENCE_AUTO_PRELOAD"
    elif final_conf >= 0.70:
        tier = "MEDIUM_CONFIDENCE_HINT"
    else:
        tier = "LOW_CONFIDENCE_FAIL_OPEN"

    return {
        "confidence": final_conf,
        "tier": tier,
        "reasons": reasons
    }


# ==========================================
# 3. 通用四步全链路任务先锋装配器
# ==========================================

def prefetch_task_assets(query: str, domain: str, confidence_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    通用四步生命周期总线装配：
    1. 什么问题（实体解构 + 本地物理资产 0ms 预取）
    2. 解决方向（破局策略 + 物理/法律/商业硬红线）
    3. 用什么工具（精准工具清单 + 脏数据脱水指南）
    4. 怎么解决与真实核验（实施步骤 + 三源出处核验标准）
    """
    conf = confidence_info.get("confidence", 0.8)
    tier = confidence_info.get("tier", "MEDIUM_CONFIDENCE_HINT")

    preloaded_assets = []
    task_blueprint = ""
    discovered_paths = []
    recommended_tools = []
    safety_redlines = []
    verification_standard = ""

    # ----------------------------------------------------
    # 场景 A：修电脑 / 系统运维 / 硬件调优
    # ----------------------------------------------------
    if domain in ["系统运维", "电脑控制"] or re.search(r"(电脑|mac|发热|温度|风扇|卡顿|卡死|核显|进程|内存|磁盘|网关|xray|vps)", query, re.I):
        discovered_paths.append("/Users/xia/Desktop/阿福知识库/系统治理与运维")
        preloaded_assets.append(MAC_HARDWARE_CARD)
        recommended_tools = ["terminal (只读探针: ps/top/sysctl)", "read_file", "process_manage"]
        safety_redlines = [
            "【红线1·禁毁系统】严禁改动或重新挂载根卷 (Root Volume)，严禁覆盖 OCLP 驱动；",
            "【红线2·禁删记录】严禁清理微信/飞书的本地聊天记录数据库与会话缓存；",
            "【红线3·只读优先】先执行轻量只读检查（查 PID/温度/显存），出具确认清单后再行动；",
            "【红线4·高危动作拍板门禁】凡涉及 kill、rm、reboot、dd 等不可逆破坏性命令，严禁擅自执行！必须出具影响清单，等主人在飞书明确拍板后方可操作。"
        ]
        verification_standard = "【真实性核验】：必须检查命令执行后的真实返回码 (exit 0) 与输出指标；禁止凭空断言'已解决'，必须二次测温/测负载对比！"
        task_blueprint = f"""【做事情的通用四步闭环 · 电脑与系统运维】
1. 什么问题：提取具体故障现象、PID或异常指标，先做只读体检；
2. 解决方向：遵照老 Mac 减负纪律，先止血（杀卡死进程）、后调优（降频释压）、防复发；
3. 用什么工具：只调原生轻量命令（ps, kill, sysctl），绝不装冗余第三方全盘杀毒软件；
4. 怎么解决与核验：执行后必须比对实际系统状态读数，结果真实无误才向主人交付。"""

    # ----------------------------------------------------
    # 场景 B：查询资料价格 / 五金商业采购核价
    # ----------------------------------------------------
    elif domain in ["商贸投标", "物料采购"] or re.search(r"(报价|价格|多少钱|单价|五金|螺栓|法兰|衬胶|镀锌|专票|运费|Commercial)", query, re.I):
        discovered_paths.append("/Users/xia/Desktop/投标报价")
        preloaded_assets.append(PINGMI_COMMERCIAL_CARD)
        recommended_tools = ["web_search_plus (工业品专线)", "web_extract_plus", "execute_code (算账比价)"]
        safety_redlines = [
            "【红线1·税率严守】必须包含 13% 增值税专用发票，未税出厂裸价坚决打回；",
            "【红线2·落地运费】必须核算送达云南昆明的专线实际物流落地运费；",
            "【红线3·虚假引流拦截】低于钢材/原材料现货大宗吨价的诱饵价（如0.1元）坚决剔除；",
            "【红线4·价格时效与保鲜】必须明确标注【报价有效截止日期】与【原材料波动条款】，严禁引用过期历史旧价坑害投标预算！",
            "【红线5·搜索中途脱水】外部检索必须使用工业品专线，Jev 中途自动过滤 80% 广告与中介水文，确保数据一手的真实性。"
        ]
        verification_standard = "【真实性三源核验】：必须附带货源厂家名称/电话/真实URL；吨价交叉算力验算（成品单价不得低于大宗钢材熔炼成本）；明确起订量限制与现货库存周期。"
        task_blueprint = f"""【做事情的通用四步闭环 · 价格查询与商业采购】
1. 什么问题：提取物料材质、通径/规格、压力等级、需求数量与交付地；
2. 解决方向：穿透虚假引流价，锁定真实的【出厂裸价 + 13%专票 + 昆明运费】总成本；
3. 用什么工具：使用工业品现货渠道与精准搜索，Jev 0ms 脱水剔除 90% 广告页面；
4. 怎么解决与核验：通过 Python 算账并核算大宗原料成本，输出标准三段式比价清单。"""

    # ----------------------------------------------------
    # 场景 C：四案诉讼抗辩与司法文书
    # ----------------------------------------------------
    elif domain in ["四案诉讼", "法律抗辩"] or re.search(r"(BankA|BankB|富民|平安|起诉|答辩|质证|案号|法院|法官|利息|违约金)", query):
        matched_case = None
        for case_key, case_info in LITIGATION_CASES_CARD.items():
            if any(k in query for k in case_info["keywords"]):
                matched_case = case_info
                discovered_paths.append(case_info["dir"])
                break
        
        if matched_case:
            preloaded_assets.append(f"【案件档案已预装】{matched_case['title']}\n- 卷宗目录：{matched_case['dir']}\n- 案件事实：{matched_case['core_entities']}")
            recommended_tools = matched_case.get("tools", ["read_file", "legal-hub"])
        else:
            discovered_paths.append("/Users/xia/Desktop/诉讼案件")
            recommended_tools = ["read_file", "legal-hub"]

        safety_redlines = [
            "【红线1·防自认拦截】诉讼文书严禁出现'被迫、借新还旧、无力偿还'等隐性自认词（主人明示特赦除外）；",
            "【红线2·客观认定句】段落首句必须是可以让法官直接复制进判决书的客观认定句；",
            "【红线3·事实认定归主人】涉案金额/流水/法定案号只整理不擅自拍板，事实认定权归主人。"
        ]
        verification_standard = "【真实性核验】：所引法条必须带国家法律法规数据库 (FLK) 唯一编号与生效年份；案卷数字必须逐字对齐原始证据清单！"
        task_blueprint = f"""【做事情的通用四步闭环 · 诉讼文书与法律抗辩】
1. 什么问题：锁定具体争议焦点（管辖权/送达程序/砍头息/虚增本金/未尽格式条款说明）；
2. 解决方向：不诉苦、不卖惨，主攻程序瑕疵与银行举证责任倒逼；
3. 用什么工具：使用 legal-hub 与本地卷宗 read_file，核实官方逐字条文；
4. 怎么解决与核验：出具法官心证认定句，逐条核对涉案金额与法条有效性。"""

    # ----------------------------------------------------
    # 场景 D：生活彩票与统计推演
    # ----------------------------------------------------
    elif domain in ["彩票推演", "彩票数据"] or re.search(r"(大乐透|双色球|快乐8|选号|形态|开奖|冷号)", query):
        discovered_paths.append("/Users/xia/Desktop/彩票")
        preloaded_assets.append("【彩票数据资产底册】\n- 目录：/Users/xia/Desktop/彩票\n- 纪律：大乐透结构E/双色球结构F；死守月500预算；单注排版不折行")
        recommended_tools = ["execute_code (Python回测与选号)", "read_file"]
        safety_redlines = [
            "【红线1·预算锁死】严格死守月500预算红线，不得无节制生成大复式；",
            "【红线2·排版直念】输出单注标准排版，禁止中途折行，直接可用于打票机照念。"
        ]
        verification_standard = "【真实性核验】：出号必须校验前区/后区号码范围与重复性；AC值、和值、跨度必须经由代码精准计算验证。"
        task_blueprint = f"""【做事情的通用四步闭环 · 彩票推演】
1. 什么问题：明确玩法期号与胆拖结构需求；
2. 解决方向：遵循历史高频形态过滤极端畸形；
3. 用什么工具：调用本地 Python 选号引擎计算；
4. 怎么解决与核验：核实号码无重叠超界，直接输出整洁注单。"""

    # ----------------------------------------------------
    # 组装完整的注入挂件
    # ----------------------------------------------------
    prompt_injection = ""
    if preloaded_assets or task_blueprint:
        prompt_injection = "\n\n【Jev 2.0 任务先锋官 · 通用四步全链路资产包】\n"
        if preloaded_assets:
            prompt_injection += "=== [1. 物理底册资产预装] ===\n" + "\n---\n".join(preloaded_assets) + "\n\n"
        if task_blueprint:
            prompt_injection += "=== [2. 标准做事闭环与方向] ===\n" + task_blueprint + "\n\n"
        if safety_redlines:
            prompt_injection += "=== [3. 物理与业务绝对安全红线] ===\n" + "\n".join(safety_redlines) + "\n\n"
        if recommended_tools:
            prompt_injection += f"=== [4. 推荐精准武器清单] ===: {', '.join(recommended_tools)}\n\n"
        if verification_standard:
            prompt_injection += f"=== [5. 交付出厂真实性核验标准] ===\n{verification_standard}\n"
        prompt_injection += """
=== [6. 双账单交付铁律 (Pre & Post Contract)] ===
1. 【开口首段·前置理解对账单】：绝不直接哐哐调用工具！开口第一段必须先给出 3 行对账卡：
   - 📋 任务定性：一句话复述主人要办的核心实事；
   - 💡 管家多想一步：明确主动补齐的材料、隐性假设与安全边界；
   - 🛠️ 预告作战工具：列出接下来要调用的工具/命令名称。
2. 【交付末尾·Jev 机器核验打勾账单】：交活结尾必须包含由 Jev 规则断言的机器核验清单：
   - 严禁假完成！真正做完、经过工具检验并有实测铁证的，必须打绿勾 ✅；
   - 凡是没做完、未达成、报错受阻或中途打断的一律打红叉 ❌；
   - 绝对禁止没做完就擅自打勾欺瞒主人！

【执行纪律】：以上资产与流程由 Jev 0ms 预装，材料已经在桌上，大模型无需再调 search_files 乱查，严格按双账单进入高质量交付！
"""

    return {
        "confidence": conf,
        "tier": tier,
        "discovered_paths": discovered_paths,
        "prompt_injection": prompt_injection,
        "recommended_tools": recommended_tools,
        "has_preloaded_assets": bool(preloaded_assets)
    }
