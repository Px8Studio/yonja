# demo-ui/storage_postgres.py
"""PostgreSQL-based file storage for Chainlit elements.

This module implements a custom storage client that stores all file uploads
(audio, video, images, documents, etc.) directly in PostgreSQL using BYTEA columns.

Benefits:
- Full data residency: All data stays in your PostgreSQL database
- No external dependencies: No S3, Azure, GCS accounts needed
- Single backup: Database backup includes all files
- ACID compliance: File operations are transactional
- Simplified infrastructure: One less service to manage

Tradeoffs:
- Database size: Large files increase DB size (use pg_dump with compression)
- Memory usage: Large files loaded into memory during read/write
- Not ideal for: Very large files (>100MB) or high-throughput streaming

For most chat applications with document/image attachments, this is ideal.
"""

import base64
import hashlib
import uuid
from datetime import datetime
from typing import Any

import structlog
from chainlit.data.storage_clients.base import BaseStorageClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = structlog.get_logger(__name__)

# Default expiry time for signed URLs (not really needed for Postgres, but kept for interface)
STORAGE_EXPIRY_SECONDS = 3600


class PostgresStorageClient(BaseStorageClient):
    """PostgreSQL-based storage client for Chainlit file elements.

    Stores files as BYTEA in a dedicated table, with metadata for retrieval.
    Files are served via a base64 data URL or through an API endpoint.

    Table schema (created by migration):
        files (
            id UUID PRIMARY KEY,
            object_key VARCHAR(500) UNIQUE,  -- Path-like key (e.g., "threads/123/files/456")
            data BYTEA,                       -- File content
            mime_type VARCHAR(100),           -- MIME type (e.g., "image/png")
            size_bytes BIGINT,                -- File size for quick lookup
            checksum VARCHAR(64),             -- SHA-256 for integrity
            created_at TIMESTAMP,
            expires_at TIMESTAMP,             -- Optional TTL for temp files
            metadata JSONB                    -- Additional metadata
        )
    """

    def __init__(
        self,
        database_url: str,
        table_name: str = "chainlit_files",
        base_url: str | None = None,
    ):
        """Initialize PostgreSQL storage client.

        Args:
            database_url: PostgreSQL connection string (async format)
            table_name: Name of the files table
            base_url: Optional base URL for file retrieval API
                      If None, files are returned as base64 data URLs
        """
        self.database_url = database_url
        self.table_name = table_name
        self.base_url = base_url

        # Create async engine and session factory
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(
            "postgres_storage_initialized",
            table=table_name,
            has_base_url=bool(base_url),
        )

    async def upload_file(
        self,
        object_key: str,
        data: bytes | str,
        mime: str = "application/octet-stream",
        overwrite: bool = True,
        content_disposition: str | None = None,
    ) -> dict[str, Any]:
        """Upload a file to PostgreSQL.

        Args:
            object_key: Unique path-like identifier (e.g., "threads/123/files/456")
            data: File content (bytes or string)
            mime: MIME type
            overwrite: If True, replace existing file with same key
            content_disposition: Optional disposition header (stored in metadata)

        Returns:
            Dict with 'object_key' and 'url'
        """
        # Convert string to bytes if needed
        if isinstance(data, str):
            data = data.encode("utf-8")

        # Calculate checksum and size
        checksum = hashlib.sha256(data).hexdigest()
        size_bytes = len(data)
        file_id = str(uuid.uuid4())

        async with self.async_session() as session:
            try:
                if overwrite:
                    # Upsert: insert or update if exists
                    query = text(
                        f"""
                        INSERT INTO {self.table_name}
                            (id, object_key, data, mime_type, size_bytes, checksum, created_at, metadata)
                        VALUES
                            (:id, :object_key, :data, :mime_type, :size_bytes, :checksum, :created_at, :metadata)
                        ON CONFLICT (object_key) DO UPDATE SET
                            data = EXCLUDED.data,
                            mime_type = EXCLUDED.mime_type,
                            size_bytes = EXCLUDED.size_bytes,
                            checksum = EXCLUDED.checksum,
                            metadata = EXCLUDED.metadata
                        RETURNING id
                    """
                    )
                else:
                    # Insert only, fail if exists
                    query = text(
                        f"""
                        INSERT INTO {self.table_name}
                            (id, object_key, data, mime_type, size_bytes, checksum, created_at, metadata)
                        VALUES
                            (:id, :object_key, :data, :mime_type, :size_bytes, :checksum, :created_at, :metadata)
                        RETURNING id
                    """
                    )

                metadata = {}
                if content_disposition:
                    metadata["content_disposition"] = content_disposition

                await session.execute(
                    query,
                    {
                        "id": file_id,
                        "object_key": object_key,
                        "data": data,
                        "mime_type": mime,
                        "size_bytes": size_bytes,
                        "checksum": checksum,
                        "created_at": datetime.utcnow(),
                        "metadata": metadata if metadata else None,
                    },
                )
                await session.commit()

                logger.debug(
                    "file_uploaded",
                    object_key=object_key,
                    size_bytes=size_bytes,
                    mime=mime,
                )

                # Generate URL
                url = self._build_data_url(object_key, data, mime)

                return {
                    "object_key": object_key,
                    "url": url,
                }

            except Exception as e:
                await session.rollback()
                logger.error("file_upload_failed", object_key=object_key, error=str(e))
                raise

    async def get_read_url(self, object_key: str) -> str:
        """Get a URL to read the file.

        If base_url is configured, returns an API URL.
        Otherwise, returns a base64 data URL (loads file into memory).

        Args:
            object_key: The file's unique key

        Returns:
            URL string (either API URL or data URL)
        """
        if self.base_url:
            # Return API endpoint URL
            return f"{self.base_url}/files/{object_key}"

        # Return base64 data URL (for small files / dev mode)
        return await self._get_data_url(object_key)

    async def _get_data_url(self, object_key: str) -> str:
        """Load file and return as base64 data URL.

        Note: This loads the entire file into memory. For large files,
        use base_url with a streaming API endpoint instead.
        """
        async with self.async_session() as session:
            query = text(
                f"""
                SELECT data, mime_type FROM {self.table_name}
                WHERE object_key = :object_key
            """
            )
            result = await session.execute(query, {"object_key": object_key})
            row = result.fetchone()

            if not row:
                logger.warning("file_not_found", object_key=object_key)
                return ""

            data, mime_type = row
            base64_data = base64.b64encode(data).decode("utf-8")
            return f"data:{mime_type};base64,{base64_data}"

    async def get_file(
        self, object_key: str, expires_in: int | None = None
    ) -> tuple[str, dict[str, str]] | None:
        """Get file content and metadata.

        Args:
            object_key: The file's unique key
            expires_in: Optional expiry time in seconds

        Returns:
            Tuple of (file_id, metadata) or None
        """
        async with self.async_session() as session:
            query = text(
                f"""
                SELECT id, data, mime_type, size_bytes, checksum, created_at, metadata
                FROM {self.table_name}
                WHERE object_key = :object_key
            """
            )
            result = await session.execute(query, {"object_key": object_key})
            row = result.fetchone()

            if not row:
                return None

            return (
                str(row[0]),
                {
                    "data": row[1],
                    "mime_type": row[2],
                    "size_bytes": row[3],
                    "checksum": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "metadata": row[6] if row[6] else {},
                },
            )

    async def delete_file(self, object_key: str) -> bool:
        """Delete a file from PostgreSQL.

        Args:
            object_key: The file's unique key

        Returns:
            True if deleted, False if not found
        """
        async with self.async_session() as session:
            try:
                query = text(
                    f"""
                    DELETE FROM {self.table_name}
                    WHERE object_key = :object_key
                    RETURNING id
                """
                )
                result = await session.execute(query, {"object_key": object_key})
                await session.commit()

                deleted = result.fetchone() is not None

                if deleted:
                    logger.debug("file_deleted", object_key=object_key)
                else:
                    logger.debug("file_not_found_for_delete", object_key=object_key)

                return deleted

            except Exception as e:
                await session.rollback()
                logger.error("file_delete_failed", object_key=object_key, error=str(e))
                return False

    async def cleanup_expired(self) -> int:
        """Delete files that have passed their expiry time.

        Returns:
            Number of files deleted
        """
        async with self.async_session() as session:
            try:
                query = text(
                    f"""
                    DELETE FROM {self.table_name}
                    WHERE expires_at IS NOT NULL AND expires_at < :now
                    RETURNING id
                """
                )
                result = await session.execute(query, {"now": datetime.utcnow()})
                await session.commit()

                deleted_count = len(result.fetchall())
                if deleted_count > 0:
                    logger.info("expired_files_cleaned", count=deleted_count)

                return deleted_count

            except Exception as e:
                await session.rollback()
                logger.error("cleanup_expired_failed", error=str(e))
                return 0

    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()
        logger.debug("postgres_storage_closed")

    def _generate_url(self, object_key: str) -> str:
        """Generate URL for file access."""
        if self.base_url:
            return f"{self.base_url}/files/{object_key}"
        # For data URLs, we'll generate on read
        return f"postgres://{object_key}"

    def _build_data_url(
        self,
        object_key: str,
        data: bytes,
        mime_type: str,
        base_url: str | None = None,
    ) -> str:
        """Generate a data URL or API URL for the file."""
        if base_url:
            return f"{base_url}/files/{object_key}"
        # For data URLs, we'll generate on read
        return f"postgres://{object_key}"


def get_postgres_storage_client(
    database_url: str,
    base_url: str | None = None,
) -> PostgresStorageClient:
    """Factory function to create PostgreSQL storage client.

    Args:
        database_url: PostgreSQL connection string
        base_url: Optional API base URL for file serving

    Returns:
        Configured PostgresStorageClient instance
    """
    return PostgresStorageClient(
        database_url=database_url,
        base_url=base_url,
    )
