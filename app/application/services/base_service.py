from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import Config

class BaseService:
    """Servicio base con factory de sesiones y utilidades compartidas."""
    
    _engine = None
    _SessionFactory = None

    def __init__(self, session=None):
        self._injected_session = session

    @classmethod
    def _init_engine(cls):
        if cls._engine is None:
            cls._engine = create_engine(Config.get_db_url(), pool_recycle=3600)
            cls._SessionFactory = sessionmaker(bind=cls._engine)

    def get_session(self):
        if self._injected_session:
            return self._injected_session
        self._init_engine()
        return self._SessionFactory()

    def _get_next_pending_day_generic(self, char_id, event_id, activity_model, max_days=31):
        """Retorna el proximo dia pendiente (status == 0 o sin registro)."""
        session = self.get_session()
        try:
            activities = session.query(activity_model).filter_by(
                character_id=char_id,
                event_id=event_id
            ).all()

            status_map = {act.day_index: act.status_code for act in activities}

            for day in range(1, max_days + 1):
                if status_map.get(day, 0) == 0:
                    return day

            return max_days
        except Exception:
            return 1
        finally:
            if not self._injected_session:
                session.close()
