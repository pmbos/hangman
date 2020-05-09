from model.result import Result

# Shared symbols
HEADER = 64
PADDING = b' '
DELIM = ";"
ASSIGNMENT = "="
LIST_DELIMITER = ","
MIN_TURNS = 5
MAX_TURNS = 25
MESSAGE_DELAY = 0.1  # in seconds

# Server symbols
MAX_REQUEST_CORRECTIONS = 5
CYCLE_TIMEOUT = 5  # in seconds
MAX_GROUPS_PER_MANAGER = 30

# Incoming from client
GUESS = "G"
SECRET = "SEC"
MAX_TRIES = "MT"

# Outgoing from server
CORRECT = "C"  # valid: C=1 or C=0
MOVE_MADE = "M"  # valid: M=*,*,*,e,*
SCORE = "S"  # valid: S=x,y,z,a
WELCOME = "HI"
REQUEST_PLAYER = "RP"
REQUEST_MAX_TRIES = "RMT"
ADDING_TO_QUEUE = "ATQ"
GAME_START = "START"
YOUR_TURN = "YT"
TURN = "T"
INVALID_INPUT = "ERR=input"
FORCE_DISCONNECT = "REVOKE"
HEARTBEAT = 'HB'
CHOOSING_PLAYER = 'CP'
CONTINUE_PLAYING = 'AR'
WIN = 'W'
LOSS = 'L'

# Shared
PLAYER = "P"


def won(scores: list):
    return f'{WIN}{DELIM}{construct_score(scores)}'


def lost(scores: list):
    return f'{LOSS}{DELIM}{construct_score(scores)}'


def construct_continue(response: str):
    if response.lower() == 'y':
        return f'{CONTINUE_PLAYING}{ASSIGNMENT}1'
    elif response.lower() == 'n':
        return f'{CONTINUE_PLAYING}{ASSIGNMENT}0'
    else:
        return None


def construct_max_tries(tries: int):
    return f'{MAX_TRIES}{ASSIGNMENT}{tries}'


def construct_choosing_player(player):
    return f'{CHOOSING_PLAYER}{DELIM}{construct_player(player)}'


def construct_secret_word(word: str):
    return f'{SECRET}{ASSIGNMENT}{word}'


def construct_guess(letter: str):
    if len(letter) == 1 and letter.isalpha():
        return True, f'G={letter}'
    return False, None


def construct_correct(value: bool):
    if value:
        return f"{CORRECT}{ASSIGNMENT}1"
    return f"{CORRECT}{ASSIGNMENT}0"


def construct_score(scores: list):
    score_string = f"{SCORE}{ASSIGNMENT}"
    score_string += LIST_DELIMITER.join([str(score) for score in scores])
    return score_string


def construct_move(guessed_letters: list):
    move_string = f"{MOVE_MADE}{ASSIGNMENT}"
    move_string += LIST_DELIMITER.join(guessed_letters)
    return move_string


def construct_turn(player, tries_left):
    return f"{TURN}{DELIM}{construct_player(player)}{DELIM}{tries_left}"


def construct_player(player):
    return f"{PLAYER}{ASSIGNMENT}{player.name}{LIST_DELIMITER}{player.preferred_players}"


def decode_turn(command: str):
    operation = decode_player(command[0])

    if not operation.success:
        print('Failure!')
        return None
    player_args = operation.result

    if len(player_args) == 2:
        try:
            tries_left = int(command[1])
            return player_args[0], tries_left
        except ValueError:
            return None

    return None


def decode_split_commands(response: str):
    return response.split(DELIM)


def decode_player(command: str):
    parts = command.split(ASSIGNMENT)
    if parts[0] == PLAYER:
        construction_arguments = parts[1].split(LIST_DELIMITER)

        if len(construction_arguments) == 2:
            try:
                return Result.get_positive((construction_arguments[0], int(construction_arguments[1])))
            except ValueError as error:
                # WARNING Invalid argument
                return Result.get_negative(error)

    return Result.get_negative()


def decode_guess(command: str):
    parts = command.split(ASSIGNMENT)
    if parts[0] == GUESS:
        if len(parts[1]) == 1:
            return parts[1]
    return None


def decode_secret_word(command: str):
    parts = command.split(ASSIGNMENT)
    if parts[0] == SECRET:
        if len(parts[1]) < 50:
            return parts[1]
    return None


def decode_max_tries(command: str):
    parts = command.split(ASSIGNMENT)
    if parts[0] == MAX_TRIES:
        try:
            max_tries = int(parts[1])
            if MIN_TURNS < max_tries <= MAX_TURNS:
                return max_tries
        except ValueError as error:
            return None


def decode_move(command: str):
    parts = command.split(ASSIGNMENT)
    if parts[0] == MOVE_MADE:
        try:
            letters = parts[1].split(LIST_DELIMITER)
            return True, letters
        except ValueError:
            return False, None
    return False, None


def decode_correct(command: str):
    parts = command.split(ASSIGNMENT)
    if parts[0] == CORRECT:
        try:
            correct = int(parts[1])
            if correct == 1:
                return True, True
            return True, False
        except ValueError:
            return False, None
    return False, None


def decode_continue(command: str):
    parts = command.split(ASSIGNMENT)
    try:
        if int(parts[1]) == 1:
            return True
        elif int(parts[1]) == 0:
            return False
    except ValueError:
        return None


def read_header(player):
    """
    Read the header from the client.
    Return a tuple (bool, obj), with bool = True if the operation is successful. False otherwise.
        If successful, obj = the number of bits to expect as an integer.
        If not, obj = the error object causing the operation to fail.
    """
    next_bits = player.get_connection.recv(HEADER).decode()
    try:
        next_bits = int(next_bits)
        return True, next_bits
    except ValueError as error:
        return False, error


def write_header(message: str):
    """
    Create a header to write to the client, given a message.
    Return the string header to send to the client.
    """
    message_as_bytes = message.encode()
    length = len(message_as_bytes)
    header = str(length).encode() + PADDING * (HEADER - length)
    return header.decode()
