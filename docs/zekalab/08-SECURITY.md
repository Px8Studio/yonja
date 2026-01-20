# 🔐 ALEM Security Guide

> **Purpose:** Security controls and threat mitigations for ALEM.

---

## ✅ Implementation Status

| Component | Status | Location |
|:----------|:-------|:---------|
| **Input Validator** | ✅ | `src/yonca/security/input_validator.py` |
| **Output Validator** | ✅ | `src/yonca/security/output_validator.py` |
| **PII Gateway** | ✅ | `src/yonca/security/pii_gateway.py` |
| Rate Limiting | ✅ | Redis-based |
| CORS | ✅ | FastAPI config |
| JWT Validation | ✅ | Auth module |
| OAuth | 🔄 | Google OAuth in Chainlit |
| RBAC | ⏳ | Planned |

---

## 🛡️ Security Architecture

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph layer1["🚪 Layer 1: Edge"]
        rate["Rate Limiter<br/>30 req/min"]
        cors["CORS Policy"]
    end
    
    subgraph layer2["🔍 Layer 2: Input"]
        length["Length Check<br/>≤2000 chars"]
        injection["Injection Scan"]
    end
    
    subgraph layer3["🛡️ Layer 3: PII"]
        pii["PII Gateway"]
    end
    
    subgraph layer4["🤖 Layer 4: AI Safety"]
        guardrails["Output Guardrails"]
    end
    
    subgraph core["✅ Safe Zone"]
        llm["LLM Processing"]
    end
    
    layer1 --> layer2 --> layer3 --> layer4 --> core
    
    style layer1 fill:#ffcdd2,stroke:#c62828
    style layer2 fill:#fff3e0,stroke:#f57c00
    style layer3 fill:#e3f2fd,stroke:#1565c0
    style layer4 fill:#e8f5e9,stroke:#2e7d32
    style core fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
```

---

## 🎯 Threat Matrix

| Threat | Likelihood | Impact | Mitigation |
|:-------|:-----------|:-------|:-----------|
| **Prompt Injection** | High | High | Input validator, guardrails |
| **PII Leakage** | Medium | Critical | PII gateway (synthetic data only) |
| **DDoS** | Medium | Medium | Rate limiting |
| **Jailbreak** | High | Medium | Output validator, redlines |

---

## 🔍 Input Validation

```python
# src/yonca/security/input_validator.py
class InputValidator:
    MAX_LENGTH = 2000
    
    def validate(self, text: str) -> ValidationResult:
        # 1. Length check
        # 2. UTF-8 encoding check
        # 3. Control character removal
        # 4. Injection pattern detection
        pass
```

**Blocked patterns:**
- Control characters (`\x00-\x08`, etc.)
- Known injection templates
- System prompt override attempts

---

## 🛡️ PII Gateway

```python
# src/yonca/security/pii_gateway.py
class PIIGateway:
    """Strip or anonymize PII before LLM processing."""
    
    PATTERNS = {
        "fin": r"\b[A-Z0-9]{7}\b",  # Azerbaijani FİN
        "phone": r"\+994\d{9}",
        "email": r"[a-z0-9._%+-]+@[a-z0-9.-]+",
    }
```

> **Note:** ALEM uses synthetic data only. Real PII should never reach the system.

---

## 🤖 Output Guardrails

**Must block:**
- Medical/legal advice
- Non-agricultural topics
- Fabricated statistics
- Specific brand names

**Must include:**
- Uncertainty acknowledgment when appropriate
- "Consult expert" for edge cases
- Source attribution (rule codes)

---

## 🔑 Authentication Flow

```mermaid
%%{init: {'theme': 'neutral'}}%%
sequenceDiagram
    participant U as User
    participant C as Chainlit
    participant G as Google OAuth
    participant DB as PostgreSQL
    
    U->>C: Access /
    C->>G: Redirect to OAuth
    G->>C: Return token
    C->>DB: Upsert user record
    C->>U: Authenticated session
```

---

## 📋 Security Principles

| Principle | Implementation |
|:----------|:---------------|
| **Defense in Depth** | Multiple validation layers |
| **Least Privilege** | Minimal permissions per component |
| **Fail Secure** | Deny by default on errors |
| **Synthetic Only** | No real farmer data in prototype |
