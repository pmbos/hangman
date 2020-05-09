from server.hangman_server import HangmanServer

SRC = 'app.py'


def main():
    server = HangmanServer()
    server.start()


if __name__ == "__main__": 
    main()
