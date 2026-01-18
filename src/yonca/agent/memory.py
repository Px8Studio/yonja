# src/yonca/agent/memory.py
"""Redis-based checkpointer for LangGraph state persistence.

Provides thread-based memory so farmers can resume conversations
even after closing the app. Uses the existing Redis infrastructure.
"""

import json
from datetime import datetime
from typing import Any, AsyncIterator, Optional

import redis.asyncio as redis
import structlog

from yonca.config import settings
from yonca.data.redis_client import RedisClient


log = structlog.get_logger()

# Try to import Redis checkpointer
try:
    from langgraph.checkpoint.redis import RedisSaver
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    log.warning("Redis checkpointer not available, install langgraph-checkpoint-redis")

# In-memory fallback
from langgraph.checkpoint.memory import MemorySaver


# ============================================================
# Redis Keys
# ============================================================

class CheckpointKeys:
    """Redis key patterns for checkpointing."""
    
    # Checkpoint storage
    CHECKPOINT_PREFIX = "yonca:checkpoint:"
    CHECKPOINT_METADATA = "yonca:checkpoint:metadata:"
    
    # Thread management
    THREAD_INDEX = "yonca:threads"
    THREAD_USER_MAP = "yonca:thread:user:"
    
    # TTLs (in seconds)
    CHECKPOINT_TTL = 86400 * 7  # 7 days - conversation history
    THREAD_INDEX_TTL = 86400 * 30  # 30 days - thread index
    
    @classmethod
    def checkpoint_key(cls, thread_id: str, checkpoint_id: str) -> str:
        """Generate key for a specific checkpoint."""
        return f"{cls.CHECKPOINT_PREFIX}{thread_id}:{checkpoint_id}"
    
    @classmethod
    def thread_checkpoints_key(cls, thread_id: str) -> str:
        """Generate key for thread's checkpoint list."""
        return f"{cls.CHECKPOINT_PREFIX}{thread_id}:checkpoints"
    
    @classmethod
    def metadata_key(cls, thread_id: str, checkpoint_id: str) -> str:
        """Generate key for checkpoint metadata."""
        return f"{cls.CHECKPOINT_METADATA}{thread_id}:{checkpoint_id}"
    
    @classmethod
    def user_threads_key(cls, user_id: str) -> str:
        """Generate key for user's thread list."""
        return f"{cls.THREAD_USER_MAP}{user_id}"


# ============================================================
# Checkpoint Data Models
# ============================================================

class CheckpointMetadata:
    """Metadata for a checkpoint."""
    
    def __init__(
        self,
        checkpoint_id: str,
        thread_id: str,
        created_at: datetime | None = None,
        parent_id: str | None = None,
        step: int = 0,
        node: str | None = None,
    ):
        self.checkpoint_id = checkpoint_id
        self.thread_id = thread_id
        self.created_at = created_at or datetime.utcnow()
        self.parent_id = parent_id
        self.step = step
        self.node = node
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "thread_id": self.thread_id,
            "created_at": self.created_at.isoformat(),
            "parent_id": self.parent_id,
            "step": self.step,
            "node": self.node,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CheckpointMetadata":
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            thread_id=data["thread_id"],
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            parent_id=data.get("parent_id"),
            step=data.get("step", 0),
            node=data.get("node"),
        )


class Checkpoint:
    """A checkpoint of the agent state."""
    
    def __init__(
        self,
        metadata: CheckpointMetadata,
        state: dict[str, Any],
    ):
        self.metadata = metadata
        self.state = state
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return {
            "metadata": self.metadata.to_dict(),
            "state": self.state,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        """Create from dictionary."""
        return cls(
            metadata=CheckpointMetadata.from_dict(data["metadata"]),
            state=data["state"],
        )


# ============================================================
# Redis Checkpointer
# ============================================================

class RedisCheckpointer:
    """Redis-based checkpointer for LangGraph.
    
    Stores agent state at each step, enabling:
    - Conversation resumption after app close
    - State recovery on errors
    - Audit trails for compliance
    
    Example:
        ```python
        checkpointer = RedisCheckpointer()
        
        # Save checkpoint
        await checkpointer.put(
            thread_id="conv_123",
            checkpoint_id="step_1",
            state=agent_state,
        )
        
        # Get latest checkpoint
        checkpoint = await checkpointer.get_latest(thread_id="conv_123")
        
        # Resume from checkpoint
        state = checkpoint.state
        ```
    """
    
    def __init__(self):
        """Initialize the checkpointer."""
        self._client: redis.Redis | None = None
    
    async def _get_client(self) -> redis.Redis:
        """Get Redis client."""
        if self._client is None:
            self._client = await RedisClient.get_client()
        return self._client
    
    # ===== Core Operations =====
    
    async def put(
        self,
        thread_id: str,
        checkpoint_id: str,
        state: dict[str, Any],
        parent_id: str | None = None,
        step: int = 0,
        node: str | None = None,
    ) -> Checkpoint:
        """Save a checkpoint.
        
        Args:
            thread_id: Conversation thread ID
            checkpoint_id: Unique checkpoint ID (typically step-based)
            state: Agent state to save
            parent_id: Parent checkpoint ID for lineage
            step: Step number in the graph
            node: Node that created this checkpoint
            
        Returns:
            The saved Checkpoint
        """
        client = await self._get_client()
        
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            thread_id=thread_id,
            parent_id=parent_id,
            step=step,
            node=node,
        )
        
        checkpoint = Checkpoint(metadata=metadata, state=state)
        
        # Store checkpoint
        checkpoint_key = CheckpointKeys.checkpoint_key(thread_id, checkpoint_id)
        await client.set(
            checkpoint_key,
            json.dumps(checkpoint.to_dict()),
            ex=CheckpointKeys.CHECKPOINT_TTL,
        )
        
        # Add to thread's checkpoint list (sorted set by step)
        checkpoints_key = CheckpointKeys.thread_checkpoints_key(thread_id)
        await client.zadd(checkpoints_key, {checkpoint_id: step})
        await client.expire(checkpoints_key, CheckpointKeys.CHECKPOINT_TTL)
        
        # Update thread index
        await client.sadd(CheckpointKeys.THREAD_INDEX, thread_id)
        
        return checkpoint
    
    async def get(
        self,
        thread_id: str,
        checkpoint_id: str,
    ) -> Checkpoint | None:
        """Get a specific checkpoint.
        
        Args:
            thread_id: Conversation thread ID
            checkpoint_id: Checkpoint ID to retrieve
            
        Returns:
            Checkpoint or None if not found
        """
        client = await self._get_client()
        
        checkpoint_key = CheckpointKeys.checkpoint_key(thread_id, checkpoint_id)
        data = await client.get(checkpoint_key)
        
        if data is None:
            return None
        
        return Checkpoint.from_dict(json.loads(data))
    
    async def get_latest(self, thread_id: str) -> Checkpoint | None:
        """Get the most recent checkpoint for a thread.
        
        Args:
            thread_id: Conversation thread ID
            
        Returns:
            Latest checkpoint or None if thread has no checkpoints
        """
        client = await self._get_client()
        
        checkpoints_key = CheckpointKeys.thread_checkpoints_key(thread_id)
        
        # Get highest-scored checkpoint ID
        result = await client.zrevrange(checkpoints_key, 0, 0)
        
        if not result:
            return None
        
        checkpoint_id = result[0]
        return await self.get(thread_id, checkpoint_id)
    
    async def list_checkpoints(
        self,
        thread_id: str,
        limit: int = 10,
    ) -> list[CheckpointMetadata]:
        """List checkpoints for a thread.
        
        Args:
            thread_id: Conversation thread ID
            limit: Maximum number to return
            
        Returns:
            List of checkpoint metadata, newest first
        """
        client = await self._get_client()
        
        checkpoints_key = CheckpointKeys.thread_checkpoints_key(thread_id)
        checkpoint_ids = await client.zrevrange(checkpoints_key, 0, limit - 1)
        
        result = []
        for checkpoint_id in checkpoint_ids:
            checkpoint = await self.get(thread_id, checkpoint_id)
            if checkpoint:
                result.append(checkpoint.metadata)
        
        return result
    
    async def delete_thread(self, thread_id: str) -> int:
        """Delete all checkpoints for a thread.
        
        Args:
            thread_id: Conversation thread ID
            
        Returns:
            Number of checkpoints deleted
        """
        client = await self._get_client()
        
        # Get all checkpoint IDs
        checkpoints_key = CheckpointKeys.thread_checkpoints_key(thread_id)
        checkpoint_ids = await client.zrange(checkpoints_key, 0, -1)
        
        # Delete each checkpoint
        deleted = 0
        for checkpoint_id in checkpoint_ids:
            checkpoint_key = CheckpointKeys.checkpoint_key(thread_id, checkpoint_id)
            deleted += await client.delete(checkpoint_key)
        
        # Delete the checkpoint list
        await client.delete(checkpoints_key)
        
        # Remove from thread index
        await client.srem(CheckpointKeys.THREAD_INDEX, thread_id)
        
        return deleted
    
    # ===== User Thread Management =====
    
    async def associate_thread_with_user(
        self,
        thread_id: str,
        user_id: str,
    ) -> None:
        """Associate a thread with a user for later retrieval.
        
        Args:
            thread_id: Conversation thread ID
            user_id: User ID
        """
        client = await self._get_client()
        
        user_threads_key = CheckpointKeys.user_threads_key(user_id)
        await client.sadd(user_threads_key, thread_id)
        await client.expire(user_threads_key, CheckpointKeys.THREAD_INDEX_TTL)
    
    async def get_user_threads(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[str]:
        """Get threads for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number to return
            
        Returns:
            List of thread IDs
        """
        client = await self._get_client()
        
        user_threads_key = CheckpointKeys.user_threads_key(user_id)
        threads = await client.smembers(user_threads_key)
        
        return list(threads)[:limit]
    
    # ===== LangGraph Integration =====
    
    async def aput(
        self,
        config: dict[str, Any],
        checkpoint: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """LangGraph-compatible put method.
        
        This matches LangGraph's BaseCheckpointSaver interface.
        """
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        checkpoint_id = metadata.get("checkpoint_id", f"step_{metadata.get('step', 0)}")
        
        saved = await self.put(
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            state=checkpoint,
            parent_id=metadata.get("parent_id"),
            step=metadata.get("step", 0),
            node=metadata.get("node"),
        )
        
        return {
            "checkpoint_id": saved.metadata.checkpoint_id,
            "thread_id": saved.metadata.thread_id,
        }
    
    async def aget(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any] | None:
        """LangGraph-compatible get method.
        
        This matches LangGraph's BaseCheckpointSaver interface.
        """
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        
        if checkpoint_id:
            checkpoint = await self.get(thread_id, checkpoint_id)
        else:
            checkpoint = await self.get_latest(thread_id)
        
        if checkpoint is None:
            return None
        
        return checkpoint.state
    
    async def alist(
        self,
        config: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        """LangGraph-compatible list method.
        
        This matches LangGraph's BaseCheckpointSaver interface.
        """
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        
        checkpoints = await self.list_checkpoints(thread_id)
        
        for metadata in checkpoints:
            checkpoint = await self.get(thread_id, metadata.checkpoint_id)
            if checkpoint:
                yield {
                    "checkpoint": checkpoint.state,
                    "metadata": checkpoint.metadata.to_dict(),
                }


# ============================================================
# Thread Manager
# ============================================================

class ThreadManager:
    """Manages conversation threads.
    
    Provides high-level operations for thread management,
    including creation, resumption, and cleanup.
    """
    
    def __init__(self, checkpointer: RedisCheckpointer | None = None):
        """Initialize with optional checkpointer."""
        self.checkpointer = checkpointer or RedisCheckpointer()
    
    async def create_thread(
        self,
        user_id: str | None = None,
    ) -> str:
        """Create a new conversation thread.
        
        Args:
            user_id: Optional user ID to associate
            
        Returns:
            New thread ID
        """
        import uuid
        thread_id = f"thread_{uuid.uuid4().hex[:12]}"
        
        if user_id:
            await self.checkpointer.associate_thread_with_user(thread_id, user_id)
        
        return thread_id
    
    async def resume_thread(
        self,
        thread_id: str,
    ) -> dict[str, Any] | None:
        """Resume a conversation from its latest checkpoint.
        
        Args:
            thread_id: Thread to resume
            
        Returns:
            Latest state or None if thread not found
        """
        checkpoint = await self.checkpointer.get_latest(thread_id)
        return checkpoint.state if checkpoint else None
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get a user's recent conversations.
        
        Args:
            user_id: User ID
            limit: Maximum number to return
            
        Returns:
            List of conversation summaries
        """
        thread_ids = await self.checkpointer.get_user_threads(user_id, limit)
        
        conversations = []
        for thread_id in thread_ids:
            checkpoint = await self.checkpointer.get_latest(thread_id)
            if checkpoint:
                # Extract summary from state
                messages = checkpoint.state.get("messages", [])
                conversations.append({
                    "thread_id": thread_id,
                    "message_count": len(messages),
                    "last_updated": checkpoint.metadata.created_at.isoformat(),
                    "last_message": messages[-1].get("content", "")[:100] if messages else "",
                })
        
        return conversations


# ============================================================
# Singleton Instances
# ============================================================

_checkpointer: RedisCheckpointer | None = None
_thread_manager: ThreadManager | None = None


def get_checkpointer() -> RedisCheckpointer:
    """Get the singleton checkpointer instance."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = RedisCheckpointer()
    return _checkpointer


def get_thread_manager() -> ThreadManager:
    """Get the singleton thread manager instance."""
    global _thread_manager
    if _thread_manager is None:
        _thread_manager = ThreadManager(get_checkpointer())
    return _thread_manager


def get_checkpointer(redis_url: Optional[str] = None):
    """Get a checkpointer, falling back to in-memory if Redis unavailable."""
    if redis_url and REDIS_AVAILABLE:
        try:
            import redis
            # Test connection first
            r = redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            return RedisSaver.from_conn_string(redis_url)
        except Exception as e:
            log.warning("Could not connect to Redis, running without checkpointer", error=str(e))
    
    # Fallback to in-memory (sessions won't persist across restarts)
    log.info("Using in-memory checkpointer (sessions won't persist)")
    return MemorySaver()
