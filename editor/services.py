from typing import Protocol, Tuple
from datetime import datetime, timedelta
from django.utils import timezone

class GameScheduleService(Protocol):
    """
    Interface for game scheduling services.
    Follows the Open/Closed Principle: new scheduling strategies can be added
    by implementing this interface without modifying the consumer code.
    """
    def get_next_game_time(self, current_time: datetime) -> Tuple[datetime, str]:
        ...

class StaticGameScheduleService:
    """
    Implementation of GameScheduleService that uses a static, hardcoded schedule.
    Preserves the original behavior of the application.
    """
    def get_next_game_time(self, current_time: datetime) -> Tuple[datetime, str]:
        # HORA PROGRAMADA DEL JUEGO (Hardcoded as per original requirement)
        game_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)

        if current_time > game_time:
            game_time += timedelta(days=1)
            
        return game_time, "Sala Principal"
