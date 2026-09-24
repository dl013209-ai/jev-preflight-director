"""
Jev Semantic Auto-Distiller & Skill Sync Engine (v2.2.0)
Continuous feature extraction, domain clustering, and cold-noise pruning engine for local zero-latency caches.
Also auto-synchronizes 'metadata.jev_router' from all workspace skills into local fast-cache patterns.
"""

import os
import re
import time
import sqlite3
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_STOP_WORDS = {
    "帮我", "请问", "看一下", "看下", "怎么", "如何", "一下", "这个", "那个",
    "什么", "今天", "明天", "现在", "可以", "能不能", "有没有", "谢谢",
    "你好", "阿福", "管家", "有点", "很多", "做个", "弄个", "查查", "搜搜"
}

def sync_skills_to_patterns(cursor: sqlite3.Cursor, skills_root: Path, now: float) -> int:
    """Scan all SKILL.md in skills_root and sync jev_router metadata to local patterns cache."""
    if not skills_root.exists():
        return 0
    
    count = 0
    for skill_file in skills_root.rglob("SKILL.md"):
        try:
            content = skill_file.read_text(encoding="utf-8", errors="ignore")
            if not content.startswith("---"):
                continue
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue
            
            import yaml
            meta = yaml.safe_load(parts[1])
            if not isinstance(meta, dict):
                continue
            
            skill_name = meta.get("name", skill_file.parent.name)
            m_data = meta.get("metadata", {})
            if not isinstance(m_data, dict):
                continue
            
            router_cfg = m_data.get("jev_router", {})
            if not router_cfg or not isinstance(router_cfg, dict):
                continue
            
            domain = router_cfg.get("domain", "DomainExpert")
            topic = f"Skill-{skill_name}"
            keywords = router_cfg.get("keywords", [])
            priority = router_cfg.get("priority", 10)
            
            for kw in keywords:
                if len(kw) < 2:
                    continue
                cursor.execute("""
                    INSERT INTO jev_learned_patterns (pattern, domain, topic, weight, last_hit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(pattern) DO UPDATE SET
                        domain = excluded.domain,
                        topic = excluded.topic,
                        weight = MAX(weight, excluded.weight),
                        last_hit = excluded.last_hit
                """, (kw, domain, topic, priority, now, now))
            count += 1
        except Exception:
            continue
    return count

def extract_features(text: str, stop_words: Optional[set] = None) -> List[str]:
    """Extract informative 2-6 character phrases from raw text."""
    if stop_words is None:
        stop_words = DEFAULT_STOP_WORDS

    cleaned = re.sub(r"[^\w\s\u4e00-\u9fa5]", " ", text)
    words = [w.strip() for w in cleaned.split() if w.strip()]
    features = []

    for chunk in words:
        if len(chunk) < 2:
            continue
        if chunk in stop_words:
            continue
        c_matches = re.findall(r"[\u4e00-\u9fa5]{2,6}", chunk)
        for m in c_matches:
            if m not in stop_words:
                features.append(m)
        e_matches = re.findall(r"[a-zA-Z0-9_\-]{3,15}", chunk)
        for em in e_matches:
            features.append(em.lower())

    return features

class SemanticDistiller:
    def __init__(self, db_path: str, skills_dir: Optional[str] = None):
        self.db_path = Path(db_path)
        self.skills_dir = Path(skills_dir) if skills_dir else None

    def run(self) -> Dict[str, Any]:
        """Execute distillation batch: process pending records, sync skills, and prune 30d cold patterns."""
        if not self.db_path.exists():
            return {"status": "skipped", "reason": "database does not exist"}

        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        c = conn.cursor()
        now = time.time()

        synced_skills = 0
        if self.skills_dir and self.skills_dir.exists():
            synced_skills = sync_skills_to_patterns(c, self.skills_dir, now)

        rows = c.execute("""
            SELECT id, raw_text, domain, topic, confidence 
            FROM jev_semantic_staging 
            WHERE status = 'pending' 
            ORDER BY id ASC LIMIT 500
        """).fetchall()

        new_count = 0
        updated_count = 0

        if rows:
            domain_features: Dict[str, List[str]] = {}
            for row_id, raw_text, domain, topic, conf in rows:
                if domain not in domain_features:
                    domain_features[domain] = []
                domain_features[domain].extend(extract_features(raw_text))

            for domain, feats in domain_features.items():
                if not feats:
                    continue
                top_k = Counter(feats).most_common(10)
                topic_name = f"auto-distill-{domain}"

                for word, freq in top_k:
                    if len(word) < 2:
                        continue
                    existing = c.execute("SELECT weight FROM jev_learned_patterns WHERE pattern = ?", (word,)).fetchone()
                    if existing:
                        c.execute("""
                            UPDATE jev_learned_patterns 
                            SET weight = weight + ?, last_hit = ?, topic = ?
                            WHERE pattern = ?
                        """, (freq, now, topic_name, word))
                        updated_count += 1
                    else:
                        c.execute("""
                            INSERT INTO jev_learned_patterns (pattern, domain, topic, weight, last_hit, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (word, domain, topic_name, freq, now, now))
                        new_count += 1

            processed_ids = [r[0] for r in rows]
            c.executemany("UPDATE jev_semantic_staging SET status = 'distilled' WHERE id = ?", [(i,) for i in processed_ids])

        # Prune cold records older than 30 days
        thirty_days_ago = now - (30 * 86400)
        c.execute("DELETE FROM jev_learned_patterns WHERE last_hit < ? AND weight <= 1", (thirty_days_ago,))
        pruned_count = c.rowcount

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "processed_samples": len(rows),
            "new_patterns": new_count,
            "updated_patterns": updated_count,
            "synced_skills": synced_skills,
            "pruned_patterns": pruned_count
        }
