from logging import Logger
import socket as S

from model.player import Player
import model.protocol as P

max_length = 25
picked_length = 10

WELCOME_MESSAGE = 'Successfully connected to the server!'
GAME_START = 'Game is starting!'
YOUR_TURN = 'Your turn to pick a word: '
INVALID_GUESS = 'Your guess was invalid! Please enter an alphabetic letter.'
INVALID_WORD = f'Your word is invalid! Please use alphabetic letters and do not exceed {picked_length}.'
CHECK_GUESS = 'Checking if guess is correct...'
CONNECT_FAILED = 'Unable to connect to server!'
YOUR_GUESS = 'Your turn to guess '
MAX_TRIES = 'Enter the maximum number of times players may guess your word: '
CORRECT_GUESS = 'Your guess was correct!'
INCORRECT_GUESS = 'Your guess was incorrect!'
INCORRECT_SERVER_FORMAT = 'Could not understand the server. Disconnecting...'
FORCE_DISCONNECT = 'The game is over. Disconnecting and shutting down...'
ADD_TO_QUEUE = 'You are being added to a game lobby.'
WIN_MESSAGE = 'You won! Asking players if they want to play another round...'
LOST_MESSAGE = 'Sorry, you lost! Better luck next time. Asking players if they want to play another round...'
ANOTHER_ROUND = 'Do you want to play another round (y/n)? '
OTHER_PLAYER_CONTINUE = 'Getting answers from other players...'


def welcome(**kwargs):
    return True, WELCOME_MESSAGE


def start(**kwargs):
    return True, GAME_START


def choosing_player(**kwargs):
    operation = P.decode_player(kwargs.get('payload', None))
    if not operation.success:
        logger = kwargs.get('file_logger', None)
        logger.error(f'Could not create player: {operation.result}')
        return False, 'Could not create player'

    return True, f'{operation.result[0]} is choosing a word.'


def send_player(**kwargs):
    player: Player = kwargs.get('player', None)
    to_send = P.construct_player(player)

    try:
        player.tell(to_send)
    except S.error as error:
        kwargs.get('file_logger', None).error(error)
        player.get_connection.close()
        return False, CONNECT_FAILED
    return True, None


def my_turn(**kwargs):
    logger: Logger = kwargs.get('logger', None)
    player: Player = kwargs.get('player', None)

    while True:
        try:
            word = input(YOUR_TURN)

            if len(word) > max_length or len(word) > picked_length:
                raise ValueError

            if not word.isalpha():
                raise ValueError

            to_send = P.construct_secret_word(word)
            player.tell(to_send)
            return True, None
        except ValueError:
            logger.warning(INVALID_WORD)
        except S.error:
            player.get_connection.close()
            return False, CONNECT_FAILED


def player_turn(**kwargs):
    payload = kwargs.get('payload', None)
    me = kwargs.get('player', None)
    player_name, tries_left = P.decode_turn(payload)

    if player_name == me.name:
        logger = kwargs.get('logger', None)

        while True:
            try:
                guess = input(YOUR_GUESS + f'({tries_left} tries left): ')
                to_send = P.construct_guess(guess)

                if not to_send[0]:
                    raise ValueError

                logger.info(CHECK_GUESS)
                me.tell(to_send[1])
                return True, None
            except ValueError:
                logger.warn(INVALID_GUESS)
            except S.error:
                me.get_connection.close()
                return False, CONNECT_FAILED
    else:
        return True, f"{player_name}'s turn to guess. ({tries_left} tries left)"


def another_round(**kwargs):
    logger = kwargs.get("logger", None)

    while True:
        response = input(ANOTHER_ROUND)
        to_send = P.construct_continue(response)

        if to_send is not None:
            player = kwargs.get('player', None)

            player.tell(to_send)
            return True, OTHER_PLAYER_CONTINUE
        logger.info('Please answer with Y(es) or N(o).')


def max_tries(**kwargs):
    logger: Logger = kwargs.get('logger', None)

    while True:
        try:
            maximum = int(input(MAX_TRIES))

            if maximum > P.MAX_TURNS or maximum < P.MIN_TURNS:
                raise ValueError

            picked = maximum

            to_send = P.construct_max_tries(picked)
            player: Player = kwargs.get('player', None)

            player.tell(to_send)
            break
        except ValueError:
            logger.warning(f'You should allow for between {P.MIN_TURNS}-{P.MAX_TURNS} tries.')
    return True, None


def process_move(**kwargs):
    payload = kwargs.get('payload', None)
    result, letters = P.decode_move(payload)

    try:
        if not result:
            raise ValueError
    except ValueError:
        kwargs.get('player', None).get_connection.close()
        return False, INCORRECT_SERVER_FORMAT

    to_display = 'Word: '
    to_display += ' '.join(letters)

    return True, to_display


def correct_guess(**kwargs):
    payload = kwargs.get('payload', None)
    correct = P.decode_correct(payload)

    if correct[0] and correct[1]:
        return True, CORRECT_GUESS
    elif correct[0] and not correct[1]:
        return True, INCORRECT_GUESS
    else:
        kwargs.get('player').get_connection.close()
        return False, INCORRECT_SERVER_FORMAT


def disconnect(**kwargs):
    socket = kwargs.get('player').get_connection
    socket.close()

    return False, FORCE_DISCONNECT


def heartbeat(**kwargs):
    logger = kwargs.get('file_logger', None)
    logger.info('Received heartbeat')
    return True, None


def win(**kwargs):
    return True, WIN_MESSAGE


def lost(**kwargs):
    return True, LOST_MESSAGE


def add_to_queue(**kwargs):
    return True, ADD_TO_QUEUE
