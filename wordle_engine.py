import argparse
import random
import sys


class WordleEngine:

    def __init__(self, filepath, word_len=5, target_word=None):
        self.WORD_LEN = word_len
        self._filepath = filepath

        # Read in the Vocabulary from filepath
        self._vocab = set()
        with open(self._filepath, 'r') as file:
            for line in file:
                self._vocab.add(line.strip().lower())

        # Set Target Word
        if target_word:
            self._target_word = target_word
        else:
            self._target_word = random.choice(list(self._vocab))
        self._letter_counts = dict.fromkeys(self._target_word, 0)
        for ch in self._target_word:
            self._letter_counts[ch] += 1


    def _reveal_target_word(self):
        return self._target_word


    def _validate_guess(self, guess):
        out = [-1] * self.WORD_LEN
        seen_cnts = dict.fromkeys(self._letter_counts, 0)
        # The 2 for-loops below shouldn't be combined together.
        # First label the correctly positioned letters, only then go about labeling -1/0's.
        for idx, ch in enumerate(guess):
            if ch == self._target_word[idx]:
                out[idx] = 1
                seen_cnts[ch] += 1
        for idx, ch in enumerate(guess):
            if out[idx] == 1:
                continue
            elif ch in self._letter_counts and seen_cnts[ch] < self._letter_counts[ch]:
                out[idx] = 0
                seen_cnts[ch] += 1
        return out


    def read_guess(self, attempt_no):
        while True:
            sys.stdout.flush()
            guess = input(f"\nGuess the word #{attempt_no}: ").strip().lower()
            if len(guess) != self.WORD_LEN:
                print(f"Expected a 5-letter word, got {guess}")
                continue
            elif guess not in self._vocab:
                print(f"{guess} is not in the vocabulary")
                continue
            else:
                break
        return guess


    def display_attempt(self, guess, validation):
        print(list(zip(guess, validation)))


    def play(self, total_attempts=6):
        for idx in range(total_attempts):
            guess = self.read_guess(idx+1)
            validation = self._validate_guess(guess)
            self.display_attempt(guess, validation)
            if sum(validation) == 5:
                return True
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Let's Play Wordle!", prog="wordle_engine")
    parser.add_argument("-t", "--target", dest="target", default=None, help="Set a Target Word")
    args = parser.parse_args()

    vocab_file_path = "./vocabulary/words1.txt"
    engine = WordleEngine(vocab_file_path, target_word=args.target)
    print(f"cheating: {engine._reveal_target_word()}\n")
    won = engine.play()
    if won:
        print("SUCCESS")
    else:
        print(f"FAILED. Target word is {engine._reveal_target_word()}")