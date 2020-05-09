import random

from model.player import Player
import model.protocol as P


class Group:
    def __init__(self, min_players=2):
        self.players = []
        self.min_players = min_players
        self.in_game = False

    def __repr__(self):
        return f"<Group id={id(self)}, players={self.players}, min_players={self.min_players}, in_game={self.in_game} />"

    def __eq__(self, value):
        if isinstance(value, Group):
            return id(self) == id(value)
        return False

    @property
    def count(self):
        return len(self.players)

    def next_player(self, current_player: Player):
        """
        @requires len(self.players) > 0.
        @ensures selects the next player to specify a word.
        Return: the next Player object to specify a word.
        """
        length = len(self.players)

        if current_player is not None:
            return self.players[(self.players.index(current_player) + 1) % length]

        return self.players[0]

    def next_guessing_player(self, current_player: Player, current_guessing: Player):
        """
        Key arguments: current_player, the currently choosing player/the player who just chose a word.
                      current_guessing, the currently guessing player/the player who just guessed.
        @requires current is not None
        @ensures selects the next player to guess.
        Return: the next Player object to guess
        """
        guessing_players = [player for player in self.players if player != current_player]
        length = len(guessing_players)

        return guessing_players[(guessing_players.index(current_guessing) + 1) % length]

    def start(self):
        self.in_game = True

    def add(self, player: list):
        self.players.extend(player)

    def remove(self, player: Player):
        self.players.remove(player)

    def select_first_guessing_player(self, current_player: Player):
        guessing_players = [p for p in self.players if p != current_player]
        random_index = random.randint(0, len(guessing_players) - 1)
        return guessing_players[random_index]

    def close_all(self):
        for player in self.players:
            if player.is_connected:
                player.tell(P.FORCE_DISCONNECT)
            player.get_connection.close()
