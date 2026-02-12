"""
Tests unitarios para el sistema de Cords y Alquimias
"""
import pytest
from app.domain.models import DailyCorRecord, AlchemyCounter


class TestDailyCorRecordModel:
    """Tests para el modelo DailyCorRecord"""
    
    def test_daily_cor_record_creation(self):
        """Verifica que se puede crear un DailyCorRecord con los campos correctos"""
        record = DailyCorRecord(
            game_account_id=1,
            event_id=1,
            day_index=5,
            cords_count=100
        )
        
        assert record.game_account_id == 1
        assert record.event_id == 1
        assert record.day_index == 5
        assert record.cords_count == 100


class TestAlchemyCounterModel:
    """Tests para el modelo AlchemyCounter"""
    
    def test_alchemy_counter_creation(self):
        """Verifica que se puede crear un AlchemyCounter con los campos correctos"""
        counter = AlchemyCounter(
            event_id=1,
            alchemy_type='diamante',
            count=10
        )
        
        assert counter.event_id == 1
        assert counter.alchemy_type == 'diamante'
        assert counter.count == 10
    
    def test_alchemy_types_valid(self):
        """Verifica que los tipos de alquimia válidos funcionan"""
        valid_types = ['diamante', 'rubi', 'jade', 'zafiro', 'granate', 'onice']
        
        for alchemy_type in valid_types:
            counter = AlchemyCounter(
                event_id=1,
                alchemy_type=alchemy_type,
                count=5
            )
            assert counter.alchemy_type == alchemy_type


class TestAlchemyControllerImports:
    """Tests para verificar que los imports funcionan correctamente"""
    
    def test_controller_imports(self):
        """Verifica que el controlador se puede importar"""
        from app.application.services.alchemy_service import AlchemyService
        controller = AlchemyService()
        
        # Verificar que los nuevos métodos existen
        assert hasattr(controller, 'update_daily_cords')
        assert hasattr(controller, 'get_daily_cords')
        assert hasattr(controller, 'get_total_cords')
        assert hasattr(controller, 'get_event_cords_summary')
        assert hasattr(controller, 'get_alchemy_counters')
        assert hasattr(controller, 'update_alchemy_count')
        assert hasattr(controller, 'increment_alchemy')


class TestAlchemyViewImports:
    """Tests para verificar que las vistas se pueden importar"""
    
    def test_view_imports(self):
        """Verifica que las vistas se pueden importar"""
        from app.presentation.views.alchemy_view import AlchemyView
        from app.presentation.views.widgets.alchemy_counters_widget import AlchemyCountersWidget
        
        # Solo verificamos que se pueden importar
        assert AlchemyView is not None

        assert AlchemyCountersWidget is not None
