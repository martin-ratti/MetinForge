from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import date
from .common import CharacterDTO, StoreAccountDTO, GameAccountDTO

@dataclass
class AlchemyEventDTO:
    id: int
    server_id: int
    name: str
    total_days: int
    created_at: date

@dataclass
class AlchemyCharacterDTO(CharacterDTO):
    """Extiende CharacterDTO para Alquimia."""
    # Mapa de dia -> estado (1, -1, 0)
    daily_status_map: Dict[int, int] = field(default_factory=dict)
    
@dataclass
class AlchemyDashboardDTO:
    """Contenedor de datos para el dashboard de Alquimia."""
    # Lista de tiendas con sus cuentas y personajes (AlchemyCharacterDTO)
    store_accounts: List[StoreAccountDTO] = field(default_factory=list)
