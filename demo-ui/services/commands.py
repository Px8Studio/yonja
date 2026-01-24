# demo-ui/services/commands.py
"""Command system for Chainlit chat interface.

Provides Discord-style slash commands for quick actions:
- /help - Show available commands
- /mcp - Show MCP server status
- /clear - Clear conversation history
- /settings - Open settings panel
- /weather - Get weather forecast
- /irrigation - Get irrigation recommendations
- /subsidy - Check subsidy eligibility
- /calendar - Show agricultural calendar
- /farm <id> - Switch farm context
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass

import chainlit as cl

logger = logging.getLogger(__name__)


@dataclass
class Command:
    """Command definition."""

    name: str  # Command name (without /)
    description: str  # User-friendly description
    handler: Callable  # Async function to execute
    parameters: list | None = None  # Optional parameters
    enabled_modes: list | None = None  # Modes where command is available
    requires_auth: bool = False  # Requires authenticated user


class CommandRegistry:
    """Registry of available slash commands."""

    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self):
        """Register all built-in commands."""
        # Help command
        self.register(
            Command(
                name="help",
                description="🆘 Show available commands",
                handler=self._handle_help,
            )
        )

        # MCP status
        self.register(
            Command(
                name="mcp",
                description="🔌 Show MCP server status",
                handler=self._handle_mcp_status,
            )
        )

        # MCP status alias
        self.register(
            Command(
                name="status",
                description="📊 Show system status",
                handler=self._handle_mcp_status,
            )
        )

        # Clear conversation
        self.register(
            Command(
                name="clear",
                description="🗑️ Clear conversation history",
                handler=self._handle_clear,
            )
        )

        # Settings
        self.register(
            Command(
                name="settings",
                description="⚙️ Open settings panel",
                handler=self._handle_settings,
            )
        )

        # Weather
        self.register(
            Command(
                name="weather",
                description="🌤️ Get weather forecast",
                handler=self._handle_weather,
            )
        )

        # Irrigation
        self.register(
            Command(
                name="irrigation",
                description="💧 Get irrigation recommendations",
                handler=self._handle_irrigation,
            )
        )

        # Subsidy
        self.register(
            Command(
                name="subsidy",
                description="📋 Check subsidy eligibility",
                handler=self._handle_subsidy,
            )
        )

        # Calendar
        self.register(
            Command(
                name="calendar",
                description="📅 Show agricultural calendar",
                handler=self._handle_calendar,
            )
        )

        # Image generation
        self.register(
            Command(
                name="image",
                description="🖼️ Generate image from description",
                handler=self._handle_image,
                parameters=["description"],
            )
        )

        # Image with quality
        self.register(
            Command(
                name="img",
                description="🎨 Generate image (quick alias)",
                handler=self._handle_image,
                parameters=["description"],
            )
        )

        # Farm switch
        self.register(
            Command(
                name="farm",
                description="🌾 Switch farm context",
                handler=self._handle_farm,
                parameters=["farm_id"],
            )
        )

        # Mode switch
        self.register(
            Command(
                name="mode",
                description="🤖 Switch interaction mode (Ask/Plan/Agent)",
                handler=self._handle_mode,
                parameters=["mode_name"],
            )
        )

        # Debug info
        self.register(
            Command(
                name="debug",
                description="🐛 Show debug information",
                handler=self._handle_debug,
                requires_auth=True,
            )
        )

    def register(self, command: Command):
        """Register a command."""
        self._commands[command.name] = command
        logger.debug(f"command_registered: {command.name}")

    def get(self, name: str) -> Command | None:
        """Get command by name."""
        return self._commands.get(name)

    def list_commands(self) -> list[Command]:
        """List all commands."""
        return list(self._commands.values())

    def get_help_text(self) -> str:
        """Generate help text for all commands."""
        commands = self.list_commands()
        lines = ["**📋 Available Commands:**\n"]

        for cmd in sorted(commands, key=lambda c: c.name):
            params = f" `<{', '.join(cmd.parameters)}>`" if cmd.parameters else ""
            auth_marker = " 🔒" if cmd.requires_auth else ""
            lines.append(f"**/{cmd.name}**{params} - {cmd.description}{auth_marker}")

        return "\n".join(lines)

    async def execute(self, command_name: str, args: list[str]) -> bool:
        """Execute a command by name.

        Args:
            command_name: Command name (without /)
            args: Command arguments

        Returns:
            True if command executed successfully
        """
        cmd = self.get(command_name)
        if not cmd:
            logger.warning(f"command_not_found: {command_name}")
            await cl.Message(
                content=f"❌ Command not found: `/{command_name}`\nType `/help` for available commands.",
                author="System",
            ).send()
            return False

        # Check authentication if required
        if cmd.requires_auth:
            user = cl.user_session.get("user")
            if not user:
                await cl.Message(
                    content=f"🔒 Command `/{command_name}` requires authentication.",
                    author="System",
                ).send()
                return False

        # Execute command handler
        try:
            await cmd.handler(*args)
            logger.info(f"command_executed: {command_name}, args={args}")
            return True
        except Exception as e:
            logger.error(f"command_execution_failed: {command_name}, error={str(e)}", exc_info=True)
            await cl.Message(
                content=f"❌ Error executing command `/{command_name}`: {str(e)}",
                author="System",
            ).send()
            return False

    # ============================================
    # COMMAND HANDLERS
    # ============================================

    async def _handle_help(self):
        """Show help message with all commands."""
        help_text = self.get_help_text()
        await cl.Message(content=help_text, author="ALEM").send()

    async def _handle_mcp_status(self):
        """Show MCP server status."""
        try:
            from yonca.config import AgentMode

            from services.mcp_connector import format_mcp_status, get_mcp_status

            chat_profile = cl.user_session.get("chat_profile", AgentMode.FAST.value)
            mcp_status = await get_mcp_status(profile=chat_profile)
            formatted = format_mcp_status(mcp_status)

            await cl.Message(
                content=formatted,
                author="System",
            ).send()

        except Exception as e:
            logger.error("mcp_status_command_failed", error=str(e))
            await cl.Message(
                content=f"❌ MCP status error: {str(e)}",
                author="System",
            ).send()

    async def _handle_clear(self):
        """Clear conversation history (start new thread)."""
        await cl.Message(
            content="🗑️ **Conversation cleared.**\n\nStarting fresh! How can I help you?",
            author="System",
        ).send()

        # Reset thread metadata
        thread_id = cl.user_session.get("thread_id")
        if thread_id:
            logger.info("conversation_cleared", thread_id=thread_id)

    async def _handle_settings(self):
        """Open settings panel."""
        await cl.Message(
            content="⚙️ **Settings**\n\nClick the settings icon ⚙️ in the sidebar to adjust preferences.",
            author="System",
        ).send()

    async def _handle_weather(self):
        """Get weather forecast."""
        await cl.Message(
            content="🌤️ **Weather Forecast**\n\nFetching weather data... (Integration pending)",
            author="ALEM",
        ).send()

    async def _handle_irrigation(self):
        """Get irrigation recommendations."""
        await cl.Message(
            content="💧 **Irrigation Recommendations**\n\nAnalyzing soil moisture and weather... (Integration pending)",
            author="ALEM",
        ).send()

    async def _handle_subsidy(self):
        """Check subsidy eligibility."""
        await cl.Message(
            content="📋 **Subsidy Information**\n\nChecking available subsidies for your farm... (Integration pending)",
            author="ALEM",
        ).send()

    async def _handle_calendar(self):
        """Show agricultural calendar."""
        await cl.Message(
            content="📅 **Agricultural Calendar**\n\nLoading seasonal recommendations... (Integration pending)",
            author="ALEM",
        ).send()

    async def _handle_image(self, description: str | None = None):
        """Generate image from description."""
        if not description:
            await cl.Message(
                content="🖼️ **Image Generation**\n\nUsage: `/image <description>` or `/img <description>`\n\n**Supported providers:**\n- 🏠 Local (Ollama)\n- ☁️ Groq\n- 🤗 Hugging Face\n- 🎨 OpenAI (fallback)\n\nExample: `/image A serene farm landscape at sunrise`",
                author="System",
            ).send()
            return

        # Send processing message
        processing_msg = await cl.Message(
            content=f"🎨 **Generating image**\n\n`{description}`\n\nProvider: Intelligent auto-selection (Ollama → Groq → HF → OpenAI)",
            author="ALEM",
        ).send()

        try:
            from services.image_processor import ImageProvider, ImageQuality, get_image_processor

            processor = get_image_processor()

            # Try primary provider first
            provider_order = [
                (ImageProvider.OLLAMA_LOCAL, "🏠 Local (Ollama)"),
                (ImageProvider.GROQ, "⚡ Groq"),
                (ImageProvider.HUGGINGFACE, "🤗 Hugging Face"),
                (ImageProvider.OPENAI, "🎨 OpenAI"),
            ]

            image_data = None
            used_provider = None

            for provider, provider_label in provider_order:
                try:
                    # Update status
                    await processing_msg.remove()
                    processing_msg = await cl.Message(
                        content=f"🎨 **Generating image** via {provider_label}\n\n`{description}`",
                        author="ALEM",
                    ).send()

                    # Generate image
                    image_data = await processor.generate_image(
                        description,
                        provider=provider,
                        quality=ImageQuality.STANDARD,
                    )

                    if image_data:
                        used_provider = provider_label
                        break

                except Exception as e:
                    logger.warning(f"provider_failed: {provider}, error={str(e)}")
                    continue

            if image_data:
                # Create image element
                image_element = cl.Image(content=image_data, name="generated_image")

                # Update message with image
                await processing_msg.remove()
                await cl.Message(
                    content=f"✨ **Image Generated** via {used_provider}\n\n`{description}`",
                    elements=[image_element],
                    author="ALEM",
                ).send()

                logger.info(f"image_generation_success: provider={used_provider}")
            else:
                await processing_msg.remove()
                await cl.Message(
                    content="❌ **Image generation failed**\n\nAll providers unavailable or errored. Please check:\n- Ollama running on port 11434\n- Groq API key configured\n- HF API key configured\n- OpenAI API key configured",
                    author="System",
                ).send()

        except Exception as e:
            await processing_msg.remove()
            logger.error(f"image_generation_error: {str(e)}", exc_info=True)
            await cl.Message(
                content=f"❌ **Image generation error:** {str(e)}",
                author="System",
            ).send()

    async def _handle_farm(self, farm_id: str | None = None):
        """Switch farm context."""
        if not farm_id:
            current_farm = cl.user_session.get("farm_id", "demo_farm_001")
            await cl.Message(
                content=f"🌾 **Current Farm:** `{current_farm}`\n\nUsage: `/farm <farm_id>`",
                author="System",
            ).send()
            return

        # Update farm context
        old_farm = cl.user_session.get("farm_id")
        cl.user_session.set("farm_id", farm_id)
        logger.info(f"farm_switched: {old_farm} -> {farm_id}")

        await cl.Message(
            content=f"✅ **Farm switched to:** `{farm_id}`",
            author="System",
        ).send()

    async def _handle_mode(self, mode_name: str | None = None):
        """Switch interaction mode."""
        if not mode_name:
            current_mode = cl.user_session.get("chat_profile", "fast")
            await cl.Message(
                content=f"🤖 **Current Mode:** `{current_mode}`\n\n**Available modes:**\n- `fast` - Quick responses\n- `thinking` - Reasoning mode\n- `agent` - Full agent with tools\n\nUsage: `/mode <mode_name>`",
                author="System",
            ).send()
            return

        # Validate mode
        valid_modes = ["fast", "thinking", "agent", "ask", "plan"]
        if mode_name.lower() not in valid_modes:
            await cl.Message(
                content=f"❌ Invalid mode: `{mode_name}`\nValid modes: {', '.join(valid_modes)}",
                author="System",
            ).send()
            return

        # Update mode
        cl.user_session.set("chat_profile", mode_name.lower())
        logger.info(f"mode_switched: {mode_name}")

        await cl.Message(
            content=f"✅ **Mode switched to:** `{mode_name}`",
            author="System",
        ).send()

    async def _handle_debug(self):
        """Show debug information."""
        session_info = {
            "user_id": cl.user_session.get("user_id", "anonymous"),
            "thread_id": cl.user_session.get("thread_id"),
            "farm_id": cl.user_session.get("farm_id"),
            "chat_profile": cl.user_session.get("chat_profile"),
            "expertise_areas": cl.user_session.get("expertise_areas"),
            "mcp_enabled": cl.user_session.get("mcp_enabled"),
            "active_model": cl.user_session.get("active_model", {}).get("model"),
        }

        debug_text = (
            "🐛 **Debug Information:**\n\n```json\n"
            + json.dumps(session_info, indent=2, ensure_ascii=False)
            + "\n```"
        )

        await cl.Message(content=debug_text, author="System").send()


# ============================================
# COMMAND PARSER
# ============================================


def parse_command(message: str) -> tuple[str | None, list[str]]:
    """Parse command from message.

    Args:
        message: User message

    Returns:
        (command_name, arguments) or (None, []) if not a command
    """
    if not message.startswith("/"):
        return None, []

    parts = message[1:].split()  # Remove / and split
    if not parts:
        return None, []

    command_name = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    return command_name, args


async def handle_command(message: str, registry: CommandRegistry) -> bool:
    """Handle command if message is a command.

    Args:
        message: User message
        registry: CommandRegistry instance

    Returns:
        True if command was handled, False if not a command
    """
    command_name, args = parse_command(message)

    if not command_name:
        return False

    await registry.execute(command_name, args)
    return True


# ============================================
# SINGLETON INSTANCE
# ============================================
_command_registry: CommandRegistry | None = None


def get_command_registry() -> CommandRegistry:
    """Get or create singleton command registry."""
    global _command_registry
    if _command_registry is None:
        _command_registry = CommandRegistry()
    return _command_registry
