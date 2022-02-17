import copy
from collections import defaultdict
import heapq
import itertools
import sys


class WordleSolver:

    def __init__(self, filepath, word_len=5):
        self.WORD_LEN = word_len

        self.inchars = set()        # characters part of the target word (green/yellow)
        self.outchars = set()       # characters not part of the target word (grey/black)
        
        self.pos_char_map = dict()  # {0..4} -> {a..z}
        
        # {0..4} -> [{a..z}]  characters not appearing on that position but part of the target word
        self.neg_pos_chars_map = defaultdict(list)

        self.filepath = filepath
        self.vocab = set()          # set of 5-letter words in the vocab
        with open(self.filepath, 'r') as file:
            for line in file:
                self.vocab.add(line.strip().lower())
        self.search_space = self.vocab.copy()

        self.prior_suggestions = ["soare", "adieu"]
        self.first_chance = True


    def _update_search_constraints(self, guess, validation, inchars=None, outchars=None, 
            pos_char_map=None, neg_pos_chars_map=None):
        
        if inchars is None or outchars is None or pos_char_map is None or neg_pos_chars_map is None:
            inchars = self.inchars
            outchars = self.outchars
            pos_char_map = self.pos_char_map
            neg_pos_chars_map = self.neg_pos_chars_map

        for idx, ch in enumerate(guess):
            if validation[idx] == 1:
                inchars.add(ch)
                outchars.discard(ch)
                pos_char_map[idx] = ch
            elif validation[idx] == 0:
                inchars.add(ch)
                neg_pos_chars_map[idx].append(ch)
            else:  # validation[idx] == -1
                if ch not in inchars:
                    outchars.add(ch)
                else:
                    neg_pos_chars_map[idx].append(ch)


    def _refine_set_of_candidates(self, search_space=None, inchars=None, outchars=None,
            pos_char_map=None, neg_pos_chars_map=None):

        if search_space is None or inchars is None or outchars is None \
                or pos_char_map is None or neg_pos_chars_map is None:
            search_space = self.search_space
            inchars = self.inchars
            outchars = self.outchars
            pos_char_map = self.pos_char_map
            neg_pos_chars_map = self.neg_pos_chars_map

        for word in list(search_space):
            if not self._check_if_word_satisfies_constraints(word, inchars, outchars, pos_char_map, neg_pos_chars_map):
                search_space.discard(word)
        return search_space


    def _check_if_word_satisfies_constraints(self, word, inchars=None, outchars=None, 
            pos_char_map=None, neg_pos_chars_map=None):

        if inchars is None or outchars is None or pos_char_map is None or neg_pos_chars_map is None:
            inchars = self.inchars
            outchars = self.outchars
            pos_char_map = self.pos_char_map
            neg_pos_chars_map = self.neg_pos_chars_map

        for idx, ch in pos_char_map.items():
            if word[idx] != ch:
                return False
        for idx, ch_list in neg_pos_chars_map.items():
            if word[idx] in ch_list:
                return False
        word_chars = set(word)
        if inchars.difference(word_chars) != set() \
                or outchars.difference(word_chars) != outchars:
            return False
        return True


    def _check_if_validation_satisfies_constraints(self, guess, validation):
        for idx, ch in self.pos_char_map.items():
            if (validation[idx] == 1 and guess[idx] != ch) \
                    or (guess[idx] == ch and validation[idx] != 1):
                return False

        for idx, ch_list in self.neg_pos_chars_map.items():
            if guess[idx] in ch_list:
                if (validation[idx] == 1) \
                        or (validation[idx] == -1 and not self._char_appears_somewhere_in_validation(
                                guess, validation, guess[idx])):
                    return False

        for idx, ch in enumerate(guess):
            if validation[idx] == -1 and ch in self.inchars and \
                    (not self._char_appears_somewhere_in_validation(guess, validation, ch)):
                return False
            if validation[idx] > -1 and ch in self.outchars:
                return False
        return True


    def _char_appears_somewhere_in_validation(self, guess, validation, char):
        for idx, ch in enumerate(guess):
            if ch == char and validation[idx] > -1:
                return True
        return False


    def _generate_all_valid_validations(self, guess):
        all_validations = itertools.product([-1, 0, 1], repeat=self.WORD_LEN)
        valid_validations = []
        for vl in all_validations:
            if self._check_if_validation_satisfies_constraints(guess, vl):
                valid_validations.append(vl)
        return valid_validations


    def compute_topk_suggestions(self, topk=10):
        cand_exp_search_space_map = dict()
        
        for candidate in self.search_space:
            cand_validations = self._generate_all_valid_validations(candidate)
            cand_search_spaces = []
            for cv in cand_validations:
                cand_init_search_space = self.search_space.copy()
                cand_init_inchars = self.inchars.copy()
                cand_init_outchars = self.outchars.copy()
                cand_init_pos_char_map = copy.deepcopy(self.pos_char_map)
                cand_init_neg_pos_chars_map = copy.deepcopy(self.neg_pos_chars_map)
                self._update_search_constraints(candidate, cv, cand_init_inchars, cand_init_outchars,
                    cand_init_pos_char_map, cand_init_neg_pos_chars_map)
                new_search_space = self._refine_set_of_candidates(cand_init_search_space, cand_init_inchars, 
                    cand_init_outchars, cand_init_pos_char_map, cand_init_neg_pos_chars_map)
                # if new_search_space:
                cand_search_spaces.append(len(new_search_space))
            if cand_search_spaces:
                cand_exp_search_space_map[candidate] = sum(cand_search_spaces)*1.0/len(cand_search_spaces)

        top_words = heapq.nsmallest(topk, cand_exp_search_space_map, key=cand_exp_search_space_map.get)
        top_words_with_search_space_sizes = [(w, cand_exp_search_space_map[w]) for w in top_words]
        return top_words_with_search_space_sizes


def read_guess_and_validation(suggestions, attempt_no):
    print(f"Here are a few suggestions: {suggestions}")
    guess = input(f"\nWhat's your attempt #{attempt_no}: ").strip().lower()
    validation = input(f"What's the engine validation (space separated list of integers): ")
    validation = list(map(int, validation.split()))
    return guess, validation


if __name__ == "__main__":
    vocab_file_path = "./words.txt"
    word_len = 5
    solver = WordleSolver(vocab_file_path, word_len)
    suggestions = solver.prior_suggestions
    
    attempt_no = 1
    while True:
        sys.stdout.flush()
        guess, validation = read_guess_and_validation(suggestions, attempt_no)
        attempt_no += 1
        
        solver._update_search_constraints(guess, validation)
        print("Here are the updated search constraints:")
        print(f"pos_char_map: {solver.pos_char_map}")
        print(f"neg_pos_chars_map: {solver.neg_pos_chars_map}")
        print(f"inchars: {solver.inchars}")
        print(f"outchars: {solver.outchars}")

        solver.search_space = solver._refine_set_of_candidates()
        
        if sum(validation) == word_len:
            print("SUCCESS")
            break
        suggestions = solver.compute_topk_suggestions(topk=10)
