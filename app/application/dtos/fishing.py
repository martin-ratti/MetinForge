from dataclasses import dataclass, field
from typing import Dict
from .common import CharacterDTO

@dataclass
class FishingActivityDTO:
    year: int
    month: int
    week: int
    status_code: int

@dataclass
class FishingCharacterDTO(CharacterDTO):
    """Extiende CharacterDTO con mapa de actividad de pesca."""
    fishing_activity_map: Dict[str, int] = field(default_factory=dict)
