"""
IntelliCross - SQLite Database Manager
======================================
Persistent storage for routing history, EV events, and audit trail.

Schema designed for:
- High-frequency inserts (WebSocket telemetry)
- Time-series queries for analytics
- Emergency vehicle event tracking
- Compliance audit logging
"""

import sqlite3
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_NAME = "traffic.db"
_db_lock = threading.Lock()


def init_db() -> None:
    """Initialize database with required tables."""
    with _db_lock:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        cursor = conn.cursor()
        
        # Main routing history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS routing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            lane_density TEXT NOT NULL,
            recommended_direction TEXT NOT NULL,
            recommended_speed REAL NOT NULL,
            emergency_detected INTEGER NOT NULL,
            emergency_lane INTEGER,
            vision_mode TEXT DEFAULT 'mock',
            node_states TEXT
        )
        """)
        
        # Emergency vehicle events table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ev_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,  -- 'detected', 'preemption', 'cleared'
            node_id TEXT,
            lane INTEGER,
            speed_kmph REAL,
            distance_m REAL,
            green_wave_triggered INTEGER DEFAULT 0,
            schedule_json TEXT
        )
        """)
        
        # Signal state changes for audit
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            node_id TEXT NOT NULL,
            lane INTEGER NOT NULL,
            old_state TEXT,
            new_state TEXT NOT NULL,
            trigger_reason TEXT,  -- 'normal', 'emergency', 'manual', 'schedule'
            triggered_by TEXT
        )
        """)
        
        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_routing_timestamp ON routing_history(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ev_timestamp ON ev_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_timestamp ON signal_audit(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_node ON signal_audit(node_id)")
        
        conn.commit()
        conn.close()


def insert_record(
    density: List[float],
    direction: str,
    speed: float,
    emergency_detected: int,
    emergency_lane: Optional[int] = None,
    vision_mode: str = "mock",
    node_states: Optional[str] = None
) -> int:
    """
    Insert a routing decision record.
    
    Returns:
        Inserted row ID
    """
    with _db_lock:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO routing_history
        (timestamp, lane_density, recommended_direction, recommended_speed, 
         emergency_detected, emergency_lane, vision_mode, node_states)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            str(density),
            direction,
            speed,
            emergency_detected,
            emergency_lane,
            vision_mode,
            node_states
        ))
        
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id


def log_ev_event(
    event_type: str,
    node_id: Optional[str] = None,
    lane: Optional[int] = None,
    speed_kmph: Optional[float] = None,
    distance_m: Optional[float] = None,
    green_wave_triggered: bool = False,
    schedule_json: Optional[str] = None
) -> int:
    """Log an emergency vehicle event."""
    with _db_lock:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO ev_events
        (timestamp, event_type, node_id, lane, speed_kmph, distance_m, 
         green_wave_triggered, schedule_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            event_type,
            node_id,
            lane,
            speed_kmph,
            distance_m,
            int(green_wave_triggered),
            schedule_json
        ))
        
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id


def log_signal_change(
    node_id: str,
    lane: int,
    new_state: str,
    old_state: Optional[str] = None,
    trigger_reason: str = "normal",
    triggered_by: str = "system"
) -> int:
    """Log signal state change for audit trail."""
    with _db_lock:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO signal_audit
        (timestamp, node_id, lane, old_state, new_state, trigger_reason, triggered_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            node_id,
            lane,
            old_state,
            new_state,
            trigger_reason,
            triggered_by
        ))
        
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return row_id


def get_history(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get routing history with pagination.
    
    Returns list of dicts with parsed JSON fields.
    """
    with _db_lock:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM routing_history
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            item = dict(row)
            # Parse JSON fields
            try:
                import json
                item['lane_density'] = json.loads(item['lane_density'].replace("'", '"'))
            except:
                item['lane_density'] = item['lane_density']
            result.append(item)
        
        return result


def get_ev_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Get emergency vehicle event history."""
    with _db_lock:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM ev_events
        ORDER BY timestamp DESC
        LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


def get_signal_audit(node_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Get signal change audit trail."""
    with _db_lock:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if node_id:
            cursor.execute("""
            SELECT * FROM signal_audit
            WHERE node_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """, (node_id, limit))
        else:
            cursor.execute("""
            SELECT * FROM signal_audit
            ORDER BY timestamp DESC
            LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


def get_analytics_summary(hours: int = 24) -> Dict[str, Any]:
    """Get analytical summary for dashboard."""
    with _db_lock:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        cursor = conn.cursor()
        
        # Total decisions
        cursor.execute("""
        SELECT COUNT(*) FROM routing_history
        WHERE timestamp >= datetime('now', ?)
        """, (f'-{hours} hours',))
        total_decisions = cursor.fetchone()[0]
        
        # Emergency events
        cursor.execute("""
        SELECT COUNT(*) FROM routing_history
        WHERE emergency_detected = 1 AND timestamp >= datetime('now', ?)
        """, (f'-{hours} hours',))
        emergency_count = cursor.fetchone()[0]
        
        # Avg speed recommendation
        cursor.execute("""
        SELECT AVG(recommended_speed) FROM routing_history
        WHERE timestamp >= datetime('now', ?)
        """, (f'-{hours} hours',))
        avg_speed = cursor.fetchone()[0] or 0
        
        # Direction distribution
        cursor.execute("""
        SELECT recommended_direction, COUNT(*) as cnt
        FROM routing_history
        WHERE timestamp >= datetime('now', ?)
        GROUP BY recommended_direction
        """, (f'-{hours} hours',))
        directions = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "period_hours": hours,
            "total_decisions": total_decisions,
            "emergency_events": emergency_count,
            "emergency_rate": emergency_count / total_decisions if total_decisions > 0 else 0,
            "average_recommended_speed_kmph": round(avg_speed, 1),
            "direction_distribution": directions
        }