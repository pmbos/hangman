import time
import logging
import socket as S
from threading import Thread
from threading import Lock

from model.logger import Logger
import model.protocol as P
from model.player import Player
from model.result import Result
from server.group import Group

SRC = 'server/threads/new_connection'


class ConnectionHandler(Thread):
    def __init__(self, player: Player, lock: Lock, groups: list):
        super().__init__()
        self.player = player
        self.logger = Logger.create_logger(self.__repr__(), logging.INFO, to_file=True)
        self.lock = lock
        self.groups = groups

    def __repr__(self):
        addr, port = self.player.get_connection.getpeername()
        return f'<ConnectionHandler remote={addr}:{port}/>'

    def run(self):
        method = 'run'
        with self.lock:
            try:
                self._handshake()
                time.sleep(P.MESSAGE_DELAY)
                self._request_player()

                self.logger.info(f"Waiting for client response...  src={SRC}/{method}:59")
                response = self.player.listen()

                commands = P.decode_split_commands(response)
                corrections = 0

                while len(commands) != 1 and corrections < P.MAX_REQUEST_CORRECTIONS:
                    self._retry_request(self._request_player, corrections)

                if corrections >= P.MAX_REQUEST_CORRECTIONS:
                    self.logger.warning(
                        f"Max request attempts exceeded. Throwing out connection... src={SRC}/{method}:77")
                    self.player.disconnect()
                    return

                self.logger.info(f"Constructing player... src={SRC}/{method}:82")
                self.player = self._construct_player(commands[0]).result

                while not self._add_to_group().success:
                    self.logger.info(f"Creating new lobby... src={SRC}/{method}:87")
                    self.groups.append(Group(min_players=self.player.preferred_players))

            except S.error as error:
                conn_addr, conn_port = self.player.get_connection.getpeername()
                self.logger.warning(f"Connection with {conn_addr}:{conn_port} closed. src={SRC}/{method}:54")

    def _handshake(self):
        method = '_handshake'
        self.logger.info(f"Performing handshake...  src={SRC}/{method}:53")
        self.player.tell(P.WELCOME)

    def _request_player(self):
        method = '_request_player'
        self.logger.info(f'Requesting player data... src={SRC}/{method}:56')
        self.player.tell(P.REQUEST_PLAYER)

    def _construct_player(self, command):
        result = P.decode_player(command)

        if not result.success:
            return Result.get_negative()

        name, number_of_players = result.result
        return Result.get_positive(Player(self.player.get_connection, name, number_of_players))

    def _add_to_group(self):
        result = self._check_available_groups()

        if not result.success:
            return Result.get_negative()

        self._add_player_to_queue()
        result.result.add([self.player])

        return Result.get_positive()

    def _add_player_to_queue(self):
        self.player.tell(P.ADDING_TO_QUEUE)

    def _retry_request(self, to_retry, corrections=0):
        method = '_retry_request'
        corrections += 1
        self.logger.warning(f"Input not recognised. Retrying... src={SRC}/{method}:68")
        self._send_invalid_input()

        to_retry()

        self.logger.info(f"Waiting for client retry...  src={SRC}/{method}:72")
        response = self.player.listen()

        commands = P.decode_split_commands(response)
        return commands, corrections

    def _send_invalid_input(self):
        try:
            self.player.tell(P.INVALID_INPUT)
            return Result.get_positive()
        except S.error as error:
            return Result.get_negative(error)

    def _check_available_groups(self):
        for group in self.groups:
            if group.count + 1 <= group.min_players and group.count + 1 <= self.player.preferred_players:
                return Result.get_positive(group)

        return Result.get_negative()
