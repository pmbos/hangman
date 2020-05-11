# Hangman
This project contains an implementation of the classic hangman
game in Python 3.8.2.  
The game is played through a server.  
  
A game goes as follows
1. 2 or more players connect.
2. One will be randomly chosen to pick a word.
    1. Said player will submit how many tries (5-15) the other players have.
    2. Said player will submit the word the other players have to guess.
3. Each player will be asked for their guess in turn.
    1. If correct, a message saying so will appear and the word will
    be partially filled out with all occurrences of the guess.
    2. If incorrect, a message saying so will appear and the word will
    not be (partially) filled out.
4. Step 3 will continue until either:
    1. The guessing players have guessed the word within the specified number
    of tries. Guessing players win.
    2. The guessing players have not guessed the word within the specified
    number of tries. Player choosing the word wins.
5. All players will be asked if they want to play again.
    1. If so, steps 2-5 repeat.
    2. If not, the players will be disconnected and their clients will 
    close.

---

##Contents
1. Server
2. Client

---

##Server
This project contains a server module. The server uses a low-level
socket implementation for communication with the client. It hosts
a game of hangman.

###Features
* Host a game of hangman.
* Listen for incoming client connections.
* Validate the connection.
* Handle the connection in a separate thread.
* Queue the connection until a lobby is ready to start a game.
* Automatically start a game when the lobby is ready.
* When the game ends, ask players if they want to play again.
* Playing concurrent games with threads.
* Elegant clean-up and error handling.

###Structure
