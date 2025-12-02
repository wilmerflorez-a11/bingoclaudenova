from typing import Protocol, Tuple, List, Dict
from datetime import datetime, timedelta
from django.utils import timezone
import random

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
        # For MVP/Testing: Game is always "now" for immediate access
        return datetime.now(), "Sala Principal"

class BingoCardService:
    """
    Service to generate valid 75-ball Bingo cards.
    """
    def generate_card(self) -> List[List[int]]:
        """
        Generates a 5x5 matrix for 75-ball Bingo.
        Columns: B (1-15), I (16-30), N (31-45), G (46-60), O (61-75).
        Center cell (2,2) is 0 (FREE).
        """
        card = []
        ranges = [
            (1, 15),   # B
            (16, 30),  # I
            (31, 45),  # N
            (46, 60),  # G
            (61, 75)   # O
        ]
        
        # Generate columns first
        columns = []
        for start, end in ranges:
            # Sample 5 unique numbers from the range
            col = random.sample(range(start, end + 1), 5)
            columns.append(col)
            
        # Transpose to rows for 5x5 matrix
        for r in range(5):
            row = []
            for c in range(5):
                if r == 2 and c == 2:
                    row.append(0) # Free space
                else:
                    row.append(columns[c][r])
            card.append(row)
            
        return card

class GameEngineService:
    """
    Service to manage game logic: drawing balls and validating wins.
    """
    def draw_ball(self, drawn_balls: List[int]) -> int:
        """
        Draws a random ball from 1-75 that hasn't been drawn yet.
        Returns -1 if all balls are drawn.
        """
        if len(drawn_balls) >= 75:
            return -1
            
        available = [n for n in range(1, 76) if n not in drawn_balls]
        return random.choice(available)
        
    def validate_bingo(self, card_matrix: List[List[int]], drawn_balls: List[int]) -> bool:
        """
        Validates if a card has a winning pattern (Line, Full House, etc.).
        For MVP, we'll check for ANY horizontal, vertical, or diagonal line.
        """
        # Convert drawn balls to set for O(1) lookup
        drawn_set = set(drawn_balls)
        drawn_set.add(0) # Free space is always "drawn"
        
        # Check Rows
        for row in card_matrix:
            if all(num in drawn_set for num in row):
                return True
                
        # Check Columns
        for c in range(5):
            col = [card_matrix[r][c] for r in range(5)]
            if all(num in drawn_set for num in col):
                return True
                
        # Check Diagonals
        diag1 = [card_matrix[i][i] for i in range(5)]
        if all(num in drawn_set for num in diag1):
            return True
            
        diag2 = [card_matrix[i][4-i] for i in range(5)]
        if all(num in drawn_set for num in diag2):
            return True
            
        return False
