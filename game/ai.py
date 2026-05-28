from game.easy_ai import EasyAI
from game.medium_ai import MediumAI
from game.hard_ai import HardAI
from utils.constants import AI_EASY, AI_MEDIUM, AI_HARD


class QuoridorAI:
    def __init__(self, player, difficulty):
        if difficulty == AI_EASY:
            self.ai = EasyAI(player)
        elif difficulty == AI_HARD:
            self.ai = HardAI(player)
        else:
            self.ai = MediumAI(player)

    def get_move(self, state):
        return self.ai.get_move(state)
