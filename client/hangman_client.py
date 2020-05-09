import socket as S
import logging
import ipaddress

from model.logger import Logger as L
from model.player import Player
import model.protocol as P
import client.interpreters as I

SRC = 'client/hangman_client.py'


class HangmanClient:
    COMMAND_TO_FUNCTION = {
        P.WELCOME: I.welcome,
        P.REQUEST_PLAYER: I.send_player,
        P.GAME_START: I.start,
        P.MOVE_MADE: I.process_move,
        P.YOUR_TURN: I.my_turn,
        P.REQUEST_MAX_TRIES: I.max_tries,
        P.TURN: I.player_turn,
        P.CORRECT: I.correct_guess,
        P.FORCE_DISCONNECT: I.disconnect,
        P.ADDING_TO_QUEUE: I.add_to_queue,
        P.INVALID_INPUT: lambda **kwargs: (True, 'Invalid input, server will re-send request...'),
        P.HEARTBEAT: I.heartbeat,
        P.WIN: I.win,
        P.LOSS: I.lost,
        P.CHOOSING_PLAYER: I.choosing_player,
        P.CONTINUE_PLAYING: I.another_round
    }

    def __init__(self, remote='127.0.0.1', port=5050, player: Player = None):
        self.remote = remote
        self.port = port
        self.address = (remote, port)
        self.player = player
        self.app_logger = L.create_logger('CLIENT_MAIN', logging.INFO, to_file=True)
        self.communication_logger = L.create_logger('Hangman client', logging.INFO)

        self.app_logger.info(f'Starting client... src={SRC}/__init__:41')
        self.communication_logger.info('Welcome to the hangman client!')

    def set_player(self, player: Player, warn=True):
        if self.player is not None and self.player.get_connection is not None:
            if warn:
                self.communication_logger.warn("""A player object already exists for this client. 
                                                Overwriting... (To turn off this message, set warn=False)""")
            else:
                self.app_logger.warn('A player object already exists for this client. Overwriting...')

        self.player = player

    def set_player_from_input(self):
        self.player = HangmanClient.build_player_from_input(self.app_logger, self.communication_logger)

    def connect(self):
        if self.player is None and self.player.get_connection is None:
            self.communication_logger.error(
                'No player has been configured for this client! Please configure a player before connecting.')
            return False

        try:
            self.player.get_connection.connect(self.address)
            self.communication_logger.info(f'Connected to: {self.remote}:{self.port}')
            return True
        except S.error as error:
            self.app_logger.error(error.message)
            self.communication_logger.error('Failed to connect, see stacktrace.log for full stacktrace.')

        return False

    def handle_server_input(self):
        method = 'handle_server_communication'
        kwargs = {'logger': self.communication_logger,
                  'player': self.player,
                  'file_logger': self.app_logger
                  }
        sock = self.player.get_connection
        listen = True

        while listen:
            try:
                data = self.player.listen()

                if not data:
                    self.app_logger.warn('Server disconnected!')
                    break

                commands = P.decode_split_commands(data)

                if len(commands) > 2:
                    kwargs['payload'] = commands[1:]
                elif len(commands) > 1:
                    kwargs['payload'] = commands[1]
                elif len(commands) == 1:
                    kwargs['payload'] = commands[0]
                self.app_logger.info(f'Received from server: {data}. src={SRC}/{method}:115')

                command = commands[0].split(P.ASSIGNMENT)[0]
                to_execute = self._interpret(command)
                view = to_execute(**kwargs)

                if view[1] is not None:
                    self.communication_logger.info(view[1])

                listen = view[0]
            except OSError:
                self.app_logger.critical(f'Could not read from server... src={SRC}/{method}:107')
                self.communication_logger.critical(I.CONNECT_FAILED)
                sock.close()
                listen = False
        self.app_logger.info('Disconnected from server')

    def set_remote_from_input(self):
        remote, port = self._build_connection_from_input()
        self.remote = remote
        self.port = port
        self.address = (remote, port)

    def set_remote(self, remote: str, port: int):
        self.remote = remote
        self.port = port
        self.address = (remote, port)

    @staticmethod
    def build_player_from_input(app_logger: logging.Logger, communication_logger: logging.Logger):
        method = 'construct_player'

        app_logger.info(f'Obtaining player info... src={SRC}/{method}:75')

        name = HangmanClient._username_from_input(app_logger, communication_logger)
        max_players = HangmanClient._max_players_from_input(communication_logger)
        sock = S.socket(S.AF_INET, S.SOCK_STREAM)

        return Player(sock, name, max_players)

    def _build_connection_from_input(self):
        return self._remote_from_input(), self._port_from_input()

    def _remote_from_input(self):
        remote = input('Enter the server address to connect to: ')
        host = S.gethostbyname(remote)
        try:
            ipaddress.ip_address(host)
            return host
        except ValueError as error:
            self.communication_logger.warn('Invalid server address. Try again...')
            self._remote_from_input()

    def _port_from_input(self):
        port = input('Enter the port you want to connect to: ')

        try:
            port = int(port)
            return port
        except ValueError as error:
            self.communication_logger.warn('Invalid port. Try again...')
            self._port_from_input()

    @staticmethod
    def _username_from_input(app_logger: logging.Logger, communication_logger: logging.Logger):
        method = '_username_from_input'
        name = input('Enter your username: ')

        if not name.isalnum():
            app_logger.warning(f'Invalid username. Retrying... src={SRC}/{method}:82')
            communication_logger.warning('The username you entered is invalid!')

            HangmanClient._username_from_input(app_logger, communication_logger)
        return name

    @staticmethod
    def _max_players_from_input(communication_logger: logging.Logger):
        try:
            preferred_players = int(input('Enter the number of players you want to play with: '))

            if preferred_players < 1 or preferred_players > 4:
                raise ValueError

            return preferred_players
        except ValueError:
            communication_logger.warning('Please enter an integer between 1-4.')
            HangmanClient._max_players_from_input(communication_logger)

    def _interpret(self, data):
        return HangmanClient.COMMAND_TO_FUNCTION.get(data, self._protocol_not_respected)

    def _protocol_not_respected(self, **kwargs):
        logger = self.app_logger
        logger.error(I.INCORRECT_SERVER_FORMAT)
        return False, I.INCORRECT_SERVER_FORMAT
