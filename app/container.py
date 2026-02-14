from app.application.services.fishing_service import FishingService
from app.application.services.alchemy_service import AlchemyService
from app.application.services.tombola_service import TombolaService

class ServiceContainer:
    _fishing_service = None
    _alchemy_service = None
    _tombola_service = None

    @classmethod
    def fishing_service(cls):
        if not cls._fishing_service:
            cls._fishing_service = FishingService()
        return cls._fishing_service

    @classmethod
    def alchemy_service(cls):
        if not cls._alchemy_service:
            cls._alchemy_service = AlchemyService()
        return cls._alchemy_service

    @classmethod
    def tombola_service(cls):
        if not cls._tombola_service:
            cls._tombola_service = TombolaService()
        return cls._tombola_service
