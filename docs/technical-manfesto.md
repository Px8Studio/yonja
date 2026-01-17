ok i love what i see #codebase 

but i wonder have we overcreated files the same functionality elsehwere... looking at the whole codebase what is your analysis and critical review of stale code, duplciation of effort and confusion, what do weo do, do we consolidate any relevant rich code with the existing streamlit app?

but remember 

This document serves as the formal **Technical Manifesto** and **Architectural Blueprint** for the Yonca AI Prototype. It outlines our strategic choices, design standards, and the "Logic-First" methodology required to deliver a high-accuracy, integratable AI engine for Digital Umbrella.

---

## 1. Executive Standpoint: The "Sidecar" Strategy

Our primary architectural decision is the **Sidecar Intelligence Model**. Instead of proposing a rebuild of the Yonca platform, we position our prototype as a detached, high-performance module.

* **Integration Philosophy:** The AI engine communicates exclusively via a **Headless API Layer (REST/GraphQL)**. This ensures that Digital Umbrella’s core GovTech and subsidy systems remain untouched and secure.
* **Data Sovereignty:** By utilizing **100% Synthetic Datasets**, we remove all legal and operational friction. The system is built to ingest "Real World" data hooks in the future without changing the underlying logic.
* **Edge-Ready Logic:** We prioritize **Lightweight Inference**. Our choice of **Qwen2.5-7B (Quantized)** ensures that the engine can run on local farm servers or in low-connectivity zones, fulfilling the "Data Safety" and "Low Connectivity" requirements.

---

## 2. Architectural Blueprint (IT Standards)

To ensure the prototype is "Production-Ready," we adhere to the following technical stack and data flow:

| Layer | Standard / Tool | Purpose |
| --- | --- | --- |
| **Inference Engine** | Qwen2.5-7B (GGUF) | Multilingual logic & local execution. |
| **Logic Layer** | Deterministic Agronomy Rulebook | Overrides LLM "hallucinations" with hard rules. |
| **API Framework** | FastAPI (Swagger/OpenAPI) | Provides the integratable backend documentation. |
| **UI Framework** | Mobile-Framed Streamlit | High-speed logic validation with a mobile "look." |
| **Data Engine** | Synthetic Scenario Manager | Generates 5 distinct farm profiles (Wheat, Livestock, etc.). |

### Data Flow Diagram (Conceptual)

`Farmer Input (AZ)` → `Intent Matcher` → `Synthetic Profile Lookup` → `Agronomy Logic Check` → `LLM Response Generation` → `JSON Payload` → `Mobile UI Card`

---

## 3. UI/UX Declaration of Standards

The UI is designed to be **Invisible yet Informative**. We follow the "Contextual Card" pattern used in modern high-end mobile ecosystems.

* **Visual Continuity:** We utilize the **Yonca Palette** (Forest Green `#2E7D32`) and rounded-corner surfaces (15px) to match their existing brand identity.
* **The "Why" Factor:** Every AI recommendation includes a **Source Citation** (e.g., *Rule: Early Frost Protection v1.2*). Farmers trust logic they can verify.
* **Native-First Viewport:** Even within a web-based demo (Streamlit), we force a **Mobile Aspect Ratio** to prevent "Desktop Drift" and show immediate compatibility with their smartphone app.

---

## 4. Master Prompt: Claude 4.5 Implementation Directive

*The following block is the "Source Truth" to be used in your LLM dev environment (Claude/Copilot) to generate the actual codebase.*

> **[PROMPT START]**
> **CONTEXT:** Developing an AI Prototype for "Yonca," a digital agri-platform.
> **TASK:** Implement a Streamlit-based "Personalized Farm Assistant" utilizing 100% synthetic data.
> **CORE MODULES REQUIRED:**
> 1. **`ScenarioEngine`**: A Python class containing 5 JSON-based synthetic profiles (Wheat, Livestock, Orchard, Mixed, Poultry).
> 2. **`AgronomyGuard`**: A rule-based logic validator. If AI suggests irrigation during a rain event (synthetic data), the Guard overrides it.
> 3. **`InferenceSim`**: A mock function simulating Qwen2.5-7B responses in Azerbaijani.
> 4. **`MobileUI`**: A Streamlit frontend with:
> * Custom CSS for a centered 400px mobile shell.
> * Green/White Yonca-branded "Advisory Cards."
> * Azerbaijani intent-based chat input.
> 
> 
> 
> 
> **DESIGN SPEC:** > - No Streamlit sidebars.
> * Use "WhatsApp-style" chat bubbles for interaction.
> * Display "Logical Accuracy" scores for every recommendation.
> 
> 
> **LANGUAGE:** All user-facing text must be in **natural Azerbaijani**. Code comments in English.
> **[PROMPT END]**

---

## 5. Success Metric Validation

Our standpoint ensures we hit all the challenge's "Success Indicators":

1. **Logical Accuracy (≥ 90%)**: Achieved via the `AgronomyGuard` rule-base.
2. **100% Data Safety**: Guaranteed by the `ScenarioEngine` synthetic isolation.
3. **UX Compatibility**: Demonstrated by the Mobile-First CSS Injection.