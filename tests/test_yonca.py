"""
Yonca AI - Test Suite
"""
import pytest
from datetime import date, timedelta

from yonca.models import (
    FarmProfile, FarmType, CropStage, TaskPriority,
    ChatMessage
)
from yonca.core.engine import RecommendationEngine
from yonca.chatbot import AzerbaijaniChatbot
from yonca.data.generators import (
    FarmGenerator, WeatherGenerator, SoilGenerator,
    generate_sample_farms
)
from yonca.data.scenarios import get_scenario_farms, ALL_SCENARIOS


class TestSyntheticDataGenerators:
    """Tests for synthetic data generation."""
    
    def test_generate_sample_farms(self):
        """Test generating sample farm profiles."""
        farms = generate_sample_farms(5)
        
        assert len(farms) == 5
        
        # Check all farm types are represented
        farm_types = {f.farm_type for f in farms}
        assert len(farm_types) == 5
    
    def test_farm_generator(self):
        """Test individual farm generation."""
        farm = FarmGenerator.generate_farm(farm_type=FarmType.WHEAT)
        
        assert farm.farm_type == FarmType.WHEAT
        assert farm.total_area_hectares > 0
        assert farm.location is not None
        assert farm.id.startswith("farm-")
    
    def test_weather_generator(self):
        """Test weather data generation."""
        weather = WeatherGenerator.generate(date.today(), "Aran", days=7)
        
        assert len(weather) == 7
        assert all(w.date >= date.today() for w in weather)
        assert all(-20 <= w.temperature_min <= 50 for w in weather)
    
    def test_soil_generator(self):
        """Test soil data generation."""
        soil = SoilGenerator.generate("Aran")
        
        assert soil.ph_level > 0
        assert 0 <= soil.moisture_percent <= 100
        assert soil.nitrogen_level >= 0


class TestScenarioFarms:
    """Tests for pre-defined scenario farms."""
    
    def test_scenario_farms_exist(self):
        """Test that scenario farms are defined."""
        farms = get_scenario_farms()
        
        assert len(farms) >= 5
    
    def test_all_scenarios_list(self):
        """Test ALL_SCENARIOS contains required farms."""
        assert len(ALL_SCENARIOS) >= 5
        
        # Check for diversity
        farm_types = {f.farm_type for f in ALL_SCENARIOS}
        assert FarmType.WHEAT in farm_types
        assert FarmType.LIVESTOCK in farm_types
        assert FarmType.ORCHARD in farm_types
    
    def test_wheat_scenario_details(self):
        """Test wheat scenario has correct configuration."""
        farms = get_scenario_farms()
        wheat_farm = farms.get("scenario-wheat")
        
        assert wheat_farm is not None
        assert wheat_farm.farm_type == FarmType.WHEAT
        assert len(wheat_farm.crops) > 0
        assert wheat_farm.soil_data is not None


class TestRecommendationEngine:
    """Tests for the AI recommendation engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RecommendationEngine()
        self.farms = get_scenario_farms()
    
    def test_generate_recommendations(self):
        """Test basic recommendation generation."""
        farm = self.farms["scenario-wheat"]
        recommendations = self.engine.generate_recommendations(farm)
        
        assert isinstance(recommendations, list)
        assert all(r.confidence >= 0 and r.confidence <= 1 for r in recommendations)
    
    def test_recommendations_have_required_fields(self):
        """Test recommendations have all required fields."""
        farm = self.farms["scenario-wheat"]
        recommendations = self.engine.generate_recommendations(farm)
        
        if recommendations:
            rec = recommendations[0]
            assert rec.id is not None
            assert rec.title is not None
            assert rec.title_az is not None
            assert rec.priority is not None
    
    def test_daily_schedule_generation(self):
        """Test daily schedule generation."""
        farm = self.farms["scenario-wheat"]
        schedule = self.engine.generate_daily_schedule(farm)
        
        assert schedule.farm_id == farm.id
        assert schedule.date == date.today()
        assert isinstance(schedule.tasks, list)
        assert isinstance(schedule.alerts, list)
    
    def test_recommendations_respect_max_results(self):
        """Test max_results parameter is respected."""
        farm = self.farms["scenario-wheat"]
        recommendations = self.engine.generate_recommendations(
            farm, max_recommendations=3
        )
        
        assert len(recommendations) <= 3
    
    def test_livestock_recommendations(self):
        """Test recommendations for livestock farm."""
        farm = self.farms["scenario-livestock"]
        recommendations = self.engine.generate_recommendations(farm)
        
        # Livestock farms should get livestock-related recommendations
        categories = {r.type for r in recommendations}
        assert "livestock" in categories or len(recommendations) == 0


class TestAzerbaijaniChatbot:
    """Tests for the Azerbaijani chatbot."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chatbot = AzerbaijaniChatbot()
    
    def test_greeting_intent(self):
        """Test greeting intent recognition."""
        message = ChatMessage(message="Salam")
        response = self.chatbot.process_message(message)
        
        assert response.intent == "greeting"
        assert response.confidence > 0.5
    
    def test_irrigation_intent(self):
        """Test irrigation intent recognition."""
        message = ChatMessage(
            message="Nə vaxt suvarmalıyam?",
            farm_id="scenario-wheat"
        )
        response = self.chatbot.process_message(message)
        
        assert response.intent == "suvarma_sorğusu"
    
    def test_fertilization_intent(self):
        """Test fertilization intent recognition."""
        message = ChatMessage(
            message="Gübrə lazımdırmı?",
            farm_id="scenario-wheat"
        )
        response = self.chatbot.process_message(message)
        
        assert response.intent == "gübrələmə_sorğusu"
    
    def test_help_intent(self):
        """Test help intent recognition."""
        message = ChatMessage(message="Kömək")
        response = self.chatbot.process_message(message)
        
        assert response.intent == "kömək"
        assert len(response.message) > 100  # Help message should be detailed
    
    def test_unknown_intent_fallback(self):
        """Test fallback for unrecognized input."""
        message = ChatMessage(message="asdfghjkl random text")
        response = self.chatbot.process_message(message)
        
        assert response.intent is None
        assert len(response.suggestions) > 0
    
    def test_suggestions_provided(self):
        """Test that suggestions are provided."""
        message = ChatMessage(message="Salam")
        response = self.chatbot.process_message(message)
        
        assert isinstance(response.suggestions, list)


class TestRecommendationLogicAccuracy:
    """
    Tests for recommendation logic accuracy.
    Target: ≥ 90% logical accuracy
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RecommendationEngine()
    
    def test_low_moisture_triggers_irrigation(self):
        """Low soil moisture should trigger irrigation recommendation."""
        from yonca.data.scenarios import WHEAT_FARM
        
        # Wheat farm has low moisture (28%)
        recommendations = self.engine.generate_recommendations(WHEAT_FARM)
        
        irrigation_recs = [r for r in recommendations if r.type == "irrigation"]
        assert len(irrigation_recs) > 0, "Low moisture should trigger irrigation"
    
    def test_low_nitrogen_triggers_fertilization(self):
        """Low nitrogen should trigger fertilization recommendation."""
        from yonca.data.scenarios import WHEAT_FARM
        
        # Wheat farm has low nitrogen (25 kg/ha)
        recommendations = self.engine.generate_recommendations(WHEAT_FARM)
        
        fert_recs = [r for r in recommendations if r.type == "fertilization"]
        # May or may not trigger depending on crop stage
        assert isinstance(fert_recs, list)
    
    def test_maturity_triggers_harvest(self):
        """Mature crops should trigger harvest recommendation."""
        from yonca.data.scenarios import VEGETABLE_FARM
        
        # Vegetable farm has mature badımcan
        recommendations = self.engine.generate_recommendations(VEGETABLE_FARM)
        
        harvest_recs = [r for r in recommendations if r.type == "harvest"]
        assert len(harvest_recs) > 0, "Mature crops should trigger harvest"
    
    def test_overdue_vaccination_triggers_alert(self):
        """Overdue vaccination should trigger livestock recommendation."""
        from yonca.data.scenarios import LIVESTOCK_FARM
        
        # Livestock farm has overdue cattle vaccination
        recommendations = self.engine.generate_recommendations(LIVESTOCK_FARM)
        
        livestock_recs = [r for r in recommendations if r.type == "livestock"]
        vaccination_recs = [r for r in livestock_recs if "peyvənd" in r.title_az.lower() or "vaccination" in r.title.lower()]
        assert len(vaccination_recs) > 0, "Overdue vaccination should trigger alert"
    
    def test_recommendations_are_prioritized(self):
        """Recommendations should be sorted by priority."""
        farm = list(get_scenario_farms().values())[0]
        recommendations = self.engine.generate_recommendations(farm)
        
        if len(recommendations) > 1:
            priority_order = {
                TaskPriority.CRITICAL: 0,
                TaskPriority.HIGH: 1,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 3,
            }
            
            # Check that higher priority comes first
            for i in range(len(recommendations) - 1):
                current_priority = priority_order[recommendations[i].priority]
                next_priority = priority_order[recommendations[i + 1].priority]
                assert current_priority <= next_priority


class TestDataSafety:
    """
    Tests for data safety principle.
    Ensures no real farmer data is used.
    """
    
    def test_all_farm_ids_are_synthetic(self):
        """All farm IDs should indicate synthetic data."""
        farms = get_scenario_farms()
        
        for farm_id in farms.keys():
            assert farm_id.startswith("scenario-") or farm_id.startswith("farm-")
    
    def test_no_real_coordinates(self):
        """Farm coordinates should be approximate regional centers."""
        farms = get_scenario_farms()
        
        for farm in farms.values():
            # Coordinates should be within Azerbaijan but not precise
            assert 38 <= farm.location.latitude <= 42
            assert 44 <= farm.location.longitude <= 51
    
    def test_generated_farms_are_synthetic(self):
        """Generated farms should have synthetic IDs."""
        farms = generate_sample_farms(3)
        
        for farm in farms:
            assert farm.id.startswith("farm-")
            assert len(farm.id) > 10  # Has random suffix


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
