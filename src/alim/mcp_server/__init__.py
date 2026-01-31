# src/ALİM/mcp_server/__init__.py
"""ZekaLab Internal MCP Server.

Exposes ALİM's agricultural rules engine as standardized MCP tools.

Philosophy:
    MCP Server = "Smart USB Port" for your rules engine
    - Tools: RPC-style callable operations
    - Resources: Read-only data retrieval
    - JSON-RPC 2.0 over stdio

Architecture:
    ├── Tools (5 total):
    │   ├── evaluate_irrigation_rules(context)
    │   ├── evaluate_fertilization_rules(context)
    │   ├── evaluate_pest_control_rules(context)
    │   ├── calculate_subsidy(params)
    │   └── predict_harvest_date(context)
    │
    └── Resources (3 total):
        ├── rules_yaml (all rules as text)
        ├── crop_profiles (crop data)
        └── subsidy_database (subsidy info)

Usage:
    python -m ALİM.mcp_server.main

Environment:
    ZEKALAB_PORT=7777
    ZEKALAB_LOG_LEVEL=INFO
    ZEKALAB_RULES_PATH=src/ALİM/rules
"""
