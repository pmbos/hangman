class Hangman:
    UNKNOWN = '*'

    def __init__(self, secret, max_tries=10):
        self.secret = secret
        self.max_tries = max_tries
        self.guessed_letters = [Hangman.UNKNOWN] * len(self.secret)
        self.tries = 0

    def guess(self, letter: str):
        """
        Key arguments: letter, a string denoting the letter guessed.
        @requires len(letter) == 1
        @ensures will determine an updated list for guessed_letters
        Return: a tuple indicating whether the guess was correct (1st) and what the result is (2nd)
        """
        result = []
        self.tries += 1

        guessed = [x if x == letter else Hangman.UNKNOWN for x in self.secret]
        guessed = zip(self.guessed_letters, guessed)

        for x, y in guessed:
            if x == Hangman.UNKNOWN and y != Hangman.UNKNOWN:
                result.append(y)
            else:
                result.append(x)

        self.guessed_letters = result
        return letter in self.secret

    @property
    def has_winner(self):
        """
        Check if the game was won. 
        Return: True if guessed_letters matches secret.
        """
        return self.guessed_letters == self.secret
