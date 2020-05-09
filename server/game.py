from threading import Lock, Thread
import concurrent.futures as F
import time

import model.protocol as P
from model.player import Player
from server.hangman import Hangman


class Game(Thread):
    UNKNOWN = "*"

    def __init__(self, group, lock: Lock):
        super().__init__()
        self.group = group
        self.lock = lock
        self.current_player = None
        self.thread_finished = False
        self.game_over = False

    def __repr__(self):
        return f"<Game id={id(self)} players={self.group.players} />"

    def run(self):
        self.play()
        with self.lock:
            self.clean_up()

    def play(self):
        # Main game/thread loop
        while not self.game_over:
            self.current_player = self.group.next_player(self.current_player)

            with self.lock:
                self.tell_game_started()
                max_tries, word = self.request_current_player_info()

            hangman = Hangman(word, max_tries)

            with self.lock:
                self.game_part_guessing(hangman)
                self.communicate_win_or_loss(hangman.tries, hangman.max_tries)

                if not self.request_continue_game():
                    self.game_over = True
        # End main game/thread loop

    @property
    def get_group(self):
        return self.group

    def tell_game_started(self):
        self.tell_all_players(P.GAME_START)
        time.sleep(0.5)
        to_send = P.construct_choosing_player(self.current_player)
        self.tell_all_but_current_player(to_send)

    def game_part_guessing(self, hangman: Hangman):
        guessing_player = self.group.select_first_guessing_player(self.current_player)

        while not hangman.has_winner and hangman.tries <= hangman.max_tries:
            guessing_player = self.group.next_guessing_player(self.current_player, guessing_player)

            self.tell_all_players(P.construct_move(hangman.guessed_letters))
            time.sleep(0.5)

            guess = self.request_guess(guessing_player, hangman.max_tries, hangman.tries)
            guessing_player.tell(P.construct_correct(hangman.guess(guess)))

    def communicate_win_or_loss(self, turns, max_tries):
        scores = [score for score in [player.score for player in self.group.players]]
        if turns <= max_tries:
            self.tell_all_but_current_player(P.won(scores))
            self.tell_current_player(P.lost(scores))
        else:
            self.current_player.increase_score()
            self.tell_all_but_current_player(P.lost(scores))
            self.tell_current_player(P.won(scores))

    def request_guess(self, guessing_player: Player, max_tries: int, tries: int):
        self.tell_all_players(P.construct_turn(guessing_player, max_tries - tries))

        response = guessing_player.listen()
        commands = P.decode_split_commands(response)

        if len(commands) != 1:
            raise ValueError

        guess = P.decode_guess(commands[0])

        if guess is not None:
            return guess

        guessing_player.tell(P.INVALID_INPUT)
        self.request_guess(guessing_player, max_tries, tries)

    def request_continue_game(self):
        with F.ThreadPoolExecutor() as executor:
            futures = [f for f in [executor.submit(p.play_again_thread) for p in self.group.players]]
            responses = [f.result() for f in futures]

        return all(responses)

    def _request_max_tries(self):
        self.tell_current_player(P.REQUEST_MAX_TRIES)

        response = self.current_player.listen()
        commands = P.decode_split_commands(response)

        if len(commands) == 1:
            max_tries = P.decode_max_tries(commands[0])
            return max_tries

        self.tell_current_player(P.INVALID_INPUT)
        self._request_max_tries()

    def _request_secret_word(self):
        self.tell_current_player(P.YOUR_TURN)

        response = self.current_player.listen()
        commands = P.decode_split_commands(response)

        if len(commands) == 1:
            secret_word = P.decode_secret_word(commands[0])

            if secret_word is not None:
                word = [letter for letter in secret_word.lower()]
                return word

        self.tell_current_player(P.INVALID_INPUT)
        self._request_secret_word()

    def request_current_player_info(self):
        return self._request_max_tries(), self._request_secret_word()

    def tell_all_players(self, message):
        for player in self.group.players:
            player.tell(message)

    def tell_current_player(self, message):
        self.current_player.tell(message)

    def tell_all_but_current_player(self, message):
        for player in self.group.players:
            if player != self.current_player:
                player.tell(message)

    def clean_up(self):
        for player in self.group.players:
            player.tell(P.FORCE_DISCONNECT)
            player.get_connection.close()
        self.thread_finished = True
