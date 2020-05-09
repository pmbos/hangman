from socket import socket
import socket as S
import logging
import time

import model.protocol as P

SRC = "model/player.py"


class Player:
    def __init__ (self, connection: socket = None, name="new_player", preferred_players=2):
        self.connection = connection
        self.score = 0
        self.name = name
        self.preferred_players = preferred_players
        self.logger = self.get_logger(f"logger_{self.__repr__()}")

    def __repr__(self):
        return f"<Player name={self.name}/>"

    @property
    def get_connection (self):
        return self.connection

    @property
    def is_connected (self):
        try:
            self.tell(P.HEARTBEAT)
            return True
        except S.error as error:
            return False

    def increase_score (self, value=1):
        self.logger.info(f"{self} Increasing score by {value}. src={SRC}/increase_score:22")
        self.score += value

    def set_name (self, value:str):
        self.logger.info(f"{self} Setting name to {value}. src={SRC}/set_name:26")
        self.name = value

    def tell (self, message):
        self.logger.info(f"Sending: {message}. src={SRC}/tell:30")
        try:
            header = P.write_header(message)
            self.connection.sendall(header.encode())
            time.sleep(P.MESSAGE_DELAY)
            self.connection.sendall(message.encode())
        except S.error as error:
            self.logger.error(f'Could not write to client! {error}')

    def listen (self, buffer=4096):
        try:
            success, header = P.read_header(self)

            if not success:
                raise S.error

            response = self.connection.recv(header).decode()
            self.logger.info(f"{self} Received: {response}. src={SRC}/listen:35")
            return response
        except S.error as error:
            self.logger.error('Could not read from client!')

    @staticmethod
    def get_logger(name: str):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('communication.log', 'w')
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        format_date = '%d/%m/%Y %I:%M:%S %p'
        formatter = logging.Formatter(fmt=format_string, datefmt=format_date)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def __eq__(self, value):
        if isinstance(value, Player):
            return self.name == value.name
        return False

    def play_again_thread(self):
        self.tell(P.CONTINUE_PLAYING)
        response = self.listen()
        return P.decode_continue(response)

    def disconnect(self):
        self.tell(P.FORCE_DISCONNECT)
        self.get_connection.close()
