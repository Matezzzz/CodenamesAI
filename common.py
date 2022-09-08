import numpy as np
import random
import os



class utils:
    @staticmethod
    def np_len(array):
        return np.array([len(a) for a in array], dtype=np.int32)

    @staticmethod
    def confirm(prompt):
        while True:
            x = input(prompt + " (y / n): ")
            if x == 'y':
                return True
            if x == 'n':
                return False
            print ("Invalid character, try again")

    # @staticmethod
    # def numpy_save(dirname, fname, array):
    #     if utils.save_check(dirname, fname):
    #         np.save(os.path.join(dirname, fname), array)

    # @staticmethod
    # def python_save(dirname, fname, contents):
    #     f = os.path.join(dirname, fname)
    #     if utils.save_check(dirname, fname):
    #         open(f, 'w').write(contents)

    @staticmethod
    def save_check(fname):
        if utils.file_exists(fname):
            if not utils.confirm(f"File {fname} exists, overwrite?"):
                print ("Writing file declined, saving nothing")
                return False
        return True
        
    @staticmethod
    def file_exists(fname):
        return os.path.exists(fname)
        
    @staticmethod
    def load_words(fname):
        return open(fname).read().lower().split(" ")

    @staticmethod
    def save_words(fname, words):
        if utils.save_check(fname):
            with open(fname, "w") as f:
                f.write(" ".join(words))

    @staticmethod
    def load_weights(fname):
        return np.load(fname)
    
    @staticmethod
    def save_weights(fname, weights):
        np.save(fname, weights)
        




class Dictionary:
    board_words : list
    board_words_inv : dict
    @property
    def board_word_count(self): return len(self.board_words)

    hint_words : list
    hint_words_inv : dict
    @property
    def hint_word_count(self): return len(self.hint_words)
    
    max_board_word_length : int
    
    def __init__(self, board_words, hint_words):
        self.weights_size = [len(board_words), len(hint_words)]
        
        def inv(words): return {w:i for i, w in enumerate(words)}
        self.board_words = board_words
        self.board_words_inv = inv(board_words)
        
        self.hint_words = hint_words
        self.hint_words_inv = inv(hint_words)
        
        self.max_board_word_length = max(len(w) for w in board_words)
    

    @staticmethod
    def load():
        return Dictionary(language_settings.loadBoardWords(), language_settings.loadHintWords())
    
    # def save(self):
    #     utils.save_words(language_settings.board_words_file, self.board_words)
    #     utils.save_words(language_settings.hint_words_file, self.hint_words)
    
    def boardWord(self, i):
        return self.board_words[i]
    
    def boardWordI(self, word):
        return self.board_words_inv.get(word)
    
    def hintWord(self, i):
        return self.hint_words[i]
    
    def hintWordI(self, word):
        return self.hint_words_inv.get(word)
    
    def contains(self, word):
        return word in self.board_words_inv or word in self.hint_words_inv
    
    def randomBoardWords(self):
        words = np.arange(self.board_word_count)
        np.random.shuffle(words)
        return words[:game_settings.card_count]
    






class GameSettings:
    card_count : int
    team1_cards : int
    team2_cards : int
    neutral_cards : int
    assassin_cards : int
    
    def __init__(self, card_count : int, team1_cards : int, team2_cards : int, neutral_cards : int, assassin_cards : int):
        self.card_count = card_count
        self.team1_cards = team1_cards
        self.team2_cards = team2_cards
        self.neutral_cards = neutral_cards
        self.assassin_cards = assassin_cards
        assert(self.card_count == self.team1_cards + self.team2_cards + self.neutral_cards + self.assassin_cards)

    def randomRoles(self, blue_start):
        b, r = self.team1_cards, self.team2_cards
        if not blue_start: b,r = r,b
        roles = [x for x in [BLUE]*b+[RED]*r+[NEUTRAL]*self.neutral_cards+[ASSASSIN]*self.assassin_cards]
        random.shuffle(roles)
        return roles

    @staticmethod
    def Default():
        return GameSettings(25, 9, 8, 7, 1)

    


class LanguageSettings:
    corpora_file : str
    fast_text_file : str
    
    board_words_file : str
    hint_words_file : str
    
    hint_word_count : int
    
    def __init__(self, corpora_file, fast_text_file, board_words_file, hint_words_file, hint_word_count = 10000):
        self.corpora_file = corpora_file
        self.fast_text_file = fast_text_file
        self.board_words_file = board_words_file
        self.hint_words_file = hint_words_file
        self.hint_word_count = hint_word_count
        
    def openCorpora(self):
        return open(self.corpora_file).read()
    
    def loadBoardWords(self):
        return utils.load_words(self.board_words_file)
    
    def loadHintWords(self):
        if utils.file_exists(self.hint_words_file): return utils.load_words(self.hint_words_file)
        print ("Generating hint words... ", end="", flush=True)
        words = {}
        corpora = self.openCorpora()
        for word in corpora.split("\n"):
            if word.isalpha() and len(word) >= 3:
                if not word in words: words[word] = 0
                words[word] += 1
        words_l = [w for w in words if len(w) > 3]
        dict_words = sorted(words_l, key=lambda x:words[x], reverse=True)[:language_settings.hint_word_count]
        utils.save_words(self.hint_words_file, dict_words)
        print ("Done.", flush=True)
        return dict_words
    
    @staticmethod
    def English():
        return LanguageSettings("data/coca/lemmas_all.txt", "data/fasttext/wiki-news-300d-1M.vec", "data/board_words_en.txt", "data/hint_words_en.txt")


UNKNOWN = 0
BLUE = 1
RED = 2
NEUTRAL = 3
ASSASSIN = 4


class BoardDisplaySettings:
    width : int
    height : int
    cell_width : int
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cell_width = dictionary.max_board_word_length + 1
    
    @property
    def card_count(self):
        return self.width * self.height
    
    from colorama import Fore, Back
    colors = {UNKNOWN:Fore.WHITE, BLUE:Fore.BLUE, RED:Fore.RED, NEUTRAL:Fore.YELLOW, ASSASSIN:Fore.BLACK}
    back_colors = {UNKNOWN:Back.LIGHTWHITE_EX, BLUE:Back.LIGHTBLUE_EX, RED:Back.LIGHTRED_EX, NEUTRAL:Back.LIGHTYELLOW_EX, ASSASSIN:Back.LIGHTBLACK_EX}
    @staticmethod
    def roleColor(role, hidden):
        return "" if role == UNKNOWN else BoardDisplaySettings.colors[role] + "" if hidden else BoardDisplaySettings.back_colors[role]
    
    @staticmethod
    def Default():
        return BoardDisplaySettings(5, 5)


def clear():
    os.system('cls' if os.name=='nt' else 'clear')

def press_enter_clear():
    input("Enter to continue")
    clear()




if __name__ == '__main__':
    import main
else:
    game_settings = GameSettings.Default()
    language_settings = LanguageSettings.English()
    dictionary = Dictionary.load()
    display_settings = BoardDisplaySettings.Default()