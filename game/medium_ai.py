
from game.algorithms import get_ai_move


class MediumAI:
    def __init__(self, player):
        self.player = player

    def get_move(self, state):
        return get_ai_move(state, self.player, "medium")
