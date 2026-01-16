"""
Yonca AI - Digital Twin Simulation Engine
=========================================

Strategic rebranding: "Dummy Data" → "Digital Twin Scenarios"

This module provides simulation capabilities for:
- Pre-deployment scenario testing
- "What-if" analysis for farmers
- Future outcome predictions
- Risk assessment modeling

A Digital Twin is a virtual replica of a farm that can be used to
simulate conditions without affecting real operations.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class SimulationMode(str, Enum):
    """Types of simulation scenarios."""
    BASELINE = "baseline"           # Normal conditions
    DROUGHT_STRESS = "drought"      # Water scarcity scenario
    PEST_OUTBREAK = "pest"          # Pest infestation scenario
    MARKET_SHIFT = "market"         # Price/demand changes
    CLIMATE_EXTREME = "climate"     # Extreme weather events
    OPTIMAL = "optimal"             # Best-case conditions
    WORST_CASE = "worst_case"       # Risk assessment


class CropType(str, Enum):
    """Crop types for simulation."""
    WHEAT = "buğda"
    COTTON = "pambıq"
    GRAPE = "üzüm"
    TOMATO = "pomidor"
    POMEGRANATE = "nar"
    HAZELNUT = "fındıq"


@dataclass
class SimulationParameters:
    """Parameters for a simulation run."""
    mode: SimulationMode
    crop_type: CropType
    field_size_hectares: float
    region: str
    start_date: datetime
    duration_days: int = 180
    initial_soil_moisture: float = 0.6  # 0-1 scale
    initial_soil_ph: float = 6.5
    irrigation_available: bool = True
    fertilizer_budget_azn: float = 500.0
    labor_hours_per_week: float = 40.0
    custom_parameters: dict = field(default_factory=dict)


@dataclass
class SimulationOutcome:
    """Results from a simulation run."""
    simulation_id: str
    parameters: SimulationParameters
    
    # Yield predictions
    predicted_yield_kg_per_hectare: float
    yield_confidence_interval: tuple[float, float]
    yield_vs_regional_average: float  # percentage
    
    # Economic projections
    estimated_revenue_azn: float
    estimated_costs_azn: float
    estimated_profit_azn: float
    roi_percentage: float
    
    # Risk factors
    risk_score: float  # 0-1, higher = more risk
    identified_risks: list[str] = field(default_factory=list)
    mitigation_suggestions: list[str] = field(default_factory=list)
    
    # Timeline events
    timeline_events: list[dict] = field(default_factory=list)
    
    # Resource projections
    water_needed_cubic_meters: float = 0.0
    fertilizer_needed_kg: float = 0.0
    labor_hours_total: float = 0.0
    
    def get_summary_az(self) -> str:
        """Get Azerbaijani summary of simulation."""
        lines = [
            f"🌱 Rəqəmsal Əkiz Simulyasiya Nəticələri",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📍 Bölgə: {self.parameters.region}",
            f"🌾 Bitki: {self.parameters.crop_type.value}",
            f"📐 Sahə: {self.parameters.field_size_hectares} hektar",
            f"📅 Müddət: {self.parameters.duration_days} gün",
            f"",
            f"📊 Məhsul Proqnozu:",
            f"  • Gözlənilən məhsul: {self.predicted_yield_kg_per_hectare:.0f} kq/ha",
            f"  • Etibarlılıq aralığı: {self.yield_confidence_interval[0]:.0f}-{self.yield_confidence_interval[1]:.0f} kq/ha",
            f"  • Bölgə ortalaması ilə: {self.yield_vs_regional_average:+.1f}%",
            f"",
            f"💰 Maliyyə Proqnozu:",
            f"  • Gözlənilən gəlir: {self.estimated_revenue_azn:,.0f} AZN",
            f"  • Xərclər: {self.estimated_costs_azn:,.0f} AZN",
            f"  • Mənfəət: {self.estimated_profit_azn:,.0f} AZN",
            f"  • ROI: {self.roi_percentage:.1f}%",
            f"",
            f"⚠️ Risk Qiymətləndirməsi: {self._risk_label()}",
        ]
        
        if self.identified_risks:
            lines.append(f"\n🚨 Müəyyən edilən risklər:")
            for risk in self.identified_risks[:3]:
                lines.append(f"  • {risk}")
        
        if self.mitigation_suggestions:
            lines.append(f"\n💡 Tövsiyələr:")
            for suggestion in self.mitigation_suggestions[:3]:
                lines.append(f"  • {suggestion}")
        
        return "\n".join(lines)
    
    def _risk_label(self) -> str:
        """Get risk label with emoji."""
        if self.risk_score < 0.3:
            return f"🟢 Aşağı ({self.risk_score:.0%})"
        elif self.risk_score < 0.6:
            return f"🟡 Orta ({self.risk_score:.0%})"
        elif self.risk_score < 0.8:
            return f"🟠 Yüksək ({self.risk_score:.0%})"
        else:
            return f"🔴 Kritik ({self.risk_score:.0%})"


@dataclass
class ScenarioComparison:
    """Comparison between multiple simulation scenarios."""
    scenarios: list[SimulationOutcome]
    baseline_index: int = 0
    
    def get_comparison_table(self, language: str = "az") -> str:
        """Generate comparison table."""
        if not self.scenarios:
            return "Müqayisə üçün ssenari yoxdur."
        
        lines = []
        if language == "az":
            lines.append("📊 Ssenari Müqayisəsi")
            lines.append("━" * 60)
            lines.append(f"{'Ssenari':<15} {'Məhsul':<12} {'Mənfəət':<12} {'Risk':<10}")
            lines.append("─" * 60)
        else:
            lines.append("📊 Scenario Comparison")
            lines.append("━" * 60)
            lines.append(f"{'Scenario':<15} {'Yield':<12} {'Profit':<12} {'Risk':<10}")
            lines.append("─" * 60)
        
        for i, scenario in enumerate(self.scenarios):
            mode_name = scenario.parameters.mode.value[:12]
            yield_str = f"{scenario.predicted_yield_kg_per_hectare:.0f} kq/ha"
            profit_str = f"{scenario.estimated_profit_azn:,.0f} AZN"
            risk_str = f"{scenario.risk_score:.0%}"
            
            marker = " ◄" if i == self.baseline_index else ""
            lines.append(f"{mode_name:<15} {yield_str:<12} {profit_str:<12} {risk_str:<10}{marker}")
        
        return "\n".join(lines)


# Regional yield averages (kg per hectare) - synthetic data
REGIONAL_YIELD_AVERAGES = {
    CropType.WHEAT: {
        "Aran": 3500,
        "Şəki-Zaqatala": 3200,
        "Lənkəran": 2800,
        "default": 3000,
    },
    CropType.COTTON: {
        "Aran": 2800,
        "Mil-Muğan": 3000,
        "default": 2500,
    },
    CropType.GRAPE: {
        "Şəki-Zaqatala": 8000,
        "Aran": 7500,
        "default": 7000,
    },
    CropType.TOMATO: {
        "Lənkəran": 45000,
        "Aran": 40000,
        "default": 35000,
    },
    CropType.POMEGRANATE: {
        "Göyçay": 12000,
        "Aran": 10000,
        "default": 9000,
    },
    CropType.HAZELNUT: {
        "Quba-Xaçmaz": 2000,
        "Şəki-Zaqatala": 1800,
        "default": 1500,
    },
}

# Market prices (AZN per kg) - synthetic data
MARKET_PRICES = {
    CropType.WHEAT: 0.45,
    CropType.COTTON: 1.20,
    CropType.GRAPE: 1.50,
    CropType.TOMATO: 0.80,
    CropType.POMEGRANATE: 2.50,
    CropType.HAZELNUT: 8.00,
}

# Cost factors (AZN per hectare)
COST_FACTORS = {
    CropType.WHEAT: {"seed": 150, "fertilizer": 200, "labor": 300, "irrigation": 100},
    CropType.COTTON: {"seed": 100, "fertilizer": 250, "labor": 500, "irrigation": 200},
    CropType.GRAPE: {"seed": 0, "fertilizer": 300, "labor": 800, "irrigation": 150},
    CropType.TOMATO: {"seed": 200, "fertilizer": 400, "labor": 1000, "irrigation": 300},
    CropType.POMEGRANATE: {"seed": 0, "fertilizer": 250, "labor": 600, "irrigation": 150},
    CropType.HAZELNUT: {"seed": 0, "fertilizer": 200, "labor": 400, "irrigation": 100},
}


class DigitalTwinSimulator:
    """
    Digital Twin Simulation Engine.
    
    Simulates farm outcomes under different conditions using
    Azerbaijani agricultural parameters and synthetic data.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize simulator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        
        self._simulation_counter = 0
    
    def _generate_simulation_id(self) -> str:
        """Generate unique simulation ID."""
        self._simulation_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"SIM-{timestamp}-{self._simulation_counter:04d}"
    
    def run_simulation(
        self,
        parameters: SimulationParameters
    ) -> SimulationOutcome:
        """
        Run a single simulation scenario.
        
        Args:
            parameters: Simulation parameters
            
        Returns:
            SimulationOutcome with predictions
        """
        sim_id = self._generate_simulation_id()
        
        # Get baseline yield for region
        baseline_yield = self._get_baseline_yield(
            parameters.crop_type,
            parameters.region
        )
        
        # Apply mode modifiers
        yield_modifier, risk_modifier = self._get_mode_modifiers(parameters.mode)
        
        # Apply environmental factors
        env_modifier = self._calculate_environmental_modifier(parameters)
        
        # Calculate predicted yield
        predicted_yield = baseline_yield * yield_modifier * env_modifier
        
        # Add stochastic variation
        variation = random.gauss(1.0, 0.1)  # ±10% variation
        predicted_yield *= max(0.5, min(1.5, variation))
        
        # Calculate confidence interval
        ci_low = predicted_yield * 0.85
        ci_high = predicted_yield * 1.15
        
        # Calculate vs regional average
        regional_avg = REGIONAL_YIELD_AVERAGES.get(
            parameters.crop_type, {}
        ).get("default", baseline_yield)
        yield_vs_avg = ((predicted_yield - regional_avg) / regional_avg) * 100
        
        # Calculate economics
        revenue, costs, profit, roi = self._calculate_economics(
            parameters, predicted_yield
        )
        
        # Calculate risk
        risk_score = self._calculate_risk_score(parameters, yield_modifier)
        risks, mitigations = self._identify_risks(parameters, risk_score)
        
        # Generate timeline
        timeline = self._generate_timeline(parameters)
        
        # Resource projections
        water = self._estimate_water_needs(parameters)
        fertilizer = self._estimate_fertilizer_needs(parameters)
        labor = parameters.labor_hours_per_week * (parameters.duration_days / 7)
        
        return SimulationOutcome(
            simulation_id=sim_id,
            parameters=parameters,
            predicted_yield_kg_per_hectare=predicted_yield,
            yield_confidence_interval=(ci_low, ci_high),
            yield_vs_regional_average=yield_vs_avg,
            estimated_revenue_azn=revenue,
            estimated_costs_azn=costs,
            estimated_profit_azn=profit,
            roi_percentage=roi,
            risk_score=risk_score,
            identified_risks=risks,
            mitigation_suggestions=mitigations,
            timeline_events=timeline,
            water_needed_cubic_meters=water,
            fertilizer_needed_kg=fertilizer,
            labor_hours_total=labor,
        )
    
    def _get_baseline_yield(self, crop: CropType, region: str) -> float:
        """Get baseline yield for crop and region."""
        crop_yields = REGIONAL_YIELD_AVERAGES.get(crop, {})
        return crop_yields.get(region, crop_yields.get("default", 3000))
    
    def _get_mode_modifiers(
        self,
        mode: SimulationMode
    ) -> tuple[float, float]:
        """
        Get yield and risk modifiers for simulation mode.
        
        Returns:
            Tuple of (yield_modifier, risk_modifier)
        """
        modifiers = {
            SimulationMode.BASELINE: (1.0, 0.3),
            SimulationMode.OPTIMAL: (1.25, 0.15),
            SimulationMode.DROUGHT_STRESS: (0.65, 0.7),
            SimulationMode.PEST_OUTBREAK: (0.70, 0.65),
            SimulationMode.MARKET_SHIFT: (1.0, 0.5),
            SimulationMode.CLIMATE_EXTREME: (0.55, 0.85),
            SimulationMode.WORST_CASE: (0.40, 0.95),
        }
        return modifiers.get(mode, (1.0, 0.3))
    
    def _calculate_environmental_modifier(
        self,
        params: SimulationParameters
    ) -> float:
        """Calculate yield modifier from environmental factors."""
        modifier = 1.0
        
        # Soil moisture impact
        if params.initial_soil_moisture < 0.3:
            modifier *= 0.8
        elif params.initial_soil_moisture > 0.8:
            modifier *= 0.9  # Too wet
        
        # Soil pH impact (optimal around 6.0-7.0)
        ph_deviation = abs(params.initial_soil_ph - 6.5)
        if ph_deviation > 1.5:
            modifier *= 0.85
        elif ph_deviation > 0.5:
            modifier *= 0.95
        
        # Irrigation availability
        if not params.irrigation_available:
            modifier *= 0.7
        
        return modifier
    
    def _calculate_economics(
        self,
        params: SimulationParameters,
        yield_kg_ha: float
    ) -> tuple[float, float, float, float]:
        """
        Calculate economic projections.
        
        Returns:
            Tuple of (revenue, costs, profit, roi)
        """
        # Revenue
        price_per_kg = MARKET_PRICES.get(params.crop_type, 1.0)
        total_yield = yield_kg_ha * params.field_size_hectares
        revenue = total_yield * price_per_kg
        
        # Apply market shift if applicable
        if params.mode == SimulationMode.MARKET_SHIFT:
            revenue *= random.uniform(0.7, 1.3)
        
        # Costs
        cost_factors = COST_FACTORS.get(params.crop_type, {
            "seed": 150, "fertilizer": 200, "labor": 400, "irrigation": 150
        })
        
        base_costs = sum(cost_factors.values()) * params.field_size_hectares
        
        # Add duration-based costs
        duration_factor = params.duration_days / 180  # Normalized to 6 months
        costs = base_costs * duration_factor
        
        # Fertilizer budget constraint
        costs = max(costs, params.fertilizer_budget_azn)
        
        # Profit & ROI
        profit = revenue - costs
        roi = (profit / costs * 100) if costs > 0 else 0
        
        return revenue, costs, profit, roi
    
    def _calculate_risk_score(
        self,
        params: SimulationParameters,
        yield_modifier: float
    ) -> float:
        """Calculate overall risk score."""
        base_risk = 0.3
        
        # Mode-based risk
        _, mode_risk = self._get_mode_modifiers(params.mode)
        base_risk = max(base_risk, mode_risk)
        
        # Environmental risks
        if params.initial_soil_moisture < 0.4:
            base_risk += 0.1
        if not params.irrigation_available:
            base_risk += 0.15
        
        # Duration risk (longer = more uncertainty)
        if params.duration_days > 180:
            base_risk += 0.05
        
        return min(1.0, base_risk)
    
    def _identify_risks(
        self,
        params: SimulationParameters,
        risk_score: float
    ) -> tuple[list[str], list[str]]:
        """Identify specific risks and mitigations."""
        risks = []
        mitigations = []
        
        if params.mode == SimulationMode.DROUGHT_STRESS:
            risks.append("Quraqlıq stresi gözlənilir")
            mitigations.append("Damcı suvarma sisteminə keçin")
            mitigations.append("Quraqlığa davamlı sortları seçin")
        
        if params.mode == SimulationMode.PEST_OUTBREAK:
            risks.append("Zərərverici yayılması riski yüksəkdir")
            mitigations.append("Profilaktik pestisid tətbiq edin")
            mitigations.append("Həşərat tələləri qurun")
        
        if params.mode == SimulationMode.CLIMATE_EXTREME:
            risks.append("Ekstremal hava hadisələri gözlənilir")
            mitigations.append("İstixana və ya örtük istifadə edin")
            mitigations.append("Sığorta al")
        
        if not params.irrigation_available:
            risks.append("Su təchizatı məhdudiyyəti")
            mitigations.append("Yağış suyu toplama sistemi qurun")
        
        if params.initial_soil_moisture < 0.3:
            risks.append("Torpaq nəmliyi kritik səviyyədə")
            mitigations.append("Dərhal suvarma planlaşdırın")
        
        if risk_score > 0.7:
            risks.append("Ümumi risk səviyyəsi yüksəkdir")
            mitigations.append("Riskləri azaltmaq üçün mütəxəssislə məsləhətləşin")
        
        return risks, mitigations
    
    def _generate_timeline(
        self,
        params: SimulationParameters
    ) -> list[dict]:
        """Generate timeline of expected events."""
        timeline = []
        current_date = params.start_date
        
        # Planting/Start
        timeline.append({
            "date": current_date.isoformat(),
            "event": "Başlanğıc",
            "event_en": "Start",
            "type": "milestone",
        })
        
        # First irrigation
        timeline.append({
            "date": (current_date + timedelta(days=7)).isoformat(),
            "event": "İlk suvarma",
            "event_en": "First irrigation",
            "type": "action",
        })
        
        # First fertilization
        timeline.append({
            "date": (current_date + timedelta(days=14)).isoformat(),
            "event": "İlk gübrələmə",
            "event_en": "First fertilization",
            "type": "action",
        })
        
        # Midpoint check
        midpoint = current_date + timedelta(days=params.duration_days // 2)
        timeline.append({
            "date": midpoint.isoformat(),
            "event": "Orta dövr qiymətləndirməsi",
            "event_en": "Midpoint assessment",
            "type": "milestone",
        })
        
        # Mode-specific events
        if params.mode == SimulationMode.PEST_OUTBREAK:
            timeline.append({
                "date": (current_date + timedelta(days=45)).isoformat(),
                "event": "⚠️ Zərərverici aşkarlanması",
                "event_en": "⚠️ Pest detection",
                "type": "alert",
            })
        
        if params.mode == SimulationMode.DROUGHT_STRESS:
            timeline.append({
                "date": (current_date + timedelta(days=60)).isoformat(),
                "event": "⚠️ Quraqlıq stresi başlayır",
                "event_en": "⚠️ Drought stress begins",
                "type": "alert",
            })
        
        # Harvest
        harvest_date = current_date + timedelta(days=params.duration_days)
        timeline.append({
            "date": harvest_date.isoformat(),
            "event": "🌾 Məhsul yığımı",
            "event_en": "🌾 Harvest",
            "type": "milestone",
        })
        
        return sorted(timeline, key=lambda x: x["date"])
    
    def _estimate_water_needs(self, params: SimulationParameters) -> float:
        """Estimate total water needs in cubic meters."""
        # Base water per hectare per day (simplified)
        water_per_ha_day = {
            CropType.WHEAT: 5,
            CropType.COTTON: 8,
            CropType.GRAPE: 6,
            CropType.TOMATO: 10,
            CropType.POMEGRANATE: 5,
            CropType.HAZELNUT: 4,
        }
        
        base_water = water_per_ha_day.get(params.crop_type, 6)
        total = base_water * params.field_size_hectares * params.duration_days
        
        # Adjust for drought scenario
        if params.mode == SimulationMode.DROUGHT_STRESS:
            total *= 1.3  # Need more to compensate
        
        return total
    
    def _estimate_fertilizer_needs(self, params: SimulationParameters) -> float:
        """Estimate total fertilizer needs in kg."""
        # Base fertilizer per hectare
        fert_per_ha = {
            CropType.WHEAT: 150,
            CropType.COTTON: 200,
            CropType.GRAPE: 180,
            CropType.TOMATO: 250,
            CropType.POMEGRANATE: 120,
            CropType.HAZELNUT: 100,
        }
        
        base_fert = fert_per_ha.get(params.crop_type, 150)
        return base_fert * params.field_size_hectares
    
    def compare_scenarios(
        self,
        base_params: SimulationParameters,
        modes: Optional[list[SimulationMode]] = None
    ) -> ScenarioComparison:
        """
        Run multiple scenarios and compare outcomes.
        
        Args:
            base_params: Base parameters to use
            modes: List of modes to compare (defaults to all)
            
        Returns:
            ScenarioComparison object
        """
        if modes is None:
            modes = [
                SimulationMode.BASELINE,
                SimulationMode.OPTIMAL,
                SimulationMode.DROUGHT_STRESS,
                SimulationMode.WORST_CASE,
            ]
        
        scenarios = []
        baseline_idx = 0
        
        for i, mode in enumerate(modes):
            # Create params copy with new mode
            scenario_params = SimulationParameters(
                mode=mode,
                crop_type=base_params.crop_type,
                field_size_hectares=base_params.field_size_hectares,
                region=base_params.region,
                start_date=base_params.start_date,
                duration_days=base_params.duration_days,
                initial_soil_moisture=base_params.initial_soil_moisture,
                initial_soil_ph=base_params.initial_soil_ph,
                irrigation_available=base_params.irrigation_available,
                fertilizer_budget_azn=base_params.fertilizer_budget_azn,
                labor_hours_per_week=base_params.labor_hours_per_week,
            )
            
            outcome = self.run_simulation(scenario_params)
            scenarios.append(outcome)
            
            if mode == SimulationMode.BASELINE:
                baseline_idx = i
        
        return ScenarioComparison(
            scenarios=scenarios,
            baseline_index=baseline_idx,
        )
