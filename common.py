import numpy as np
import random
import os
from typing import Dict, List


class utils:
    #ask the user to confirm a given operation
    @staticmethod
    def confirm(prompt : str):
        while True:
            x = input(prompt + " (y / n): ")
            if x == 'y':
                return True
            if x == 'n':
                return False
            print ("Invalid character, try again")

    #check whether fname exists, ask user to confirm op if it does. returns true if file should be saved
    @staticmethod
    def save_check(fname : str):
        if utils.file_exists(fname):
            if not utils.confirm(f"File {fname} exists, overwrite?"):
                print ("Writing file declined, saving nothing")
                return False
        return True
    
    @staticmethod
    def file_exists(fname : str):
        return os.path.exists(fname)
    
    #load space-separated words from a given file
    @staticmethod
    def load_words(fname : str):
        return open(fname).read().lower().split(" ")

    #save space-separated words into a given file. Ask if file exists.
    @staticmethod
    def save_words(fname : str, words : List[str]):
        if utils.save_check(fname):
            with open(fname, "w") as f:
                f.write(" ".join(words))

    #load numpy array from a given file
    @staticmethod
    def load_weights(fname : str):
        return np.load(fname)
    
    #save numpy array to a given file. Ask if file exists
    @staticmethod
    def save_weights(fname : str, weights : np.ndarray):
        if utils.save_check(fname):
            np.save(fname, weights)
        



#holds all board and hint words and methods to convert between them
class Dictionary:
    #list of all board words
    board_words : List[str]
    #dictionary of (board word, index in board words array)
    board_words_inv : Dict[str, int]
    @property
    def board_word_count(self): return len(self.board_words)


    #list of all hint words
    hint_words : List[str]
    #dictionary of (hint word, index in hint words array)
    hint_words_inv : Dict[str, int]
    @property
    def hint_word_count(self): return len(self.hint_words)
    
    #longest board word, in characters
    max_board_word_length : int
    
    #dictionary name (for file saving)
    name : str
    
    def __init__(self, board_words : List[str], hint_words : List[str], name : str):
        self.weights_size = [len(board_words), len(hint_words)]
        
        #create a dictionary as an inverse to the given list
        def inv(words): return {w:i for i, w in enumerate(words)}
        
        
        self.board_words = board_words
        self.board_words_inv = inv(board_words)
        
        self.hint_words = hint_words
        self.hint_words_inv = inv(hint_words)
        
        self.max_board_word_length = max(len(w) for w in board_words)
        
        self.name = name
    
    #load based on language settings
    @staticmethod
    def load():
        return Dictionary(language_settings.loadBoardWords(), language_settings.loadHintWords(), f"{language_settings.language}_board")
    
    #return the board word with a given index
    def boardWord(self, i : int):
        return self.board_words[i]
    
    #return an index for a given board word
    def boardWordI(self, word : str):
        return self.board_words_inv.get(word)
    
    #return the hint word with a given index
    def hintWord(self, i : int):
        return self.hint_words[i]
    
    #return an index for a given hint word
    def hintWordI(self, word : str):
        return self.hint_words_inv.get(word)
    
    #true if given word is a board or hint word
    def contains(self, word):
        return word in self.board_words_inv or word in self.hint_words_inv
    
    #get an array of random words
    def randomBoardWords(self):
        words = np.arange(self.board_word_count)
        np.random.shuffle(words)
        return words[:game_settings.card_count]
    





#holds card counts in a game
class GameSettings:
    card_count : int
    #starting team count
    team1_cards : int
    #second team count
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

    #return an with the correct amount of each role, shuffled
    def randomRoles(self, blue_start):
        b, r = self.team1_cards, self.team2_cards
        if not blue_start: b,r = r,b
        roles = [x for x in [BLUE]*b+[RED]*r+[NEUTRAL]*self.neutral_cards+[ASSASSIN]*self.assassin_cards]
        random.shuffle(roles)
        return roles

    #default game settings - 25 cards, 9 of starting team, 8 of the other one, 7 neutrals, and one assassin
    @staticmethod
    def Default():
        return GameSettings(25, 9, 8, 7, 1)

    

#all settings for a single language
class LanguageSettings:
    #corpora of lemmas
    corpora_file : str
    
    #fast text embeddings file
    fast_text_file : str
    
    #two files, one with all board words, second with all hint words
    board_words_file : str
    hint_words_file : str
    
    #language name
    language : str
    
    #return this many most frequent from a language as hint words
    hint_word_count : int
    
    def __init__(self, corpora_file, fast_text_file, board_words_file, hint_words_file, language, hint_word_count = 10000):
        self.corpora_file = corpora_file
        self.fast_text_file = fast_text_file
        self.board_words_file = board_words_file
        self.hint_words_file = hint_words_file
        self.language = language
        self.hint_word_count = hint_word_count
    
    #open and read the corpora file
    def openCorpora(self):
        return open(self.corpora_file).read()
    
    #load all board words
    def loadBoardWords(self):
        return utils.load_words(self.board_words_file)
    
    #load all hint words. Generate them from corpora if the file doesn't exist
    def loadHintWords(self):
        if utils.file_exists(self.hint_words_file): return utils.load_words(self.hint_words_file)
        print ("Generating hint words... ", end="", flush=True)
        #compute counts for every word of length > 3 in the corpora
        words = {}
        corpora = self.openCorpora()
        for word in corpora.split("\n"):
            if word.isalpha() and len(word) > 3:
                if not word in words: words[word] = 0
                words[word] += 1
        #create a list of all words
        words_l = [w for w in words]
        #sort words according to the frequencies computed above, then return N most frequent ones
        dict_words = sorted(words_l, key=lambda x:words[x], reverse=True)[:language_settings.hint_word_count]
        #save the computed words and return them
        utils.save_words(self.hint_words_file, dict_words)
        print ("Done.", flush=True)
        return dict_words
    
    #create language settings for english
    @staticmethod
    def English():
        return LanguageSettings("data/coca/lemmas_all.txt", "data/fasttext/wiki-news-300d-1M.vec", "data/board_words_en.txt", "data/hint_words_en.txt", "en")


#one constant for every possible card value
UNKNOWN = 0
BLUE = 1
RED = 2
NEUTRAL = 3
ASSASSIN = 4


#display settings for a board - width and height in words, cell width in characters
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
    
    #return a color matching a role. if not hidden, background is colored as well
    from colorama import Fore, Back
    colors = {UNKNOWN:Fore.WHITE, BLUE:Fore.BLUE, RED:Fore.RED, NEUTRAL:Fore.YELLOW, ASSASSIN:Fore.BLACK}
    back_colors = {UNKNOWN:Back.LIGHTWHITE_EX, BLUE:Back.LIGHTBLUE_EX, RED:Back.LIGHTRED_EX, NEUTRAL:Back.LIGHTYELLOW_EX, ASSASSIN:Back.LIGHTBLACK_EX}
    @staticmethod
    def roleColor(role, hidden):
        return "" if role == UNKNOWN else BoardDisplaySettings.colors[role] + "" if hidden else BoardDisplaySettings.back_colors[role]
    
    #default render settings 5x5 board,25 cards
    @staticmethod
    def Default():
        return BoardDisplaySettings(5, 5)

#clear everything in the console. Different for windows and unix systems
def clear():
    os.system('cls' if os.name=='nt' else 'clear')

#wait for user to press enter, clear the console when he does
def press_enter_clear():
    input("Enter to continue")
    clear()




if __name__ == '__main__':
    import main
else:
    #set all settings as global variables
    game_settings = GameSettings.Default()
    language_settings = LanguageSettings.English()
    dictionary = Dictionary.load()
    display_settings = BoardDisplaySettings.Default()