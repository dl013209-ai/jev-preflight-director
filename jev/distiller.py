"""
Jev Semantic Auto-Distiller
Continuous feature extraction, domain clustering, and cold-noise pruning engine for local zero-latency caches.
"""

import os
import re
import time
import sqlite3
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any, Optional

DEFAULT_STOP_WORDS = {
    "please", "help", "check", "how", "what", "can", "could", "would",
    "帮我", "请问", "看一下", "看下", "怎么", "如何", "一下", "这个", "那个",
    "什么", "今天", "明天", "现在", "可以", "能不能", "有没有", "谢谢",
    "你好", "有点", "很多", "做个", "弄个", "查查", "搜搜"
}

def extract_features(text: str, stop_words: Optional[set] = None) -> List[str]:
    """Extract domain entity tokens and n-grams (length 2-6) from raw input."""
    sw = stop_words or DEFAULT_STOP_WORDS
    cleaned = re.sub(r"[^\w\s\u4e00-\u9fa5]", " ", text)
    words = [w.strip() for w in cleaned.split() if w.strip()]
    features = []

    for chunk in words:
        if len(chunk) < 2 or chunk in sw:
            continue
        c_matches = re.findall(r"[\u4e00-\u9fa5]{2,6}", chunk)
        for m in c_matches:
            if m not in sw:
                features.append(m)
        alnum_matches = re.findall(r"[A-Za-z0-9_-]{3,15}", chunk)
        for a in alnum_matches:
            features.append(a.lower())

    return features

class SemanticDistiller:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

    def distill(self, max_samples: int = 500) -> Dict[str, Any]:
        """Run clustering, pattern distillation, and cache compaction."""
        if not self.db_path.exists():
            return {"status": "error", "message": "Database not found"}

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        c = conn.cursor()

        # Fetch pending live samples
        rows = c.execute("""
            SELECT id, raw_text, domain, topic, confidence 
            FROM jev_semantic_staging 
            WHERE status = 'pending'
            ORDER BY id ASC LIMIT ?
        """, (max_samples,)).fetchall()

        if not rows:
            conn.close()
            return {"status": "noop", "processed_samples": 0}

        domain_features: Dict[str, List[str]] = {}
        for row_id, raw_text, domain, topic, conf in rows:
            if domain not in domain_features:
                domain_features[domain] = []
            domain_features[domain].extend(extract_features(raw_text))

        now = time.time()
        new_count = 0
        updated_count = 0

        for domain, feats in domain_features.items():
            if not feats:
                continue
            top_k = Counter(feats).most_common(10)
            topic_label = f"AutoDistill-{domain}"

            for word, freq in top_k:
                if len(word) < 2:
                    continue
                existing = c.execute("SELECT weight FROM jev_learned_patterns WHERE pattern = ?", (word,)).fetchone()
                if existing:
                    c.execute("""
                        UPDATE jev_learned_patterns 
                        SET weight = weight + ?, last_hit = ?, topic = ?
                        WHERE pattern = ?
                    """, (freq, now, topic_label, word))
                    updated_count += 1
                else:
                    c.execute("""
                        INSERT INTO jev_learned_patterns (pattern, domain, topic, weight, last_hit, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (word, domain, topic_label, freq, now, now))
                    new_count += 1

        processed_ids = [r[0] for r in rows]
        c.executemany("UPDATE jev_semantic_staging SET status = 'distilled' WHERE id = ?", [(i,) for i in processed_ids])

        # Drop cold patterns unhit for 30+ days
        cutoff = now - (30 * 86400)
        c.execute("DELETE FROM jev_learned_patterns WHERE last_hit < ? AND weight <= 1", (cutoff,))
        pruned_count = c.rowcount

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "processed_samples": len(rows),
            "new_patterns": new_count,
            "updated_patterns": updated_count,
            "pruned_cold": pruned_count
        }
