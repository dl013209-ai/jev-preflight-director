# -*- coding: utf-8 -*-
"""jev_context.py - Jev 单轮指标隔离采集器"""
import threading
from dataclasses import dataclass
from typing import Optional

@dataclass
class JevTurnStats:
    calls: int = 0
    assigned_model: Optional[str] = None
    is_fallback: bool = False
    eval_count: int = 0

_lock = threading.Lock()
_global_stats = JevTurnStats()

def reset_turn_stats() -> JevTurnStats:
    """轮首重置（在 run_turn_runner 轮首触发）"""
    global _global_stats
    with _lock:
        _global_stats = JevTurnStats()
        return _global_stats

def record_jev_call(assigned_model: Optional[str] = None, is_fallback: bool = False, eval_count: int = 0):
    """工具被调用时累加（在 jev_classify handler 触发，线程安全支持子任务）"""
    global _global_stats
    with _lock:
        _global_stats.calls += 1
        if assigned_model:
            _global_stats.assigned_model = assigned_model
        if is_fallback:
            _global_stats.is_fallback = True
        if eval_count > 0:
            _global_stats.eval_count += eval_count

def get_turn_stats() -> JevTurnStats:
    """轮末读取指标（包含所有子任务线程累计）"""
    with _lock:
        return JevTurnStats(
            calls=_global_stats.calls,
            assigned_model=_global_stats.assigned_model,
            is_fallback=_global_stats.is_fallback,
            eval_count=_global_stats.eval_count,
        )
