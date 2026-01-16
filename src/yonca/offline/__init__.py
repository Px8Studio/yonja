"""
Yonca AI - Offline Support Layer
Enables the app to work in low-connectivity environments.
"""
import json
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class CacheEntry:
    """A cached data entry."""
    key: str
    data: str  # JSON serialized
    created_at: str
    expires_at: Optional[str]
    checksum: str


@dataclass
class SyncQueueItem:
    """An item waiting to be synced to the server."""
    id: int
    operation: str  # 'create', 'update', 'delete'
    entity_type: str  # 'recommendation', 'task', 'message'
    entity_id: str
    data: str  # JSON serialized
    created_at: str
    synced: bool
    retry_count: int


class OfflineStorage:
    """
    SQLite-based offline storage for Yonca AI.
    Provides caching and sync queue functionality.
    """
    
    def __init__(self, db_path: str = "yonca_offline.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Cache table for offline data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                checksum TEXT NOT NULL
            )
        """)
        
        # Sync queue for pending operations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                synced INTEGER DEFAULT 0,
                retry_count INTEGER DEFAULT 0
            )
        """)
        
        # Farm profiles cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS farms (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        
        # Recommendations cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                farm_id TEXT NOT NULL,
                data TEXT NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Chat history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                intent TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ============= Cache Methods =============
    
    def cache_set(
        self,
        key: str,
        data: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Store data in the cache.
        
        Args:
            key: Cache key
            data: Data to store (will be JSON serialized)
            ttl_seconds: Time to live in seconds (optional)
            
        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        json_data = json.dumps(data, default=str)
        checksum = hashlib.md5(json_data.encode()).hexdigest()
        created_at = datetime.now().isoformat()
        expires_at = None
        
        if ttl_seconds:
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO cache (key, data, created_at, expires_at, checksum)
            VALUES (?, ?, ?, ?, ?)
        """, (key, json_data, created_at, expires_at, checksum))
        
        conn.commit()
        conn.close()
        return True
    
    def cache_get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT data, expires_at FROM cache WHERE key = ?
        """, (key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        data, expires_at = row
        
        # Check expiration
        if expires_at:
            if datetime.fromisoformat(expires_at) < datetime.now():
                self.cache_delete(key)
                return None
        
        return json.loads(data)
    
    def cache_delete(self, key: str) -> bool:
        """Delete a cache entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()
        conn.close()
        return True
    
    def cache_clear(self) -> bool:
        """Clear all cache entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache")
        conn.commit()
        conn.close()
        return True
    
    # ============= Sync Queue Methods =============
    
    def queue_add(
        self,
        operation: str,
        entity_type: str,
        entity_id: str,
        data: Any
    ) -> int:
        """
        Add an operation to the sync queue.
        
        Args:
            operation: 'create', 'update', or 'delete'
            entity_type: Type of entity
            entity_id: Entity identifier
            data: Entity data
            
        Returns:
            Queue item ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sync_queue (operation, entity_type, entity_id, data, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            operation,
            entity_type,
            entity_id,
            json.dumps(data, default=str),
            datetime.now().isoformat()
        ))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return item_id
    
    def queue_get_pending(self, limit: int = 50) -> list[SyncQueueItem]:
        """Get pending items from the sync queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, operation, entity_type, entity_id, data, created_at, synced, retry_count
            FROM sync_queue
            WHERE synced = 0
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))
        
        items = []
        for row in cursor.fetchall():
            items.append(SyncQueueItem(
                id=row[0],
                operation=row[1],
                entity_type=row[2],
                entity_id=row[3],
                data=row[4],
                created_at=row[5],
                synced=bool(row[6]),
                retry_count=row[7],
            ))
        
        conn.close()
        return items
    
    def queue_mark_synced(self, item_id: int) -> bool:
        """Mark a queue item as synced."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sync_queue SET synced = 1 WHERE id = ?",
            (item_id,)
        )
        conn.commit()
        conn.close()
        return True
    
    def queue_increment_retry(self, item_id: int) -> bool:
        """Increment the retry count for a queue item."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sync_queue SET retry_count = retry_count + 1 WHERE id = ?",
            (item_id,)
        )
        conn.commit()
        conn.close()
        return True
    
    # ============= Farm Cache Methods =============
    
    def save_farm(self, farm_id: str, farm_data: dict) -> bool:
        """Save a farm profile to offline storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO farms (id, data, last_updated)
            VALUES (?, ?, ?)
        """, (
            farm_id,
            json.dumps(farm_data, default=str),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        return True
    
    def get_farm(self, farm_id: str) -> Optional[dict]:
        """Get a farm profile from offline storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT data FROM farms WHERE id = ?", (farm_id,))
        row = cursor.fetchone()
        conn.close()
        
        return json.loads(row[0]) if row else None
    
    def get_all_farms(self) -> list[dict]:
        """Get all farm profiles from offline storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT data FROM farms")
        farms = [json.loads(row[0]) for row in cursor.fetchall()]
        conn.close()
        
        return farms
    
    # ============= Recommendations Cache =============
    
    def save_recommendations(
        self,
        farm_id: str,
        recommendations: list[dict],
        target_date: date
    ) -> bool:
        """Save recommendations to offline storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for rec in recommendations:
            cursor.execute("""
                INSERT OR REPLACE INTO recommendations (id, farm_id, data, date, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rec.get('id', ''),
                farm_id,
                json.dumps(rec, default=str),
                str(target_date),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        return True
    
    def get_recommendations(
        self,
        farm_id: str,
        target_date: Optional[date] = None
    ) -> list[dict]:
        """Get cached recommendations for a farm."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if target_date:
            cursor.execute("""
                SELECT data FROM recommendations
                WHERE farm_id = ? AND date = ?
                ORDER BY created_at DESC
            """, (farm_id, str(target_date)))
        else:
            cursor.execute("""
                SELECT data FROM recommendations
                WHERE farm_id = ?
                ORDER BY date DESC, created_at DESC
            """, (farm_id,))
        
        recommendations = [json.loads(row[0]) for row in cursor.fetchall()]
        conn.close()
        
        return recommendations
    
    # ============= Chat History =============
    
    def save_chat_message(
        self,
        user_message: str,
        bot_response: str,
        intent: Optional[str] = None,
        farm_id: Optional[str] = None
    ) -> int:
        """Save a chat exchange to history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO chat_history (farm_id, user_message, bot_response, intent, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            farm_id,
            user_message,
            bot_response,
            intent,
            datetime.now().isoformat()
        ))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_chat_history(
        self,
        farm_id: Optional[str] = None,
        limit: int = 50
    ) -> list[dict]:
        """Get chat history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if farm_id:
            cursor.execute("""
                SELECT id, farm_id, user_message, bot_response, intent, created_at
                FROM chat_history
                WHERE farm_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (farm_id, limit))
        else:
            cursor.execute("""
                SELECT id, farm_id, user_message, bot_response, intent, created_at
                FROM chat_history
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row[0],
                'farm_id': row[1],
                'user_message': row[2],
                'bot_response': row[3],
                'intent': row[4],
                'created_at': row[5],
            })
        
        conn.close()
        return history


class OfflineSyncManager:
    """
    Manages synchronization between offline storage and the server.
    """
    
    def __init__(self, storage: OfflineStorage):
        self.storage = storage
        self.is_online = True
    
    def check_connectivity(self) -> bool:
        """Check if the device has internet connectivity."""
        # In a real implementation, this would ping the server
        # For the prototype, we simulate connectivity
        import random
        self.is_online = random.random() > 0.1  # 90% online
        return self.is_online
    
    async def sync_pending_items(self) -> dict:
        """
        Sync all pending items to the server.
        
        Returns:
            Summary of sync results
        """
        if not self.check_connectivity():
            return {
                'status': 'offline',
                'synced': 0,
                'failed': 0,
                'pending': len(self.storage.queue_get_pending())
            }
        
        pending = self.storage.queue_get_pending()
        synced = 0
        failed = 0
        
        for item in pending:
            try:
                # In real implementation, send to server
                # await self._send_to_server(item)
                
                # Mark as synced
                self.storage.queue_mark_synced(item.id)
                synced += 1
                
            except Exception as e:
                self.storage.queue_increment_retry(item.id)
                failed += 1
        
        return {
            'status': 'completed',
            'synced': synced,
            'failed': failed,
            'pending': len(self.storage.queue_get_pending())
        }
    
    def prefetch_data(self, farm_ids: list[str]) -> dict:
        """
        Prefetch data for offline use.
        
        Args:
            farm_ids: List of farm IDs to prefetch
            
        Returns:
            Summary of prefetched data
        """
        from yonca.data.scenarios import get_scenario_farms
        from yonca.core.engine import recommendation_engine
        
        farms = get_scenario_farms()
        prefetched = {'farms': 0, 'recommendations': 0}
        
        for farm_id in farm_ids:
            if farm_id in farms:
                farm = farms[farm_id]
                
                # Save farm profile
                self.storage.save_farm(farm_id, farm.model_dump())
                prefetched['farms'] += 1
                
                # Generate and save recommendations
                recommendations = recommendation_engine.generate_recommendations(farm)
                rec_dicts = [r.model_dump() for r in recommendations]
                self.storage.save_recommendations(farm_id, rec_dicts, date.today())
                prefetched['recommendations'] += len(recommendations)
        
        return prefetched


# Singleton instances
offline_storage = OfflineStorage()
sync_manager = OfflineSyncManager(offline_storage)
