from threading import Event
from threading import Thread
from threading import Lock
import logging

import model.protocol as P
from model.logger import Logger
from server.game import Game

SRC = 'server/threads/group_manager_thread'


class GroupManager(Thread):
    """A thread for managing the different groups or lobbies"""

    def __init__(self, assigned_groups: list, lock: Lock, add_event_to_server):
        """
        Initialise the group manager.
        :param assigned_groups: the groups this manager will manage.
        :param lock: a thread lock to ensure the Game thread does not access its group at the same time as this manager.
        :param add_event_to_server: a reference to the corresponding server's add_terminal_event method.
        """
        super().__init__()
        self.terminal_event = Event()
        self.groups = assigned_groups
        self.logger = Logger.create_logger(self.__repr__(), logging.INFO, to_file=True)
        self.games = []
        self.lock = lock

        add_event_to_server(self.terminal_event)

    def __repr__(self):
        return f'<GroupManager, id={id(self)}>'

    def run(self):
        """
        Check whether each group is ready to start a game.
        Start a game for a particular group if it is ready.
        Check if players have disconnected from a game, terminate connections and remove group if so.
        Clean up any games and groups that have finished.
        :return: None
        """
        while not self.is_terminal_event_set:
            with self.lock:
                for group in [g for g in self.groups if not g.in_game]:
                    if not self.all_players_connected:
                        self.logger.info(f"""Players from {group} are no longer connected. Clearing group...
                                          src={SRC}/run:21""")
                        group.close_all()
                        self.groups.remove(group)
                        continue

                    if GroupManager.is_ready(group):
                        group.start()
                        self.logger.info(f"{group}, ready... src={SRC}/run:28")

                        game_thread = Game(group, self.lock)
                        self.games.append(game_thread)
                        game_thread.start()

                        self.logger.info("Game started... src={SRC}/run:35")

                self.clean_finished_games()

            self.terminal_event.wait(P.CYCLE_TIMEOUT)
        self.logger.warning('Shutting down manager thread. src={SRC}/run:45')

    @property
    def manager_id(self):
        return id(self)

    @property
    def responsible_groups(self):
        return self.groups.copy()

    @property
    def is_terminal_event_set(self):
        return self.terminal_event.isSet()

    @property
    def all_players_connected(self):
        list_of_lists = [g.players for g in self.responsible_groups]
        players = [p for players in list_of_lists for p in players]
        return all([player.is_connected for player in players])

    @staticmethod
    def is_ready(group):
        return group.count >= group.min_players

    def clean_finished_games(self):
        for game in [g for g in self.games if g.thread_finished]:
            try:
                self.games.remove(game)
                self.groups.remove(game.get_group)
                self.logger.info(f'Game {game} is over. Cleaned up {game} and {game.get_group}')
            except ValueError:
                self.logger.error(
                    f'{game} not found or corresponding group not found... src={SRC}/run:42')

    def set_terminal_event(self):
        self.terminal_event.set()

    def reset_terminal_event(self):
        self.terminal_event.clear()
