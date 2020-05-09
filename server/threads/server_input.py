from socket import socket
from threading import Thread
from threading import Event
import logging

from model.logger import Logger


class ServerInput(Thread):
    def __init__(self, server_socket: socket, events: list):
        super().__init__()
        self.socket = server_socket
        self.events = events
        self.logger = Logger.create_logger('SERVER_INPUT', logging.INFO, to_file=True)

    def run(self):
        self.logger.info('Ready to accept commands...')

        while True:
            command = input()
            self.logger.info(f'Received command: {command}')
            if command == 'CLOSE':
                self.socket.close()
                for event in self.events:
                    event.set()
                break
