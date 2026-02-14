from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CharacterDTO:
    id: int
    name: str
    name: str
    # Campos específicos se añadirán por herencia o composición en DTOs especializados
    # Pero para mantener compatibilidad con Fishing (que usa este DTO base), lo dejo extensible
    # idealmente FishingCharacterDTO heredaría de este.
    # Por ahora, mantengo fishing_activity_map aquí para no romper FishingService inmediatamente,
    # o mejor: FishingService usará FishingCharacterDTO.

@dataclass
class GameAccountDTO:
    id: int
    username: str
    server_id: int
    # Characters será una lista de CharacterDTO genéricos o específicos según el contexto
    characters: List[CharacterDTO] = field(default_factory=list)

@dataclass
class StoreAccountDTO:
    id: int
    email: str
    game_accounts: List[GameAccountDTO] = field(default_factory=list)
