"""Test suite for command system.

Tests command parsing, registration, and execution.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path BEFORE importing from demo-ui
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "demo-ui"))

from services.commands import (  # noqa: E402
    Command,
    CommandRegistry,
    get_command_registry,
    handle_command,
    parse_command,
)


class TestCommandParsing:
    """Test command parsing functionality."""

    def test_parse_simple_command(self):
        """Test parsing simple command without parameters."""
        cmd, args = parse_command("/help")
        assert cmd == "help"
        assert args == []

    def test_parse_command_with_args(self):
        """Test parsing command with arguments."""
        cmd, args = parse_command("/farm demo_farm_001")
        assert cmd == "farm"
        assert args == ["demo_farm_001"]

    def test_parse_command_with_multiple_args(self):
        """Test parsing command with multiple arguments."""
        cmd, args = parse_command("/mode agent verbose")
        assert cmd == "mode"
        assert args == ["agent", "verbose"]

    def test_parse_non_command(self):
        """Test parsing regular message (not a command)."""
        cmd, args = parse_command("Hello, how are you?")
        assert cmd is None
        assert args == []

    def test_parse_empty_command(self):
        """Test parsing just a slash."""
        cmd, args = parse_command("/")
        assert cmd is None
        assert args == []

    def test_parse_command_case_insensitive(self):
        """Test that commands are case-insensitive."""
        cmd1, _ = parse_command("/HELP")
        cmd2, _ = parse_command("/Help")
        cmd3, _ = parse_command("/help")
        assert cmd1 == cmd2 == cmd3 == "help"


class TestCommandRegistry:
    """Test CommandRegistry functionality."""

    def test_builtin_commands_registered(self):
        """Test that built-in commands are registered."""
        registry = CommandRegistry()

        # Essential commands should exist
        assert registry.get("help") is not None
        assert registry.get("mcp") is not None
        assert registry.get("clear") is not None
        assert registry.get("settings") is not None
        assert registry.get("weather") is not None
        assert registry.get("farm") is not None

    def test_register_custom_command(self):
        """Test registering a custom command."""
        registry = CommandRegistry()

        async def custom_handler():
            pass

        custom_cmd = Command(
            name="test",
            description="Test command",
            handler=custom_handler,
        )

        registry.register(custom_cmd)
        assert registry.get("test") == custom_cmd

    def test_get_nonexistent_command(self):
        """Test getting command that doesn't exist."""
        registry = CommandRegistry()
        assert registry.get("nonexistent") is None

    def test_list_commands(self):
        """Test listing all commands."""
        registry = CommandRegistry()
        commands = registry.list_commands()

        # Should have multiple commands
        assert len(commands) > 5

        # All should be Command instances
        assert all(isinstance(cmd, Command) for cmd in commands)

    def test_help_text_generation(self):
        """Test help text generation."""
        registry = CommandRegistry()
        help_text = registry.get_help_text()

        # Should contain command names
        assert "/help" in help_text
        assert "/mcp" in help_text
        assert "/clear" in help_text

        # Should contain descriptions
        assert "Show available commands" in help_text
        assert "MCP server status" in help_text


class TestCommandExecution:
    """Test command execution."""

    @pytest.mark.asyncio
    @patch("chainlit.Message")
    async def test_execute_help_command(self, mock_message):
        """Test executing /help command."""
        registry = CommandRegistry()

        # Mock Message.send()
        mock_msg_instance = AsyncMock()
        mock_message.return_value = mock_msg_instance

        success = await registry.execute("help", [])

        assert success is True
        mock_msg_instance.send.assert_called_once()

    @pytest.mark.asyncio
    @patch("chainlit.Message")
    async def test_execute_nonexistent_command(self, mock_message):
        """Test executing command that doesn't exist."""
        registry = CommandRegistry()

        # Mock Message.send()
        mock_msg_instance = AsyncMock()
        mock_message.return_value = mock_msg_instance

        success = await registry.execute("nonexistent", [])

        assert success is False
        mock_msg_instance.send.assert_called_once()

    @pytest.mark.asyncio
    @patch("chainlit.Message")
    @patch("chainlit.user_session")
    async def test_execute_farm_command(self, mock_session, mock_message):
        """Test executing /farm command."""
        registry = CommandRegistry()

        # Mock session
        mock_session.get.return_value = "demo_farm_001"
        mock_session.set = MagicMock()

        # Mock Message.send()
        mock_msg_instance = AsyncMock()
        mock_message.return_value = mock_msg_instance

        success = await registry.execute("farm", ["demo_farm_002"])

        assert success is True
        mock_session.set.assert_called_with("farm_id", "demo_farm_002")
        mock_msg_instance.send.assert_called_once()

    @pytest.mark.asyncio
    @patch("chainlit.Message")
    async def test_execute_command_with_error(self, mock_message):
        """Test command execution with error."""
        registry = CommandRegistry()

        # Register command that raises error
        async def error_handler():
            raise ValueError("Test error")

        error_cmd = Command(
            name="error_test",
            description="Error test",
            handler=error_handler,
        )
        registry.register(error_cmd)

        # Mock Message.send()
        mock_msg_instance = AsyncMock()
        mock_message.return_value = mock_msg_instance

        success = await registry.execute("error_test", [])

        assert success is False
        mock_msg_instance.send.assert_called_once()

        # Error message should be sent
        call_args = mock_message.call_args
        assert "Error executing command" in call_args[1]["content"]


class TestCommandHandler:
    """Test handle_command function."""

    @pytest.fixture
    async def mock_chainlit_context(self):
        """Mock Chainlit context for testing"""
        with patch("chainlit.context.get_context") as mock_ctx:
            mock_session = MagicMock()
            mock_session.thread_id = "test_thread"
            mock_ctx.return_value.session = mock_session
            yield mock_ctx

    @pytest.mark.asyncio
    async def test_handle_command_success(self, mock_chainlit_context):
        """Test successful command execution"""
        registry = CommandRegistry()

        with patch("chainlit.Message") as mock_message:
            mock_msg_instance = AsyncMock()
            mock_message.return_value = mock_msg_instance
            mock_msg_instance.send = AsyncMock()

            await handle_command("/help", registry)

            # Verify message was sent
            mock_msg_instance.send.assert_called_once()

    # ...existing code...


class TestSingletonPattern:
    """Test singleton pattern for command registry."""

    def test_get_command_registry_singleton(self):
        """Test that get_command_registry returns singleton."""
        registry1 = get_command_registry()
        registry2 = get_command_registry()

        assert registry1 is registry2


class TestCommandParameters:
    """Test command parameter handling."""

    def test_command_with_parameters(self):
        """Test command with parameter definition."""

        async def handler(param1, param2):
            pass

        cmd = Command(
            name="test",
            description="Test",
            handler=handler,
            parameters=["param1", "param2"],
        )

        assert cmd.parameters == ["param1", "param2"]

    def test_command_without_parameters(self):
        """Test command without parameters."""

        async def handler():
            pass

        cmd = Command(
            name="test",
            description="Test",
            handler=handler,
        )

        assert cmd.parameters is None


class TestCommandModes:
    """Test command mode restrictions."""

    def test_command_enabled_in_specific_modes(self):
        """Test command with mode restrictions."""

        async def handler():
            pass

        cmd = Command(
            name="test",
            description="Test",
            handler=handler,
            enabled_modes=["agent", "plan"],
        )

        assert cmd.enabled_modes == ["agent", "plan"]

    def test_command_enabled_in_all_modes(self):
        """Test command without mode restrictions."""

        async def handler():
            pass

        cmd = Command(
            name="test",
            description="Test",
            handler=handler,
        )

        assert cmd.enabled_modes is None


class TestCommandAuthentication:
    """Test command authentication requirements."""

    def test_command_requires_auth(self):
        """Test command that requires authentication."""

        async def handler():
            pass

        cmd = Command(
            name="debug",
            description="Debug info",
            handler=handler,
            requires_auth=True,
        )

        assert cmd.requires_auth is True

    def test_command_no_auth_required(self):
        """Test command that doesn't require authentication."""

        async def handler():
            pass

        cmd = Command(
            name="help",
            description="Help",
            handler=handler,
        )

        assert cmd.requires_auth is False

    @pytest.mark.asyncio
    @patch("chainlit.Message")
    @patch("chainlit.user_session")
    async def test_execute_auth_command_without_user(self, mock_session, mock_message):
        """Test executing auth-required command without user."""
        registry = CommandRegistry()

        # Mock no user
        mock_session.get.return_value = None

        # Mock Message.send()
        mock_msg_instance = AsyncMock()
        mock_message.return_value = mock_msg_instance

        success = await registry.execute("debug", [])

        assert success is False
        mock_msg_instance.send.assert_called_once()

        # Should show auth required message
        call_args = mock_message.call_args
        assert "requires authentication" in call_args[1]["content"]
