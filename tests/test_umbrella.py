"""
Yonca AI - Digital Umbrella Test Suite
======================================

Tests for the Digital Umbrella prototype modules.
"""
import pytest
from datetime import date, timedelta

from yonca.umbrella.scenario_manager import (
    ScenarioManager,
    ScenarioProfile,
    SCENARIO_LABELS,
)
from yonca.umbrella.mock_backend import (
    MockBackend,
    FarmProfileRequest,
    RecommendationPriority,
    RecommendationType,
)
from yonca.umbrella.agronomy_rules import AgronomyLogicGuard


class TestScenarioManager:
    """Tests for ScenarioManager class."""
    
    def test_initialization(self):
        """Test ScenarioManager initializes with all 5 profiles."""
        manager = ScenarioManager()
        profiles = manager.list_profiles()
        
        assert len(profiles) == 5
        assert ScenarioProfile.WHEAT in [p["profile"] for p in profiles]
        assert ScenarioProfile.LIVESTOCK in [p["profile"] for p in profiles]
        assert ScenarioProfile.ORCHARD in [p["profile"] for p in profiles]
        assert ScenarioProfile.MIXED in [p["profile"] for p in profiles]
        assert ScenarioProfile.POULTRY in [p["profile"] for p in profiles]
    
    def test_switch_profile(self):
        """Test switching between farm profiles."""
        manager = ScenarioManager()
        
        # Default is WHEAT
        assert manager.current_profile == ScenarioProfile.WHEAT
        
        # Switch to LIVESTOCK
        farm = manager.switch_profile(ScenarioProfile.LIVESTOCK)
        assert manager.current_profile == ScenarioProfile.LIVESTOCK
        assert farm.profile_type == ScenarioProfile.LIVESTOCK
        assert farm.name == "Qazax Heyvandarlıq Ferması"
    
    def test_wheat_scenario_data(self):
        """Test wheat scenario has specific low moisture data."""
        manager = ScenarioManager()
        farm = manager.get_farm(ScenarioProfile.WHEAT)
        
        assert farm.soil is not None
        assert farm.soil.moisture_percent == 12  # Critical low
        assert farm.soil.nitrogen_kg_ha == 22.0  # Low nitrogen
        assert farm.satellite_alert is not None
        assert "sarılma" in farm.satellite_alert.lower()  # Yellowing detected
    
    def test_livestock_scenario_data(self):
        """Test livestock scenario has heat stress conditions."""
        manager = ScenarioManager()
        farm = manager.get_farm(ScenarioProfile.LIVESTOCK)
        
        assert farm.weather is not None
        assert farm.weather.humidity_percent >= 70  # High humidity
        assert farm.weather.temperature_max >= 32  # High temperature
        assert len(farm.livestock) > 0
    
    def test_all_farms_have_ids(self):
        """Test all farm profiles have unique IDs."""
        manager = ScenarioManager()
        profiles = manager.list_profiles()
        
        ids = [p["farm"].id for p in profiles]
        assert len(ids) == len(set(ids))  # All unique
        
        for farm_id in ids:
            assert farm_id.startswith("scenario-")
    
    def test_profile_labels_in_azerbaijani(self):
        """Test all profiles have Azerbaijani labels."""
        for profile in ScenarioProfile:
            label = SCENARIO_LABELS[profile]
            
            assert "name" in label
            assert "description" in label
            assert "icon" in label
            assert "region" in label
            
            # Check name is Azerbaijani (contains special chars)
            assert any(c in label["name"] for c in "ıəöüğşçİƏÖÜĞŞÇ") or \
                   label["name"].isascii()  # Some names may be Latin


class TestMockBackend:
    """Tests for MockBackend class."""
    
    def test_recommend_returns_payload(self):
        """Test recommend returns a valid payload."""
        backend = MockBackend()
        
        request = FarmProfileRequest(
            farm_id="test-farm",
            farm_type="wheat",
            region="Aran",
            area_hectares=50.0,
            soil_moisture_percent=15,
            soil_nitrogen=20.0,
        )
        
        payload = backend.recommend(request)
        
        assert payload.request_id.startswith("req-")
        assert payload.farm_id == "test-farm"
        assert payload.status == "success"
        assert payload.inference_engine == "qwen2.5-7b-simulated"
        assert len(payload.recommendations) > 0
    
    def test_wheat_recommendations_for_low_moisture(self):
        """Test wheat farm with low moisture gets irrigation rec."""
        backend = MockBackend()
        
        request = FarmProfileRequest(
            farm_id="wheat-farm",
            farm_type="wheat",
            region="Aran",
            area_hectares=85.0,
            soil_moisture_percent=12,  # Critical low
            soil_nitrogen=22.0,        # Low
        )
        
        payload = backend.recommend(request)
        
        # Should have critical irrigation recommendation
        irrigation_recs = [
            r for r in payload.recommendations 
            if r.type == RecommendationType.IRRIGATION
        ]
        
        assert len(irrigation_recs) > 0
        assert irrigation_recs[0].priority == RecommendationPriority.CRITICAL
        assert "suvarma" in irrigation_recs[0].title.lower() or \
               "suvarma" in irrigation_recs[0].description.lower()
    
    def test_livestock_recommendations_for_heat_stress(self):
        """Test livestock farm with high humidity gets ventilation rec."""
        backend = MockBackend()
        
        request = FarmProfileRequest(
            farm_id="livestock-farm",
            farm_type="livestock",
            region="Gəncə-Qazax",
            area_hectares=45.0,
            temperature_max=36.0,
            humidity_percent=78,
            barn_humidity=80,
            livestock_types=["mal-qara", "qoyun"],
            livestock_counts=[35, 120],
        )
        
        payload = backend.recommend(request)
        
        # Should have ventilation recommendation
        vent_recs = [
            r for r in payload.recommendations 
            if r.type == RecommendationType.VENTILATION
        ]
        
        assert len(vent_recs) > 0
        assert "ventilyasiya" in vent_recs[0].title.lower() or \
               "ventilyasiya" in vent_recs[0].description.lower()
    
    def test_daily_routine_generated(self):
        """Test daily routine is generated for each farm type."""
        backend = MockBackend()
        
        for farm_type in ["wheat", "livestock", "poultry"]:
            request = FarmProfileRequest(
                farm_id=f"test-{farm_type}",
                farm_type=farm_type,
                region="Test",
                area_hectares=50.0,
            )
            
            payload = backend.recommend(request)
            
            assert len(payload.daily_routine) > 0
            
            # Check routine has required fields
            for item in payload.daily_routine:
                assert item.time_slot is not None
                assert item.title is not None
                assert item.icon is not None
                assert item.duration_minutes > 0
    
    def test_health_endpoint(self):
        """Test health endpoint returns status."""
        backend = MockBackend()
        health = backend.get_health()
        
        assert health["status"] == "healthy"
        assert health["inference_engine"] == "qwen2.5-7b-simulated"


class TestAgronomyLogicGuard:
    """Tests for AgronomyLogicGuard class."""
    
    def test_blocks_irrigation_during_rain(self):
        """Test logic guard blocks irrigation when rain expected."""
        guard = AgronomyLogicGuard()
        backend = MockBackend(logic_guard=guard)
        
        # Request with rain expected
        request = FarmProfileRequest(
            farm_id="test-farm",
            farm_type="wheat",
            region="Aran",
            area_hectares=50.0,
            soil_moisture_percent=15,  # Would trigger irrigation
            is_rain_expected=True,     # But rain is coming
        )
        
        payload = backend.recommend(request)
        
        # Irrigation should be blocked or have no critical irrigation
        irrigation_recs = [
            r for r in payload.recommendations 
            if r.type == RecommendationType.IRRIGATION and
            r.priority == RecommendationPriority.CRITICAL
        ]
        
        # Should have no critical irrigation due to rain
        assert len(irrigation_recs) == 0
    
    def test_blocks_irrigation_high_moisture(self):
        """Test logic guard blocks irrigation when soil moisture high."""
        guard = AgronomyLogicGuard()
        backend = MockBackend(logic_guard=guard)
        
        request = FarmProfileRequest(
            farm_id="test-farm",
            farm_type="wheat",
            region="Aran",
            area_hectares=50.0,
            soil_moisture_percent=75,  # Already high
        )
        
        payload = backend.recommend(request)
        
        # Irrigation should be blocked
        irrigation_recs = [
            r for r in payload.recommendations 
            if r.type == RecommendationType.IRRIGATION
        ]
        
        # Should have no irrigation recommendations
        assert len(irrigation_recs) == 0
    
    def test_modifies_vaccination_in_heat(self):
        """Test logic guard modifies vaccination during extreme heat."""
        guard = AgronomyLogicGuard()
        
        # Create a vaccination recommendation directly
        from yonca.umbrella.mock_backend import RecommendationItem
        from uuid import uuid4
        
        rec = RecommendationItem(
            id=f"rec-{uuid4().hex[:8]}",
            type=RecommendationType.VACCINATION,
            priority=RecommendationPriority.MEDIUM,
            confidence=0.8,
            title="Test Peyvənd",
            description="Test",
            action="Peyvənd edin",
            why_title="Test",
            why_explanation="Test",
        )
        
        # High temperature request
        request = FarmProfileRequest(
            farm_id="test",
            farm_type="livestock",
            region="Test",
            area_hectares=50.0,
            temperature_max=38.0,  # Extreme heat
        )
        
        validated = guard.validate_recommendations([rec], request)
        
        # Should be modified or blocked
        # (vaccination timing should be adjusted)
        if len(validated) > 0:
            # If returned, should be modified
            assert validated[0].source == "hybrid-modified" or \
                   "gözləyin" in validated[0].action.lower()
    
    def test_statistics_tracking(self):
        """Test logic guard tracks statistics."""
        guard = AgronomyLogicGuard()
        
        stats = guard.get_statistics()
        
        assert "total_validations" in stats
        assert "total_overrides" in stats
        assert "rules_count" in stats
        assert stats["rules_count"] > 0
    
    def test_rules_summary(self):
        """Test rules summary provides useful info."""
        guard = AgronomyLogicGuard()
        
        summary = guard.get_rules_summary()
        
        assert len(summary) > 0
        
        for rule in summary:
            assert "rule_id" in rule
            assert "name" in rule
            assert "name_az" in rule
            assert rule["rule_id"].startswith("AG-")


class TestIntegration:
    """Integration tests for the full umbrella system."""
    
    def test_full_wheat_workflow(self):
        """Test complete workflow for wheat scenario."""
        # Initialize components
        manager = ScenarioManager()
        guard = AgronomyLogicGuard()
        backend = MockBackend(logic_guard=guard)
        
        # Get wheat farm
        manager.switch_profile(ScenarioProfile.WHEAT)
        farm = manager.current_farm
        
        # Build request from farm data
        request = FarmProfileRequest(
            farm_id=farm.id,
            farm_type=farm.profile_type.value,
            region=farm.region,
            area_hectares=farm.area_hectares,
            soil_moisture_percent=farm.soil.moisture_percent if farm.soil else None,
            soil_nitrogen=farm.soil.nitrogen_kg_ha if farm.soil else None,
            temperature_max=farm.weather.temperature_max if farm.weather else None,
            humidity_percent=farm.weather.humidity_percent if farm.weather else None,
            crops=[c.crop_type for c in farm.crops],
            crop_stages=[c.growth_stage for c in farm.crops],
        )
        
        # Get recommendations
        payload = backend.recommend(request)
        
        # Verify response
        assert payload.status == "success"
        assert payload.total_count > 0
        
        # Wheat with low moisture should have critical recommendations
        assert payload.critical_count > 0
        
        # Should have daily routine
        assert len(payload.daily_routine) > 0
    
    def test_full_livestock_workflow(self):
        """Test complete workflow for livestock scenario."""
        manager = ScenarioManager()
        guard = AgronomyLogicGuard()
        backend = MockBackend(logic_guard=guard)
        
        # Get livestock farm
        manager.switch_profile(ScenarioProfile.LIVESTOCK)
        farm = manager.current_farm
        
        request = FarmProfileRequest(
            farm_id=farm.id,
            farm_type=farm.profile_type.value,
            region=farm.region,
            area_hectares=farm.area_hectares,
            temperature_max=farm.weather.temperature_max if farm.weather else None,
            humidity_percent=farm.weather.humidity_percent if farm.weather else None,
            barn_humidity=farm.weather.humidity_percent if farm.weather else None,
            livestock_types=[l.animal_type for l in farm.livestock],
            livestock_counts=[l.count for l in farm.livestock],
        )
        
        payload = backend.recommend(request)
        
        assert payload.status == "success"
        
        # Should have ventilation or livestock care recommendations
        types = [r.type for r in payload.recommendations]
        assert RecommendationType.VENTILATION in types or \
               RecommendationType.LIVESTOCK_CARE in types
    
    def test_all_profiles_generate_recommendations(self):
        """Test all 5 profiles generate valid recommendations."""
        manager = ScenarioManager()
        backend = MockBackend()
        
        for profile in ScenarioProfile:
            manager.switch_profile(profile)
            farm = manager.current_farm
            
            request = FarmProfileRequest(
                farm_id=farm.id,
                farm_type=farm.profile_type.value,
                region=farm.region,
                area_hectares=farm.area_hectares,
                soil_moisture_percent=farm.soil.moisture_percent if farm.soil else None,
                temperature_max=farm.weather.temperature_max if farm.weather else None,
                humidity_percent=farm.weather.humidity_percent if farm.weather else None,
            )
            
            payload = backend.recommend(request)
            
            assert payload.status == "success", f"Failed for {profile.value}"
            assert len(payload.recommendations) > 0, f"No recs for {profile.value}"
            assert len(payload.daily_routine) > 0, f"No routine for {profile.value}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
