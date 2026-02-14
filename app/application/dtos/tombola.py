from dataclasses import dataclass, field
from typing import Dict, List
from datetime import date
from .common import CharacterDTO, StoreAccountDTO, GameAccountDTO

@dataclass
class TombolaEventDTO:
    id: int
    server_id: int
    name: str
    total_days: int
    created_at: date

@dataclass
class TombolaCharacterDTO(CharacterDTO):
    """Extiende CharacterDTO para Tómbola."""
    daily_status_map: Dict[int, int] = field(default_factory=dict)
    
@dataclass
class TombolaDashboardDTO:
    """Contenedor de datos para el dashboard de Tómbola."""
    store_accounts: List[StoreAccountDTO] = field(default_factory=list)
