import socket
import logging
from threading import Event
from threading import Lock

from model.logger import Logger as L
from model.player import Player
from server.threads.group_manager_thread import GroupManager
from server.threads.new_connection_thread import ConnectionHandler
from server.threads.server_input import ServerInput

SRC = 'server/hangman_server.py'


class HangmanServer:
    """
    This class represents a server hosting a game of Hangman.
    Once started, it will listen for connections and forward them to threads to deal with them.
    """
    def __init__(self, host='', port=5050, max_connections=5):
        """
        Initialise the server.
        :param host: the host's IPv4 address to bind the server to.
        :param port: the port to bind the server to. Default = 5050.
        :param max_connections: the maximum number of connections the server will queue before dropping the next.
        """
        self.logger_file = L.create_logger('SERVER_MAIN', logging.INFO, to_file=True)
        self.logger_info = L.create_logger('SERVER_MAIN_COMM', logging.INFO, to_file=False)
        self.host = host
        self.port = port
        self.address = (host, port)
        self.groups = []
        self.events = []
        self.max_connections = max_connections

    def start(self):
        """
        Start the server.
        :return: None
        """
        self.logger_file.info(f"Starting server... src={SRC}/main:40")
        sock = self.setup_socket()

        lock = Lock()

        input_thread = ServerInput(sock, self.events)
        input_thread.start()

        queue_managing_thread = GroupManager(self.groups, lock, self.add_terminal_event)
        queue_managing_thread.start()

        self.logger_file.info('Server ready... src={SRC}/main:53')
        self.logger_info.info("Ready...")

        while True:
            try:
                connection, address = sock.accept()
                self.logger_file.info(f'{address[0]}:{address[1]} just connected. src={SRC}/main:59')
                self.logger_info.info(f"{address[0]}:{address[1]} just connected.")

                with lock:
                    connection_handler = ConnectionHandler(Player(connection=connection), lock, self.groups)
                    connection_handler.start()

            except socket.error:
                self.logger_file.critical("Socket closed... Terminating server... src={SRC}/main:67")
                break

    def setup_socket(self):
        """
        Create a server-socket, set it up and enable it to listen.
        :return: socket.socket, the created server socket.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger_file.info(f"Socket opened... src={SRC}/set_up:23")

        try:
            s.bind(self.address)
        except OSError:
            self.logger_file.error(f"Could not bind socket to: {self.host}:{self.port}. src={SRC}/set_up:28")
            exit(1)
        
        self.logger_file.info("Socket bound successfully... src={SRC}/set_up:31")

        s.listen(self.max_connections)
        self.logger_file.info("Socket now listening... src={SRC}/set_up:34")
        return s

    def add_terminal_event(self, event: Event):
        """
        Add a terminal event to the server's event list.
        Used to gracefully terminate threads, when the termination command is given.
        :param event: threading.Event, the event to add.
        :return: None
        """
        self.events.append(event)
