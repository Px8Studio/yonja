# tests/unit/test_mcp_resilience.py
"""Unit tests for MCPResilienceManager service.

Tests cover:
- Health checks (success/failure)
- Exponential backoff retry logic
- Graceful degradation (continue without tools)
- Status reporting
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from services.mcp_resilience import MCPResilienceManager

# ============================================================
# Tests: MCPResilienceManager
# ============================================================


class TestMCPResilienceManager:
    """Tests for MCPResilienceManager class."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        manager = MCPResilienceManager(mcp_url="http://test-mcp:7777")

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            is_healthy = await manager.health_check()
            assert is_healthy is True
            assert manager.last_error is None

    @pytest.mark.asyncio
    async def test_health_check_failure_500(self):
        """Test health check failure (500 error)."""
        manager = MCPResilienceManager(mcp_url="http://test-mcp:7777")

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            is_healthy = await manager.health_check()
            assert is_healthy is False
            assert "500" in manager.last_error

    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check timeout."""

        manager = MCPResilienceManager(mcp_url="http://test-mcp:7777")

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.side_effect = TimeoutError()

        with patch("httpx.AsyncClient", return_value=mock_client):
            is_healthy = await manager.health_check()
            assert is_healthy is False
            assert "Timeout" in manager.last_error

    @pytest.mark.asyncio
    async def test_initialize_with_retry_success_first_try(self):
        """Test initialization success on first attempt."""
        manager = MCPResilienceManager(max_retries=3)

        # Mock health_check to return True immediately
        with patch.object(manager, "health_check", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True

            result = await manager.initialize_with_retry()

            assert result is True
            assert manager.is_available is True
            assert mock_health.call_count == 1
            assert manager.retry_count == 1

    @pytest.mark.asyncio
    async def test_initialize_with_retry_success_after_failure(self):
        """Test initialization success after 2 failures (3rd try)."""
        manager = MCPResilienceManager(max_retries=3, initial_delay=0.1)

        # Mock health_check: False, False, True
        with patch.object(manager, "health_check", new_callable=AsyncMock) as mock_health:
            mock_health.side_effect = [False, False, True]

            # Using real sleep would slow tests, but 0.1s is fast enough
            # Or we can patch sleep
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                result = await manager.initialize_with_retry()

                assert result is True
                assert manager.is_available is True
                assert mock_health.call_count == 3
                assert mock_sleep.call_count == 2
                assert manager.retry_count == 3

    @pytest.mark.asyncio
    async def test_initialize_with_retry_failure_exhausted(self):
        """Test initialization failure after exhausting retries."""
        manager = MCPResilienceManager(max_retries=3, initial_delay=0.1)

        # Mock health_check to always fail
        with patch.object(manager, "health_check", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await manager.initialize_with_retry()

                assert result is False
                assert manager.is_available is False
                assert mock_health.call_count == 3
                assert manager.retry_count == 3

    @pytest.mark.asyncio
    async def test_ensure_available_degraded(self):
        """Test ensure_available with allowed degradation."""
        manager = MCPResilienceManager()
        manager.is_available = False

        # Mock initialize to fail
        with patch.object(manager, "initialize_with_retry", new_callable=AsyncMock) as mock_init:
            mock_init.return_value = False

            # Should return True because allow_degraded=True
            result = await manager.ensure_available(allow_degraded=True)

            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_available_strict(self):
        """Test ensure_available strict mode (no degradation)."""
        manager = MCPResilienceManager()
        manager.is_available = False

        # Mock initialize to fail
        with patch.object(manager, "initialize_with_retry", new_callable=AsyncMock) as mock_init:
            mock_init.return_value = False

            # Should return False because allow_degraded=False
            result = await manager.ensure_available(allow_degraded=False)

            assert result is False

    def test_get_status(self):
        """Test get_status method."""
        manager = MCPResilienceManager(mcp_url="http://test:7777")
        manager.is_available = True
        manager.retry_count = 2
        manager.last_error = "Previous error"

        status = manager.get_status()

        assert status["available"] is True
        assert status["url"] == "http://test:7777"
        assert status["retry_attempts"] == 2
        assert status["last_error"] == "Previous error"
