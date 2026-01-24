# tests/unit/test_session_manager.py
"""Unit tests for SessionManager service.

Tests cover:
- Loading user preferences from DB
- Saving user preferences to DB
- Restoring session state to cl.user_session
- Handling missing data layer (graceful failure)
- Session hydration logic
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from services.session_manager import SessionManager

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_chainlit_session():
    """Mock chainlit.user_session."""
    session_data = {}

    def get(key, default=None):
        return session_data.get(key, default)

    def set(key, value):
        session_data[key] = value

    mock_session = MagicMock()
    mock_session.get.side_effect = get
    mock_session.set.side_effect = set

    with patch("chainlit.user_session", mock_session):
        yield mock_session


@pytest.fixture
def mock_data_layer():
    """Mock Chainlit data layer."""
    mock_layer = AsyncMock()

    # Mock user object with metadata
    mock_user = MagicMock()
    mock_user.identifier = "test_user_id"
    mock_user.metadata = {
        "alim_preferences": {
            "farm_id": "farm_123",
            "chat_profile": "Ask",
            "expertise_areas": ["irrigation"],
        }
    }

    mock_layer.get_user.return_value = mock_user
    mock_layer.update_user.return_value = True

    return mock_layer


# ============================================================
# Tests: SessionManager
# ============================================================


class TestSessionManager:
    """Tests for SessionManager class."""

    @pytest.mark.asyncio
    async def test_load_preferences_success(self, mock_data_layer):
        """Test successful loading of user preferences."""
        with patch("data_layer.get_data_layer", return_value=mock_data_layer):
            prefs = await SessionManager.load_user_preferences("test_user_id")

            assert prefs["farm_id"] == "farm_123"
            assert prefs["chat_profile"] == "Ask"
            mock_data_layer.get_user.assert_called_once_with("test_user_id")

    @pytest.mark.asyncio
    async def test_load_preferences_no_user(self, mock_data_layer):
        """Test loading when user not found."""
        mock_data_layer.get_user.return_value = None

        with patch("data_layer.get_data_layer", return_value=mock_data_layer):
            prefs = await SessionManager.load_user_preferences("unknown_user")

            assert prefs == {}
            mock_data_layer.get_user.assert_called_once_with("unknown_user")

    @pytest.mark.asyncio
    async def test_load_preferences_no_datalayer(self):
        """Test loading when data layer is unavailable."""
        with patch("data_layer.get_data_layer", return_value=None):
            prefs = await SessionManager.load_user_preferences("test_user")
            assert prefs == {}

    @pytest.mark.asyncio
    async def test_save_preferences_success(self, mock_data_layer):
        """Test successful saving of user preferences."""
        new_prefs = {"farm_id": "farm_999"}

        with patch("data_layer.get_data_layer", return_value=mock_data_layer):
            result = await SessionManager.save_user_preferences("test_user_id", new_prefs)

            assert result is True
            mock_data_layer.update_user.assert_called_once()

            # Verify metadata update
            _, kwargs = mock_data_layer.update_user.call_args
            assert kwargs["user_id"] == "test_user_id"
            metadata = json.loads(kwargs["metadata"])
            assert metadata["alim_preferences"] == new_prefs

    @pytest.mark.asyncio
    async def test_restore_session(self, mock_data_layer, mock_chainlit_session):
        """Test restoring session state from DB to cl.user_session."""
        with patch("data_layer.get_data_layer", return_value=mock_data_layer):
            await SessionManager.restore_session("test_user_id")

            # Check directly on the mocked get method calls or check side effects if accessible
            # Since we mocked get/set, we can check calls
            calls = mock_chainlit_session.set.call_args_list

            # Verify calls were made for expected keys
            keys_set = [call[0][0] for call in calls]
            assert "farm_id" in keys_set
            # Restore logic maps alim_preferences to session keys
            # Verify basic restore logic
            assert "chat_profile" in keys_set
            assert "expertise_areas" in keys_set

    @pytest.mark.asyncio
    async def test_save_farm_selection(self, mock_data_layer):
        """Test verify helper: save_farm_selection."""
        with patch("data_layer.get_data_layer", return_value=mock_data_layer):
            success = await SessionManager.save_farm_selection("test_user_id", "new_farm")

            assert success is True
            mock_data_layer.update_user.assert_called_once()

            # Check specific update logic
            _, kwargs = mock_data_layer.update_user.call_args
            metadata = json.loads(kwargs["metadata"])
            assert metadata["alim_preferences"]["farm_id"] == "new_farm"

    @pytest.mark.asyncio
    async def test_save_custom_preferences(self, mock_data_layer):
        """Test verify helper: save_custom_preferences."""
        with patch("data_layer.get_data_layer", return_value=mock_data_layer):
            success = await SessionManager.save_custom_preferences(
                "test_user_id", language="English", detail_level="High"
            )

            assert success is True

            _, kwargs = mock_data_layer.update_user.call_args
            metadata = json.loads(kwargs["metadata"])
            prefs = metadata["alim_preferences"]
            assert prefs["language"] == "English"
            assert prefs["detail_level"] == "High"
            # Ensure existing prefs preserved
            assert prefs["farm_id"] == "farm_123"
