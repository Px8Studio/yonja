# demo-ui/tests/unit/test_lifecycle.py
"""Unit tests for lifecycle service handlers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestHandleChatStart:
    """Tests for handle_chat_start handler."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock Chainlit User."""
        user = MagicMock()
        user.identifier = "test-user-123"
        user.metadata = {
            "email": "test@example.com",
            "name": "Test Farmer",
        }
        return user

    @pytest.fixture
    def mock_session(self):
        """Create a mock user session."""
        session_data = {}

        def get_item(key, default=None):
            return session_data.get(key, default)

        def set_item(key, value):
            session_data[key] = value

        session = MagicMock()
        session.get = get_item
        session.set = set_item
        session._data = session_data
        return session

    @pytest.mark.asyncio
    async def test_anonymous_user_skips_persona(self, mock_session):
        """Test that anonymous users skip persona provisioning."""
        with patch("chainlit.user_session", mock_session):
            with patch("services.lifecycle.logger") as mock_logger:
                # Import after patching
                from services.lifecycle import handle_chat_start

                # Mock all the callback functions
                mock_get_data_layer = MagicMock(return_value=None)
                mock_setup_settings = AsyncMock(return_value={})
                mock_send_welcome = AsyncMock()

                # Call with no user
                await handle_chat_start(
                    user=None,
                    session_id="test-session-001",
                    get_data_layer_fn=mock_get_data_layer,
                    setup_chat_settings_fn=mock_setup_settings,
                    send_dashboard_welcome_fn=mock_send_welcome,
                )

                # Verify welcome was sent
                mock_send_welcome.assert_called_once()

                # Verify log for no user
                mock_logger.debug.assert_any_call("no_authenticated_user_skipping_persona")


class TestHandleChatResume:
    """Tests for handle_chat_resume handler."""

    @pytest.fixture
    def mock_thread(self):
        """Create a mock ThreadDict."""
        return {
            "id": "thread-123",
            "name": "Test Thread",
            "userId": "user-456",
            "metadata": {
                "farm_id": "demo_farm_001",
                "expertise_areas": ["general", "cotton"],
            },
            "tags": ["cotton", "Aran"],
            "createdAt": "2026-01-24T10:00:00Z",
        }

    @pytest.mark.asyncio
    async def test_resume_restores_thread_id(self, mock_thread):
        """Test that resume correctly restores thread_id in session."""
        session_data = {}

        with patch("chainlit.user_session") as mock_session:
            mock_session.get = lambda k, d=None: session_data.get(k, d)
            mock_session.set = lambda k, v: session_data.update({k: v})

            with patch(
                "services.lifecycle.load_alim_persona_from_db", new_callable=AsyncMock
            ) as mock_load:
                mock_load.return_value = None  # No persona found

                with patch("services.lifecycle.logger"):
                    with patch("chainlit.Message") as mock_msg:
                        mock_msg.return_value.send = AsyncMock()

                        from services.lifecycle import handle_chat_resume

                        mock_checkpointer = AsyncMock(return_value=None)
                        mock_compile = MagicMock(return_value=None)
                        mock_setup = AsyncMock(return_value={})

                        await handle_chat_resume(
                            thread=mock_thread,
                            get_app_checkpointer_fn=mock_checkpointer,
                            compile_agent_graph_fn=mock_compile,
                            setup_chat_settings_fn=mock_setup,
                        )

                        # Verify thread_id was set in session
                        assert session_data.get("thread_id") == "thread-123"


class TestHandleSharedThreadView:
    """Tests for handle_shared_thread_view handler."""

    @pytest.mark.asyncio
    async def test_allows_all_viewers(self):
        """Test that shared thread view allows all viewers (placeholder policy)."""
        from services.lifecycle import handle_shared_thread_view

        thread = {
            "id": "thread-123",
            "userId": "owner-456",
            "metadata": {"is_shared": True},
        }
        viewer = MagicMock()
        viewer.identifier = "viewer-789"

        with patch("services.lifecycle.logger"):
            result = await handle_shared_thread_view(thread, viewer)

        assert result is True

    @pytest.mark.asyncio
    async def test_allows_anonymous_viewer(self):
        """Test that anonymous viewers can access shared threads."""
        from services.lifecycle import handle_shared_thread_view

        thread = {
            "id": "thread-123",
            "userId": "owner-456",
            "metadata": {},
        }

        with patch("services.lifecycle.logger"):
            result = await handle_shared_thread_view(thread, None)

        assert result is True
