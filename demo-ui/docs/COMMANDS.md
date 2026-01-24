# 🎮 ALEM Command System

Discord-style slash commands for ALEM agricultural assistant.

## 📋 Available Commands

### System Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/help` | Show all available commands | `/help` |
| `/mcp` | Show MCP server status | `/mcp` |
| `/status` | Show system status (alias for /mcp) | `/status` |
| `/clear` | Clear conversation history | `/clear` |
| `/settings` | Open settings panel | `/settings` |
| `/debug` 🔒 | Show debug information | `/debug` |

### Agricultural Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/weather` | Get weather forecast for current farm | `/weather` |
| `/irrigation` | Get irrigation recommendations | `/irrigation` |
| `/subsidy` | Check subsidy eligibility | `/subsidy` |
| `/calendar` | Show agricultural calendar | `/calendar` |

### Context Management

| Command | Description | Usage | Example |
|---------|-------------|-------|---------|
| `/farm` | Switch farm context | `/farm <farm_id>` | `/farm demo_farm_002` |
| `/mode` | Switch interaction mode | `/mode <fast\|thinking\|agent>` | `/mode agent` |

🔒 = Requires authentication

## 🏗️ Architecture

### Command Registry Pattern

```python
# services/commands.py
class CommandRegistry:
    """Registry of available slash commands."""

    def register(self, command: Command):
        """Register a command."""

    def execute(self, command_name: str, args: list[str]) -> bool:
        """Execute a command by name."""

    def get_help_text(self) -> str:
        """Generate help text for all commands."""
```

### Command Dataclass

```python
@dataclass
class Command:
    """Command definition."""
    name: str  # Command name (without /)
    description: str  # User-friendly description
    handler: Callable  # Async function to execute
    parameters: Optional[list] = None  # Optional parameters
    enabled_modes: Optional[list] = None  # Modes where command is available
    requires_auth: bool = False  # Requires authenticated user
```

### Integration with Chainlit

```python
# app.py
@cl.on_message
async def on_message(message: cl.Message):
    # Command system intercepts messages starting with /
    from services.commands import handle_command, get_command_registry

    command_registry = get_command_registry()
    if await handle_command(message.content.strip(), command_registry):
        return  # Command handled, don't process as chat message

    # Normal message processing continues...
```

## 🚀 Usage Examples

### User Types Command

```
/help
```

**System Response:**
```
📋 Available Commands:

/calendar - 📅 Show agricultural calendar
/clear - 🗑️ Clear conversation history
/debug - 🐛 Show debug information 🔒
/farm <farm_id> - 🌾 Switch farm context
/help - 🆘 Show available commands
/irrigation - 💧 Get irrigation recommendations
/mcp - 🔌 Show MCP server status
/mode <mode_name> - 🤖 Switch interaction mode (Ask/Plan/Agent)
/settings - ⚙️ Open settings panel
/status - 📊 Show system status
/subsidy - 📋 Check subsidy eligibility
/weather - 🌤️ Get weather forecast
```

### MCP Status Command

```
/mcp
```

**System Response:**
```
🔌 MCP Server Status

🟢 ZekaLab MCP Server: Connected
🟢 Tools Available: 15
🟢 Profile: agent (all tools enabled)

Available Tools:
  ✓ check_irrigation_needs
  ✓ get_fertilization_plan
  ✓ analyze_pest_risk
  ... (12 more)

🌐 Server URL: http://localhost:7777
```

### Farm Switch Command

```
/farm demo_farm_002
```

**System Response:**
```
✅ Farm switched to: demo_farm_002
```

### Mode Switch Command

```
/mode agent
```

**System Response:**
```
✅ Mode switched to: agent
```

## 🔧 Adding New Commands

### 1. Register Command in CommandRegistry

```python
# services/commands.py
def _register_builtin_commands(self):
    # ... existing commands

    # Add new command
    self.register(
        Command(
            name="soil",
            description="🌱 Get soil analysis",
            handler=self._handle_soil,
            parameters=["parcel_id"],  # Optional
            enabled_modes=["agent"],  # Only in agent mode
        )
    )
```

### 2. Implement Handler

```python
# services/commands.py
async def _handle_soil(self, parcel_id: Optional[str] = None):
    """Get soil analysis for parcel."""
    if not parcel_id:
        await cl.Message(
            content="🌱 **Soil Analysis**\n\nUsage: `/soil <parcel_id>`",
            author="System",
        ).send()
        return

    # Fetch soil data
    await cl.Message(
        content=f"🌱 **Soil Analysis for Parcel:** `{parcel_id}`\n\nAnalyzing...",
        author="ALEM",
    ).send()
```

### 3. Document Command

Add to this COMMANDS.md file and update `/help` output.

## 🧪 Testing Commands

### Manual Testing

1. Start ALEM UI:
   ```powershell
   .\activate.ps1
   chainlit run demo-ui/app.py -w
   ```

2. Open http://localhost:8001

3. Type commands in chat:
   - `/help` - Should show all commands
   - `/mcp` - Should show MCP status
   - `/farm demo_farm_001` - Should switch farm
   - `/clear` - Should clear conversation

### Automated Testing

```python
# tests/unit/test_commands.py
import pytest
from services.commands import CommandRegistry, parse_command

def test_parse_command():
    """Test command parsing."""
    cmd, args = parse_command("/help")
    assert cmd == "help"
    assert args == []

    cmd, args = parse_command("/farm demo_farm_001")
    assert cmd == "farm"
    assert args == ["demo_farm_001"]

def test_command_registry():
    """Test command registration."""
    registry = CommandRegistry()

    # Built-in commands should be registered
    assert registry.get("help") is not None
    assert registry.get("mcp") is not None

    # Invalid command should return None
    assert registry.get("invalid") is None
```

## 🎯 Roadmap

### Phase 1: Core Commands ✅
- [x] Help command
- [x] MCP status
- [x] Clear conversation
- [x] Settings
- [x] Farm/mode switching

### Phase 2: Agricultural Commands 🔄
- [x] Weather placeholder
- [x] Irrigation placeholder
- [x] Subsidy placeholder
- [x] Calendar placeholder
- [ ] Integrate with real MCP tools
- [ ] Add soil analysis
- [ ] Add pest management

### Phase 3: Advanced Features 📋
- [ ] Command autocomplete in message bar
- [ ] Parameter validation and hints
- [ ] Command history (arrow up/down)
- [ ] Aliases (/w → /weather)
- [ ] Command chaining (/farm X && /weather)
- [ ] Custom user commands

### Phase 4: UI Enhancements 📋
- [ ] Commands button in UI (Discord-style)
- [ ] Command palette (Ctrl+K)
- [ ] Rich command responses with buttons
- [ ] Command shortcuts sidebar

## 🐛 Known Issues

1. **No autocomplete yet**: Commands don't appear in autocomplete dropdown (requires Chainlit 3.0 API)
2. **No parameter validation**: Invalid parameters are not validated before execution
3. **No command history**: Arrow up/down doesn't cycle through command history

## 📚 References

- [Chainlit Documentation](https://docs.chainlit.io/)
- [Discord Slash Commands](https://discord.com/developers/docs/interactions/application-commands)
- [Command Pattern (Design Patterns)](https://refactoring.guru/design-patterns/command)

---

**Last Updated:** 2024-12-20
**Version:** 1.0.0
**Maintainer:** ALEM Development Team
