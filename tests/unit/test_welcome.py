# demo-ui/tests/unit/test_welcome.py
"""Unit tests for welcome service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSendDashboardWelcome:
    """Tests for send_dashboard_welcome handler."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock Chainlit User."""
        user = MagicMock()
        user.identifier = "test-user-123"
        user.metadata = {
            "email": "test@example.com",
            "name": "İlham Əliyev",  # Azerbaijani name for testing
        }
        return user

    @pytest.mark.asyncio
    async def test_welcome_includes_user_first_name(self, mock_user):
        """Test that welcome message personalizes with user's first name."""
        with patch("chainlit.user_session") as mock_session:
            mock_session.set = MagicMock()

            with patch("chainlit.Message") as mock_msg:
                mock_instance = MagicMock()
                mock_instance.send = AsyncMock()
                mock_msg.return_value = mock_instance

                with patch("services.welcome.logger"):
                    from services.welcome import send_dashboard_welcome

                    await send_dashboard_welcome(user=mock_user)

                    # Check that Message was called with greeting
                    call_args = mock_msg.call_args
                    content = call_args.kwargs.get(
                        "content", call_args.args[0] if call_args.args else ""
                    )

                    # First name should be in greeting
                    assert "İlham" in content
                    assert "Salam" in content

    @pytest.mark.asyncio
    async def test_welcome_has_quick_actions(self, mock_user):
        """Test that welcome message includes quick action buttons."""
        with patch("chainlit.user_session") as mock_session:
            mock_session.set = MagicMock()

            with patch("chainlit.Message") as mock_msg:
                mock_instance = MagicMock()
                mock_instance.send = AsyncMock()
                mock_msg.return_value = mock_instance

                with patch("chainlit.Action") as mock_action:
                    mock_action.return_value = MagicMock()

                    with patch("services.welcome.logger"):
                        from services.welcome import send_dashboard_welcome

                        await send_dashboard_welcome(user=mock_user)

                        # Should have created 4 actions (weather, subsidy, irrigation, mcp_status)
                        assert mock_action.call_count >= 4

    @pytest.mark.asyncio
    async def test_welcome_anonymous_user(self):
        """Test that anonymous users get generic welcome."""
        with patch("chainlit.user_session") as mock_session:
            mock_session.set = MagicMock()

            with patch("chainlit.Message") as mock_msg:
                mock_instance = MagicMock()
                mock_instance.send = AsyncMock()
                mock_msg.return_value = mock_instance

                with patch("services.welcome.logger"):
                    from services.welcome import send_dashboard_welcome

                    await send_dashboard_welcome(user=None)

                    # Check generic greeting
                    call_args = mock_msg.call_args
                    content = call_args.kwargs.get(
                        "content", call_args.args[0] if call_args.args else ""
                    )

                    assert "Xoş gəlmisiniz" in content

    @pytest.mark.asyncio
    async def test_welcome_includes_alim_branding(self, mock_user):
        """Test that welcome includes ALİM branding."""
        with patch("chainlit.user_session") as mock_session:
            mock_session.set = MagicMock()

            with patch("chainlit.Message") as mock_msg:
                mock_instance = MagicMock()
                mock_instance.send = AsyncMock()
                mock_msg.return_value = mock_instance

                with patch("services.welcome.logger"):
                    from services.welcome import send_dashboard_welcome

                    await send_dashboard_welcome(user=mock_user)

                    call_args = mock_msg.call_args
                    content = call_args.kwargs.get(
                        "content", call_args.args[0] if call_args.args else ""
                    )

                    # Must use ALİM branding, not "ALİM" or "Sidecar"
                    assert "ALİM" in content
                    assert "Sidecar" not in content

    @pytest.mark.asyncio
    async def test_welcome_fallback_on_error(self):
        """Test that welcome falls back to simple message on error."""
        with patch("chainlit.user_session") as mock_session:
            mock_session.set = MagicMock(side_effect=Exception("Session error"))

            with patch("chainlit.Message") as mock_msg:
                mock_instance = MagicMock()
                mock_instance.send = AsyncMock()
                mock_msg.return_value = mock_instance

                with patch("services.welcome.logger"):
                    from services.welcome import send_dashboard_welcome

                    # Should not raise, should send fallback
                    await send_dashboard_welcome(user=None)

                    # Fallback message should be sent
                    assert mock_msg.call_count >= 1
