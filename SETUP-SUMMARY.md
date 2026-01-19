# ✅ Command Line Setup Complete!

## 🎯 What Was Created

### 1. **activate.ps1** - PowerShell Quick Activate
```powershell
# Activate environment and see available commands
.\activate.ps1

# Show help without activating
.\activate.ps1 -Info
```

### 2. **activate.bat** - CMD/Batch Quick Activate
```cmd
REM For Windows Command Prompt users
activate.bat

REM Show help
activate.bat -info
```

### 3. **Poetry Scripts** (in pyproject.toml)
```powershell
# Run without activating environment
poetry run dev        # Start FastAPI server
poetry run migrate    # Run Alembic migrations
poetry run seed       # Seed database
```

### 4. **COMMANDS.md** - Comprehensive Reference
Complete guide to all three methods of running commands.

---

## 🚀 Now You Can Use Commands Three Ways

### Method 1: Poetry Shell (Clean & Interactive)
```powershell
# Activate once per terminal session
poetry shell

# Then use commands directly
uvicorn yonca.api.main:app --reload
alembic upgrade head
chainlit run demo-ui/app.py --port 8501
```

### Method 2: Quick Activate Script
```powershell
# One command activation
.\activate.ps1

# Then use commands directly  
uvicorn yonca.api.main:app --reload
alembic upgrade head
```

### Method 3: Poetry Run (No Activation)
```powershell
# Works in any terminal
poetry run dev        # Start API
poetry run migrate    # Migrations
poetry run seed       # Seed DB
```

---

## 🎓 Why This Happens

**The Problem:**
Windows doesn't automatically find executables in virtual environments. Commands like `uvicorn` and `alembic` are in `.venv\Scripts\`, which isn't in your `PATH`.

**The Solution:**
1. **Activate the environment** - Temporarily adds `.venv\Scripts\` to PATH
2. **Use Poetry run** - Poetry handles paths automatically
3. **Use full paths** - Specify exact location (verbose but works)

**Best Practice:**
- **Development:** Use `poetry shell` once per terminal
- **Scripts/CI:** Use `poetry run` for reproducibility
- **VS Code:** Use Tasks (they handle paths automatically)

---

## 🔍 Quick Verification

Test your setup:
```powershell
# Test 1: Poetry shell
poetry shell
uvicorn --version
alembic --version
exit

# Test 2: Poetry run
poetry run python -c "import uvicorn; print(uvicorn.__version__)"

# Test 3: Quick activate
.\activate.ps1
uvicorn --version
```

All three should work without errors!

---

## 📚 Reference Documents

- **[COMMANDS.md](COMMANDS.md)** - Complete command reference (⭐ recommended)
- **[README.md](README.md)** - Full project documentation
- **[QUICK-START.md](QUICK-START.md)** - Testing the API
- **[pyproject.toml](pyproject.toml)** - Poetry scripts configuration

---

## 💡 Pro Tips

1. **Add alias to PowerShell profile:**
   ```powershell
   # Edit: notepad $PROFILE
   function yonca { cd C:\Users\rjjaf\_Projects\yonja; poetry shell }
   ```

2. **Use VS Code integrated terminal:**
   - Opens in project directory automatically
   - Can auto-activate virtual environments
   - Tasks use correct paths automatically

3. **Check if environment is active:**
   ```powershell
   # Look for prompt prefix
   (yonca-ai) PS C:\Users\rjjaf\_Projects\yonja>
   ```

4. **Install shell autocompletion:**
   ```powershell
   # For Poetry autocompletion
   poetry completions powershell | Out-String | Invoke-Expression
   ```

---

**🎉 You're all set! No more "command not recognized" errors!**

See [COMMANDS.md](COMMANDS.md) for the complete reference.
