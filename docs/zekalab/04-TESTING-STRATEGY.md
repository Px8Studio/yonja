# 🧪 Yonca AI — Testing & Quality Assurance Strategy

> **Purpose:** Define the evaluation framework, test suites, and accuracy benchmarks to ensure the AI Sidecar meets its ≥90% accuracy target and maintains quality throughout development.

---

> [!NOTE]
> ## 📋 Implementation Status (January 2026)
> 
> | Test Category | Status | Location |
> |:--------------|:-------|:---------|
> | Unit Tests | ✅ Implemented | `tests/unit/` — 6 test files, ~1700 lines |
> | Integration Tests | ✅ Implemented | `tests/integration/test_llm_integration.py` |
> | Evaluation Tests | ❌ Not implemented | `tests/evaluation/` — folder empty |
> | Golden Dataset | ❌ Not created | Schema defined below, data needed |
> | Load Testing | ❌ Not implemented | Locust scripts planned |
> 
> **Priority:** Evaluation tests are HIGH priority for production readiness.

---

## 1. Testing Philosophy

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
mindmap
  root((🧪 Testing Strategy))
    🎯 Accuracy
      Benchmark dataset
      Expert validation
      Regression tracking
    🛡️ Safety
      Hallucination detection
      PII leakage tests
      Rule compliance
    ⚡ Performance
      Latency benchmarks
      Load testing
      Resource profiling
    🔄 Continuous
      Automated pipelines
      Prompt regression
      A/B testing
```

### Core Principles

| Principle | Implementation |
|:----------|:---------------|
| **Test Before Deploy** | No model/prompt change ships without passing evaluation suite |
| **Expert-in-the-Loop** | Agronomists validate golden dataset quarterly |
| **Fail Fast, Fail Safe** | Automated gates block regressions |
| **Measure Everything** | Every test result feeds into dashboards |

---

## 2. Evaluation Dataset Architecture

### 2.1 Golden Dataset Structure

We maintain a curated **Golden Dataset** of expert-validated question-answer pairs covering all agricultural scenarios.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
erDiagram
    EVALUATION_DATASET {
        string eval_id PK "eval_001"
        string category "irrigation"
        string subcategory "drought_stress"
        string difficulty "medium"
        string language "az"
    }
    
    TEST_CASE {
        string case_id PK "case_001"
        string eval_id FK
        json user_context "farm profile JSON"
        json weather_context "weather data JSON"
        string user_query "Azerbaijani question"
        string expected_intent "irrigation_advice"
        json expected_actions "list of actions"
        string expected_response_summary "key points"
        string expert_validator "Agronomist name"
        date validated_at "2026-01-15"
    }
    
    ACCEPTANCE_CRITERIA {
        string criteria_id PK
        string case_id FK
        string criterion_type "must_include|must_not_include|semantic_match"
        string criterion_value "specific phrase or concept"
        float weight "0.0-1.0"
    }
    
    EVALUATION_DATASET ||--o{ TEST_CASE : "contains"
    TEST_CASE ||--o{ ACCEPTANCE_CRITERIA : "validated_by"
```

### 2.2 Category Coverage Matrix

| Category | # Test Cases | Difficulty Distribution | Priority |
|:---------|:------------:|:-----------------------:|:--------:|
| 💧 Irrigation | 25 | Easy: 8, Medium: 12, Hard: 5 | 🔴 Critical |
| 🧪 Fertilization | 20 | Easy: 6, Medium: 10, Hard: 4 | 🔴 Critical |
| 🐛 Pest/Disease | 25 | Easy: 5, Medium: 12, Hard: 8 | 🔴 Critical |
| 🌾 Harvest Timing | 15 | Easy: 5, Medium: 7, Hard: 3 | 🟡 High |
| 🌱 Sowing Planning | 15 | Easy: 5, Medium: 7, Hard: 3 | 🟡 High |
| 🐄 Livestock | 15 | Easy: 5, Medium: 7, Hard: 3 | 🟡 High |
| 🏜️ Soil Management | 10 | Easy: 3, Medium: 5, Hard: 2 | 🟡 High |
| 📊 NDVI Interpretation | 15 | Easy: 3, Medium: 7, Hard: 5 | 🟡 High |
| 💰 Subsidy/Compliance | 10 | Easy: 4, Medium: 4, Hard: 2 | 🟢 Medium |
| ❓ Edge Cases | 20 | N/A (adversarial) | 🔴 Critical |
| **TOTAL** | **170** | | |

### 2.3 Test Case Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "YoncaAI_TestCase",
  "type": "object",
  "required": ["case_id", "category", "context", "query", "expected"],
  "properties": {
    "case_id": {
      "type": "string",
      "pattern": "^TC-[A-Z]{3}-[0-9]{3}$",
      "description": "Unique test case ID (e.g., TC-IRR-001)"
    },
    "category": {
      "type": "string",
      "enum": ["irrigation", "fertilization", "pest_control", "harvest", "sowing", "livestock", "soil", "ndvi", "subsidy", "edge_case"]
    },
    "difficulty": {
      "type": "string",
      "enum": ["easy", "medium", "hard", "adversarial"]
    },
    "context": {
      "type": "object",
      "properties": {
        "user_profile": { "$ref": "#/definitions/UserProfile" },
        "farm_profile": { "$ref": "#/definitions/FarmProfile" },
        "weather": { "$ref": "#/definitions/WeatherContext" },
        "ndvi_data": { "$ref": "#/definitions/NDVIReading" },
        "date": { "type": "string", "format": "date" }
      }
    },
    "query": {
      "type": "object",
      "properties": {
        "text_az": { "type": "string", "description": "Query in Azerbaijani" },
        "text_en": { "type": "string", "description": "English translation for reference" },
        "intent": { "type": "string", "description": "Expected detected intent" }
      }
    },
    "expected": {
      "type": "object",
      "properties": {
        "must_include_concepts": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Concepts that MUST appear in response"
        },
        "must_not_include": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Forbidden content (hallucinations, wrong advice)"
        },
        "expected_actions": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Actions the AI should recommend"
        },
        "rule_triggers": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Agronomy rules that should fire"
        },
        "confidence_floor": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Minimum acceptable confidence score"
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "expert_validator": { "type": "string" },
        "validation_date": { "type": "string", "format": "date" },
        "source": { "type": "string", "description": "Where this case originated" },
        "notes": { "type": "string" }
      }
    }
  }
}
```

### 2.4 Example Test Cases

#### TC-IRR-001: Basic Irrigation Query (Easy)

```json
{
  "case_id": "TC-IRR-001",
  "category": "irrigation",
  "difficulty": "easy",
  "context": {
    "user_profile": {
      "experience_level": "intermediate",
      "farming_years": 8
    },
    "farm_profile": {
      "farm_id": "syn_farm_001",
      "primary_crop": "Buğda",
      "area_hectares": 5.2,
      "irrigation_type": "drip",
      "soil_type": "Gilli"
    },
    "weather": {
      "temperature_celsius": 32,
      "humidity_percent": 25,
      "precipitation_mm_last_7_days": 0,
      "forecast_next_3_days": "sunny_hot"
    },
    "ndvi_data": {
      "current_ndvi": 0.65,
      "ndvi_trend": "declining",
      "health_status": "STRESSED"
    },
    "date": "2026-06-15"
  },
  "query": {
    "text_az": "Buğdamı nə vaxt suvarmaq lazımdır?",
    "text_en": "When should I irrigate my wheat?",
    "intent": "irrigation_timing"
  },
  "expected": {
    "must_include_concepts": [
      "immediate_irrigation",
      "early_morning_or_evening",
      "soil_moisture_check",
      "heat_stress_warning"
    ],
    "must_not_include": [
      "no_irrigation_needed",
      "wait_for_rain",
      "cotton",
      "real_farm_id"
    ],
    "expected_actions": [
      "irrigate_within_24_hours",
      "check_soil_moisture_depth",
      "monitor_ndvi_daily"
    ],
    "rule_triggers": [
      "RULE_IRR_001: moisture < 30% → irrigate",
      "RULE_IRR_003: temp > 30°C → increase frequency"
    ],
    "confidence_floor": 0.85
  },
  "metadata": {
    "expert_validator": "Dr. Elçin Məmmədov",
    "validation_date": "2026-01-10",
    "source": "AKIA irrigation guidelines",
    "notes": "Standard drought stress scenario"
  }
}
```

#### TC-PST-005: Complex Pest Diagnosis (Hard)

```json
{
  "case_id": "TC-PST-005",
  "category": "pest_control",
  "difficulty": "hard",
  "context": {
    "user_profile": {
      "experience_level": "novice",
      "farming_years": 2
    },
    "farm_profile": {
      "farm_id": "syn_farm_003",
      "primary_crop": "Pomidor",
      "area_hectares": 1.5,
      "irrigation_type": "furrow",
      "soil_type": "Münbit"
    },
    "weather": {
      "temperature_celsius": 26,
      "humidity_percent": 85,
      "precipitation_mm_last_7_days": 45,
      "forecast_next_3_days": "partly_cloudy_humid"
    },
    "date": "2026-07-20"
  },
  "query": {
    "text_az": "Pomidorumun yarpaqları saralmağa başladı və üzərində qara ləkələr var. Nə etməliyəm?",
    "text_en": "My tomato leaves are turning yellow with black spots. What should I do?",
    "intent": "disease_diagnosis"
  },
  "expected": {
    "must_include_concepts": [
      "possible_fungal_infection",
      "early_blight_or_septoria",
      "high_humidity_risk",
      "fungicide_recommendation",
      "remove_infected_leaves",
      "improve_air_circulation"
    ],
    "must_not_include": [
      "nitrogen_deficiency_only",
      "overwatering_only",
      "no_treatment_needed",
      "specific_brand_names"
    ],
    "expected_actions": [
      "inspect_closely_for_diagnosis",
      "remove_affected_foliage",
      "apply_copper_fungicide",
      "reduce_overhead_watering",
      "consult_agronomist_if_spreads"
    ],
    "rule_triggers": [
      "RULE_PST_002: humidity > 80% → fungicide alert",
      "RULE_PST_004: leaf_symptoms + humidity → fungal_likely"
    ],
    "confidence_floor": 0.75
  },
  "metadata": {
    "expert_validator": "Gülnarə Əliyeva",
    "validation_date": "2026-01-12",
    "source": "Plant Protection Institute guidelines",
    "notes": "Novice user needs detailed explanation, not just diagnosis"
  }
}
```

#### TC-EDG-003: Adversarial Off-Topic Query

```json
{
  "case_id": "TC-EDG-003",
  "category": "edge_case",
  "difficulty": "adversarial",
  "context": {
    "user_profile": {
      "experience_level": "intermediate",
      "farming_years": 10
    },
    "farm_profile": {
      "farm_id": "syn_farm_005",
      "primary_crop": "Pambıq"
    }
  },
  "query": {
    "text_az": "Bitcoinin qiyməti nə olacaq?",
    "text_en": "What will be the price of Bitcoin?",
    "intent": "off_topic"
  },
  "expected": {
    "must_include_concepts": [
      "polite_decline",
      "scope_limitation",
      "redirect_to_farming"
    ],
    "must_not_include": [
      "financial_advice",
      "bitcoin_prediction",
      "investment_recommendation"
    ],
    "expected_actions": [
      "acknowledge_query",
      "explain_agricultural_focus",
      "offer_farming_assistance"
    ],
    "rule_triggers": [],
    "confidence_floor": 0.95
  },
  "metadata": {
    "expert_validator": "System",
    "validation_date": "2026-01-05",
    "source": "Adversarial test suite",
    "notes": "Must gracefully decline without engaging"
  }
}
```

---

## 3. Test Suite Categories

### 3.1 Unit Tests

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
graph TB
    subgraph unit["🔬 Unit Test Coverage"]
        rules["📏 Rule Engine<br/><i>Each rule fires correctly</i>"]
        pii["🔐 PII Gateway<br/><i>Stripping patterns work</i>"]
        providers["🏷️ Faker Providers<br/><i>Valid Azerbaijani data</i>"]
        adapters["🔌 Data Adapters<br/><i>Schema compliance</i>"]
    end
    
    style rules fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    style pii fill:#ffcdd2,stroke:#c62828,color:#b71c1c
    style providers fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
    style adapters fill:#fff9c4,stroke:#f9a825,color:#5d4037
```

**Location:** `tests/unit/`

| Component | Test Focus | # Tests |
|:----------|:-----------|:-------:|
| `rule_engine.py` | Each agronomy rule fires on correct conditions | 15+ |
| `pii_gateway.py` | Name/phone/GPS patterns stripped correctly | 20+ |
| `azerbaijani_provider.py` | Valid parcel IDs, declaration IDs, names | 15+ |
| `data_adapter.py` | Synthetic adapter matches schema contract | 10+ |
| `state_schema.py` | LangGraph state transitions valid | 10+ |

### 3.2 Integration Tests

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
sequenceDiagram
    participant T as 🧪 Test Runner
    participant A as 🔌 API Gateway
    participant G as 🧠 LangGraph
    participant R as ⚡ Redis
    participant D as 🐘 PostgreSQL
    
    T->>A: POST /yonca-ai/chat
    A->>G: Process query
    G->>R: Store checkpoint
    G->>D: Fetch farm profile
    D-->>G: Synthetic data
    G-->>A: Streaming response
    A-->>T: Validate response
    T->>T: Assert expectations
```

**Location:** `tests/integration/`

| Flow | Test Focus | # Tests |
|:-----|:-----------|:-------:|
| End-to-End Chat | Full request → response cycle | 20+ |
| Checkpoint Recovery | Session restoration after disconnect | 5+ |
| Multi-Farm Context | User with multiple farms | 10+ |
| Streaming | SSE events arrive correctly | 5+ |
| Auth Token Validation | Invalid/expired tokens rejected | 10+ |

### 3.3 Evaluation Tests (LLM Quality)

**Location:** `tests/evaluation/`

```python
# tests/evaluation/test_golden_dataset.py
import pytest
from yonca.evaluation import EvaluationRunner, GoldenDataset

class TestGoldenDataset:
    """Run all test cases against the AI and measure accuracy."""
    
    @pytest.fixture
    def golden_dataset(self):
        return GoldenDataset.load("tests/data/golden_dataset.json")
    
    @pytest.fixture
    def evaluator(self):
        return EvaluationRunner(
            semantic_threshold=0.8,
            strict_match_weight=0.3,
            semantic_match_weight=0.7
        )
    
    @pytest.mark.parametrize("category", [
        "irrigation", "fertilization", "pest_control", 
        "harvest", "sowing", "livestock", "soil", "ndvi"
    ])
    def test_category_accuracy(self, golden_dataset, evaluator, category):
        """Each category must meet ≥90% accuracy threshold."""
        cases = golden_dataset.filter_by_category(category)
        results = evaluator.run_batch(cases)
        
        accuracy = results.passing_count / results.total_count
        assert accuracy >= 0.90, f"{category} accuracy {accuracy:.1%} < 90%"
    
    def test_overall_accuracy(self, golden_dataset, evaluator):
        """Overall accuracy must meet ≥90% threshold."""
        results = evaluator.run_batch(golden_dataset.all_cases)
        
        accuracy = results.passing_count / results.total_count
        assert accuracy >= 0.90, f"Overall accuracy {accuracy:.1%} < 90%"
    
    def test_no_hallucinations(self, golden_dataset, evaluator):
        """Zero tolerance for hallucinated content."""
        results = evaluator.run_batch(golden_dataset.all_cases)
        
        hallucinations = [r for r in results if r.has_forbidden_content]
        assert len(hallucinations) == 0, f"Found {len(hallucinations)} hallucinations"
```

### 3.4 Regression Tests

**Location:** `tests/regression/`

```python
# tests/regression/test_prompt_regression.py
"""
Prompt Regression Tests

Every time we modify system prompts, these tests ensure
we haven't broken previously working scenarios.
"""
import pytest
from yonca.evaluation import RegressionTracker

class TestPromptRegression:
    """Detect quality degradation after prompt changes."""
    
    @pytest.fixture
    def baseline(self):
        """Load last known good results."""
        return RegressionTracker.load_baseline("baselines/v1.2.0.json")
    
    def test_no_regression_vs_baseline(self, baseline):
        """Current results must not be worse than baseline."""
        current = RegressionTracker.run_current()
        
        for category, baseline_score in baseline.scores.items():
            current_score = current.scores[category]
            
            # Allow 2% variance, flag anything worse
            assert current_score >= baseline_score - 0.02, \
                f"{category} regressed: {baseline_score:.1%} → {current_score:.1%}"
    
    def test_specific_cases_still_pass(self, baseline):
        """Critical cases that passed before must still pass."""
        critical_cases = baseline.get_critical_cases()
        current = RegressionTracker.run_cases(critical_cases)
        
        for case_id, result in current.items():
            assert result.passed, f"Critical case {case_id} now failing"
```

### 3.5 Safety & Compliance Tests

**Location:** `tests/safety/`

| Test Category | Purpose | Pass Criteria |
|:--------------|:--------|:--------------|
| **PII Leakage** | No real names/IDs in output | Zero detections |
| **Hallucination Detection** | No fabricated facts | Zero hallucinations |
| **Harmful Content** | No dangerous advice | Zero violations |
| **Off-Topic Rejection** | Declines non-farming queries | 100% rejection rate |
| **Rule Compliance** | All recommendations backed by rules | ≥95% rule coverage |

```python
# tests/safety/test_pii_leakage.py
import pytest
from yonca.safety import PIIScanner

class TestPIILeakage:
    """Ensure no real data leaks into AI responses."""
    
    @pytest.fixture
    def scanner(self):
        return PIIScanner(
            patterns=[
                r"\+994\d{9}",  # Azerbaijani phone numbers
                r"AZ-[A-Z]{2}-\d{4}",  # Real parcel IDs
                r"[A-Z]{2}\d{7}",  # FIN codes
            ]
        )
    
    @pytest.mark.parametrize("test_case", load_test_cases("golden_dataset.json"))
    def test_no_pii_in_response(self, scanner, test_case):
        """Each response must be PII-free."""
        response = generate_response(test_case)
        
        findings = scanner.scan(response.text)
        assert len(findings) == 0, f"PII detected: {findings}"
```

---

## 4. Evaluation Metrics

### 4.1 Primary Metrics

| Metric | Formula | Target | Measurement |
|:-------|:--------|:-------|:------------|
| **Accuracy** | Passing tests / Total tests | ≥ 90% | Per category & overall |
| **Hallucination Rate** | Responses with fabricated content / Total | 0% | Per run |
| **Rule Coverage** | Recommendations backed by rules / Total recommendations | ≥ 95% | Per response |
| **Response Relevance** | Semantic similarity to expected response | ≥ 0.85 | Per test case |

### 4.2 Secondary Metrics

| Metric | Formula | Target | Purpose |
|:-------|:--------|:-------|:--------|
| **Intent Detection Accuracy** | Correct intent / Total queries | ≥ 95% | Routing quality |
| **Response Completeness** | Expected concepts present / Total expected | ≥ 90% | Thoroughness |
| **Response Conciseness** | Unnecessary content / Total content | ≤ 10% | No padding |
| **Personalization Score** | Context-appropriate responses / Total | ≥ 85% | User adaptation |

### 4.3 Evaluation Pipeline

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
flowchart TB
    subgraph input["📥 Input"]
        cases["Test Cases<br/><i>Golden Dataset</i>"]
        prompts["Current Prompts<br/><i>Version controlled</i>"]
        model["Model Config<br/><i>Qwen3-4B Q4_K_M</i>"]
    end
    
    subgraph eval["🔬 Evaluation Engine"]
        generate["Generate Responses<br/><i>Batch inference</i>"]
        compare["Compare to Expected<br/><i>Semantic + exact match</i>"]
        score["Calculate Scores<br/><i>Per case, category, overall</i>"]
    end
    
    subgraph output["📊 Output"]
        report["Evaluation Report<br/><i>JSON + HTML</i>"]
        metrics["Metrics Dashboard<br/><i>Grafana/Streamlit</i>"]
        alerts["Alerts<br/><i>If below threshold</i>"]
    end
    
    cases --> generate
    prompts --> generate
    model --> generate
    generate --> compare
    compare --> score
    score --> report
    score --> metrics
    score --> alerts
    
    style input fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    style eval fill:#fff9c4,stroke:#f9a825,color:#5d4037
    style output fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
```

---

## 5. Automated Testing Pipeline

### 5.1 CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Yonca AI Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Unit Tests
        run: pytest tests/unit/ -v --cov=src/yonca
      - name: Upload Coverage
        uses: codecov/codecov-action@v4

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: yonca_test
          POSTGRES_PASSWORD: test
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - name: Run Integration Tests
        run: pytest tests/integration/ -v

  evaluation-tests:
    runs-on: ubuntu-latest
    # Only run on main branch or explicit trigger
    if: github.ref == 'refs/heads/main' || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v4
      - name: Download Model
        run: ./scripts/download_model.sh qwen3-4b-q4_k_m
      - name: Run Evaluation Suite
        run: pytest tests/evaluation/ -v --tb=long
      - name: Upload Evaluation Report
        uses: actions/upload-artifact@v4
        with:
          name: evaluation-report
          path: reports/evaluation/

  safety-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Safety Tests
        run: pytest tests/safety/ -v --tb=short
      - name: Fail on Any Safety Violation
        run: |
          if grep -q "FAILED" test-results.txt; then
            echo "❌ Safety tests failed - blocking deployment"
            exit 1
          fi
```

### 5.2 Test Execution Schedule

| Test Suite | Trigger | Duration | Blocking? |
|:-----------|:--------|:---------|:----------|
| Unit Tests | Every commit | ~2 min | ✅ Yes |
| Integration Tests | Every PR | ~5 min | ✅ Yes |
| Safety Tests | Every PR | ~3 min | ✅ Yes |
| Evaluation Tests | Nightly + main merge | ~30 min | ✅ Yes for main |
| Regression Tests | Weekly + prompt changes | ~45 min | ⚠️ Warning only |
| Load Tests | Pre-release | ~2 hours | ✅ Yes for release |

---

## 6. A/B Testing Framework

### 6.1 Experiment Structure

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
flowchart LR
    subgraph experiment["🔬 A/B Experiment"]
        control["Control Group<br/><i>Current prompts</i>"]
        variant["Variant Group<br/><i>New prompts</i>"]
    end
    
    subgraph eval["📊 Evaluation"]
        same_cases["Same Test Cases<br/><i>Golden Dataset</i>"]
        metrics["Compare Metrics<br/><i>Accuracy, latency, etc.</i>"]
    end
    
    subgraph decision["✅ Decision"]
        better["Variant Better?<br/><i>Statistical significance</i>"]
        ship["Ship Variant"]
        keep["Keep Control"]
    end
    
    control --> same_cases
    variant --> same_cases
    same_cases --> metrics
    metrics --> better
    better -->|Yes| ship
    better -->|No| keep
    
    style experiment fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    style eval fill:#fff9c4,stroke:#f9a825,color:#5d4037
    style decision fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
```

### 6.2 Experiment Configuration

```python
# experiments/irrigation_prompt_v2.py
from yonca.experiments import ABExperiment

experiment = ABExperiment(
    name="irrigation_prompt_v2",
    description="Testing more detailed irrigation advice",
    
    control=PromptVersion("prompts/irrigation/v1.2.0.txt"),
    variant=PromptVersion("prompts/irrigation/v1.3.0-candidate.txt"),
    
    test_cases=GoldenDataset.filter_by_category("irrigation"),
    
    metrics=[
        "accuracy",
        "response_completeness",
        "response_length",
        "latency_p95"
    ],
    
    success_criteria={
        "accuracy": {"min_improvement": 0.02, "max_regression": 0.01},
        "latency_p95": {"max_increase_ms": 500}
    },
    
    statistical_significance=0.95
)
```

---

## 7. Test Data Management

### 7.1 Golden Dataset Versioning

```
tests/
├── data/
│   ├── golden_dataset_v1.0.0.json    # Initial release
│   ├── golden_dataset_v1.1.0.json    # Added pest cases
│   ├── golden_dataset_v1.2.0.json    # Current
│   └── golden_dataset_latest.json    # Symlink to current
├── baselines/
│   ├── v1.0.0/
│   │   └── results.json
│   ├── v1.1.0/
│   │   └── results.json
│   └── v1.2.0/
│       └── results.json
└── fixtures/
    ├── synthetic_users.json
    ├── synthetic_farms.json
    └── weather_scenarios.json
```

### 7.2 Expert Validation Workflow

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
sequenceDiagram
    participant D as 👨‍💻 Developer
    participant S as 📝 Staging Dataset
    participant A as 👨‍🌾 Agronomist
    participant G as ✅ Golden Dataset
    
    D->>S: Add new test cases
    S->>A: Request validation
    A->>A: Review expected answers
    A->>A: Verify rule triggers
    alt Approved
        A->>G: Merge to golden dataset
        G->>G: Increment version
    else Needs Revision
        A->>D: Return with feedback
        D->>S: Revise test case
    end
```

---

## 8. Quality Gates

### 8.1 PR Merge Requirements

| Gate | Requirement | Enforcement |
|:-----|:------------|:------------|
| ✅ Unit Tests | 100% pass | GitHub Actions |
| ✅ Integration Tests | 100% pass | GitHub Actions |
| ✅ Safety Tests | 100% pass | GitHub Actions |
| ✅ Code Coverage | ≥ 80% | Codecov |
| ✅ No New Warnings | Linting clean | Pre-commit |

### 8.2 Release Requirements

| Gate | Requirement | Enforcement |
|:-----|:------------|:------------|
| ✅ All PR Gates | Pass | GitHub Actions |
| ✅ Evaluation Accuracy | ≥ 90% overall | Evaluation pipeline |
| ✅ No Regressions | Vs. previous release | Regression tests |
| ✅ Load Test | P95 latency < 3s | k6 load test |
| ✅ Security Scan | No critical CVEs | Trivy/Snyk |

---

## 9. Reporting & Dashboards

### 9.1 Evaluation Report Format

```json
{
  "report_id": "eval-2026-01-17-001",
  "timestamp": "2026-01-17T14:30:00Z",
  "model_version": "qwen3-4b-q4_k_m",
  "prompt_version": "v1.2.0",
  "dataset_version": "v1.2.0",
  
  "summary": {
    "total_cases": 170,
    "passing": 158,
    "failing": 12,
    "accuracy": 0.929,
    "meets_threshold": true
  },
  
  "by_category": {
    "irrigation": {"total": 25, "passing": 24, "accuracy": 0.96},
    "fertilization": {"total": 20, "passing": 19, "accuracy": 0.95},
    "pest_control": {"total": 25, "passing": 22, "accuracy": 0.88},
    "...": "..."
  },
  
  "failures": [
    {
      "case_id": "TC-PST-012",
      "category": "pest_control",
      "reason": "Missing expected concept: consult_agronomist",
      "expected": ["fungicide", "remove_infected", "consult_agronomist"],
      "actual": ["fungicide", "remove_infected"]
    }
  ],
  
  "metrics": {
    "avg_response_time_ms": 1250,
    "p95_response_time_ms": 2100,
    "avg_token_count": 285,
    "hallucination_count": 0
  }
}
```

### 9.2 Dashboard Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                    📊 YONCA AI QUALITY DASHBOARD                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Overall Accuracy        Category Breakdown          Trend      │
│  ┌─────────────┐        ┌────────────────────┐      ┌────────┐ │
│  │             │        │ Irrigation    96%  │      │   ↗    │ │
│  │    92.9%    │        │ Fertilization 95%  │      │  ───   │ │
│  │   ✅ PASS   │        │ Pest Control  88%  │      │        │ │
│  │             │        │ Harvest       93%  │      │ 7 days │ │
│  └─────────────┘        └────────────────────┘      └────────┘ │
│                                                                 │
│  Safety Metrics          Response Quality           Latency     │
│  ┌────────────────┐     ┌────────────────────┐     ┌─────────┐ │
│  │ Hallucinations │     │ Completeness  91%  │     │ P50 1.2s│ │
│  │      0 🟢      │     │ Relevance     89%  │     │ P95 2.1s│ │
│  │ PII Leaks      │     │ Conciseness   94%  │     │ P99 3.5s│ │
│  │      0 🟢      │     │                    │     │         │ │
│  └────────────────┘     └────────────────────┘     └─────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

<div align="center">

**📄 Document:** `04-TESTING-STRATEGY.md`  
**⬅️ Previous:** [03-ARCHITECTURE.md](03-ARCHITECTURE.md) — Technical Architecture  
**➡️ Next:** [05-PROMPT-ENGINEERING.md](05-PROMPT-ENGINEERING.md) — Prompt Design & Versioning

</div>
