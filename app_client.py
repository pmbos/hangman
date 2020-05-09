from client.hangman_client import HangmanClient

SRC = 'app.py'


def main():
    client = HangmanClient()
    client.set_player_from_input()
    if client.connect():
        client.handle_server_input()


if __name__ == "__main__":
    main()
