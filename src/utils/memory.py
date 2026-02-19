"""
Persistent Memory System for Kencan
Inspired by claude-mem - stores conversation context and observations across sessions
"""

import sqlite3
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PersistentMemory:
    """SQLite-based persistent memory for Kencan sessions"""
    
    def __init__(self, db_path: str = None):
        """Initialize memory system"""
        if db_path is None:
            # Default to user's home directory
            db_dir = Path.home() / '.kencan'
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / 'memory.db')
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Sessions table
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    summary TEXT
                );
                
                -- Observations (actions taken, results, learnings)
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    type TEXT,  -- 'action', 'result', 'learning', 'user_preference'
                    content TEXT,
                    metadata TEXT,  -- JSON
                    importance INTEGER DEFAULT 5,  -- 1-10 scale
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                );
                
                -- Summaries (compressed context from past sessions)
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_ids TEXT,  -- JSON array of session IDs
                    summary TEXT,
                    tokens_saved INTEGER
                );
                
                -- User preferences learned over time
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    confidence REAL DEFAULT 0.5,  -- 0-1
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    times_observed INTEGER DEFAULT 1
                );
                
                -- Full-text search index
                CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
                    content,
                    content='observations',
                    content_rowid='id'
                );
                
                -- Triggers to keep FTS in sync
                CREATE TRIGGER IF NOT EXISTS observations_ai AFTER INSERT ON observations BEGIN
                    INSERT INTO observations_fts(rowid, content) VALUES (new.id, new.content);
                END;
                
                CREATE TRIGGER IF NOT EXISTS observations_ad AFTER DELETE ON observations BEGIN
                    INSERT INTO observations_fts(observations_fts, rowid, content) 
                    VALUES('delete', old.id, old.content);
                END;
            """)
    
    def start_session(self) -> str:
        """Start a new session and return session ID"""
        session_id = hashlib.sha256(
            f"{datetime.now().isoformat()}-{id(self)}".encode()
        ).hexdigest()[:16]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (id) VALUES (?)",
                (session_id,)
            )
        
        logger.info(f"Started memory session: {session_id}")
        return session_id
    
    def end_session(self, session_id: str, summary: str = None):
        """End a session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE sessions SET ended_at = CURRENT_TIMESTAMP, summary = ? WHERE id = ?",
                (summary, session_id)
            )
        logger.info(f"Ended memory session: {session_id}")
    
    def record_observation(self, session_id: str, obs_type: str, content: str,
                          metadata: Dict = None, importance: int = 5):
        """Record an observation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO observations (session_id, type, content, metadata, importance)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, obs_type, content, json.dumps(metadata or {}), importance)
            )
    
    def record_action(self, session_id: str, action: str, parameters: Dict, 
                      result: Dict, importance: int = 5):
        """Record an action taken"""
        content = f"Action: {action}\nParameters: {json.dumps(parameters)}\nResult: {json.dumps(result)}"
        self.record_observation(
            session_id, 'action', content,
            {'action': action, 'parameters': parameters, 'result': result},
            importance
        )
    
    def record_learning(self, session_id: str, learning: str, importance: int = 7):
        """Record something learned"""
        self.record_observation(session_id, 'learning', learning, importance=importance)
    
    def update_preference(self, key: str, value: str, confidence: float = 0.5):
        """Update a learned user preference"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO preferences (key, value, confidence, times_observed)
                   VALUES (?, ?, ?, 1)
                   ON CONFLICT(key) DO UPDATE SET
                       value = excluded.value,
                       confidence = MIN(1.0, confidence + 0.1),
                       times_observed = times_observed + 1,
                       last_updated = CURRENT_TIMESTAMP""",
                (key, value, confidence)
            )
    
    def get_preferences(self) -> Dict[str, Any]:
        """Get all learned preferences"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT key, value, confidence FROM preferences WHERE confidence >= 0.3"
            ).fetchall()
            return {row['key']: {'value': row['value'], 'confidence': row['confidence']} 
                    for row in rows}
    
    def search_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """Search past observations using full-text search"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT o.*, s.started_at as session_date
                   FROM observations_fts f
                   JOIN observations o ON f.rowid = o.id
                   JOIN sessions s ON o.session_id = s.id
                   WHERE observations_fts MATCH ?
                   ORDER BY o.importance DESC, o.timestamp DESC
                   LIMIT ?""",
                (query, limit)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def get_recent_context(self, hours: int = 24, limit: int = 20) -> List[Dict]:
        """Get recent observations for context"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cutoff = datetime.now() - timedelta(hours=hours)
            rows = conn.execute(
                """SELECT * FROM observations 
                   WHERE timestamp >= ? 
                   ORDER BY importance DESC, timestamp DESC 
                   LIMIT ?""",
                (cutoff.isoformat(), limit)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def get_high_importance_memories(self, min_importance: int = 7, 
                                      limit: int = 10) -> List[Dict]:
        """Get high-importance memories across all sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT o.*, s.started_at as session_date
                   FROM observations o
                   JOIN sessions s ON o.session_id = s.id
                   WHERE o.importance >= ?
                   ORDER BY o.timestamp DESC
                   LIMIT ?""",
                (min_importance, limit)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def build_context_prompt(self, current_query: str = None) -> str:
        """Build a context prompt from memory for injection into conversations"""
        parts = []
        
        # Add preferences
        prefs = self.get_preferences()
        if prefs:
            pref_lines = [f"- {k}: {v['value']}" for k, v in prefs.items()]
            parts.append("## User Preferences\n" + "\n".join(pref_lines))
        
        # Add recent high-importance memories
        important = self.get_high_importance_memories(limit=5)
        if important:
            mem_lines = [f"- [{m['type']}] {m['content'][:200]}" for m in important]
            parts.append("## Important Past Context\n" + "\n".join(mem_lines))
        
        # Search for relevant memories if query provided
        if current_query:
            relevant = self.search_memory(current_query, limit=3)
            if relevant:
                rel_lines = [f"- {m['content'][:200]}" for m in relevant]
                parts.append("## Relevant Past Interactions\n" + "\n".join(rel_lines))
        
        return "\n\n".join(parts) if parts else ""
    
    def cleanup_old_memories(self, days: int = 30):
        """Clean up old, low-importance memories"""
        with sqlite3.connect(self.db_path) as conn:
            cutoff = datetime.now() - timedelta(days=days)
            conn.execute(
                """DELETE FROM observations 
                   WHERE timestamp < ? AND importance < 5""",
                (cutoff.isoformat(),)
            )
            conn.execute("VACUUM")
    
    def get_stats(self) -> Dict[str, int]:
        """Get memory statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            stats['sessions'] = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            stats['observations'] = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            stats['preferences'] = conn.execute("SELECT COUNT(*) FROM preferences").fetchone()[0]
            return stats
