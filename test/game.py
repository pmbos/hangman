import logging

from server.game import Game
from model.player import Player

game = None
player_1 = None
player_2 = None

logger = logging.getLogger("test_game")
logger.setLevel(logging.INFO)


def run ():
    set_up()
    game.guessed_letters = [Game.UNKNOWN for x in game.word]
    check(test_has_no_winner())

    set_up()
    game.guessed_letters = [x for x in game.word]
    check(test_has_winner())

    set_up()
    game.guessed_letters = [Game.UNKNOWN for x in game.word]
    check(test_guess_correct())

    set_up()
    game.guessed_letters = [Game.UNKNOWN for x in game.word]
    check(test_guess_incorrect())

    set_up()
    check(test_next_guessing_player_current_is_none())

    set_up()
    check(test_next_guessing_player_current_not_none())

    set_up()
    check(test_next_player())


def set_up ():
    global game
    global player_1
    global player_2

    player_1 = Player(name="Pascal")
    player_2 = Player(name="Alina")
    game = Game([player_1, player_2])
    game.word = ['n', 'a', 'm', 'e']


def test_next_player ():
    global game
    start_test('test_next_player')

    first = game.next_player()
    game.current_player = first
    first_correct = first == Player(name="Pascal")

    second = game.next_player()
    game.current_player  = second
    second_correct = second == Player(name="Alina")

    last = game.next_player() == Player(name="Pascal")

    return first_correct and second_correct and last


def test_has_no_winner ():
    global game
    start_test("test_has_no_winner")

    return not game.has_winner


def test_has_winner ():
    global game
    start_test("test_has_winner")

    return game.has_winner


def test_guess_correct ():
    global game
    start_test("test_guess_correct")

    correct, result = game.guess('n')

    return correct and result[0] == 'n'


def test_guess_incorrect ():
    global game
    start_test('test_guess_incorrect')

    correct, result = game.guess('r')

    return not correct and 'r' not in result


def test_next_guessing_player_current_is_none ():
    global game
    start_test('test_next_guessing_player_current_is_none')

    current = game.players[0]
    next_player_1 = game.next_guessing_player(current)
    next_player_2 = game.next_guessing_player(next_player_1)

    current_correct = current == Player(name="Pascal")
    player_1_correct = next_player_1 == Player(name="Alina")
    player_2_correct = next_player_2 == Player(name="Pascal")

    return current_correct and player_1_correct and player_2_correct


def test_next_guessing_player_current_not_none ():
    global game
    start_test('test_next_guessing_player_current_not_none')

    game.current_player = game.players[0]
    next_player_1 = game.next_guessing_player(game.players[1])
    next_player_2 = game.next_guessing_player(next_player_1)

    current_correct = game.current_player == Player(name="Pascal")
    player_1_correct = next_player_1 == Player(name="Alina")
    player_2_correct = next_player_2 == Player(name="Alina")

    return current_correct and player_1_correct and player_2_correct


def check(method:bool):
    global logger

    if method:
      logger.warning("PASSED \n")
    else:
      logger.warning("FAILED \n")


def start_test (name):
    global logger
    logger.warning(f"TESTING: {name}")


if __name__ == "__main__":
    run()
