from typing import List
from common import *
from renderer import colored
from Levenshtein import distance as levenshtein_dist





#represents one card currently present on the board
class BoardCard:
    #word on this card, index into an array of all possible board words
    word_i : int
    #role (BLUE, RED, NEUTRAL or ASSASSIN)
    role : int
    #whether this card is flipped over
    hidden : bool

    def __init__(self, word_i : int, role : int, hidden : bool = True):
        self.word_i = word_i
        self.role = role
        self.hidden = hidden
    
    #the word on this card, as string
    @property
    def word(self) -> str:
        return dictionary.boardWord(self.word_i)
    
    #get a colored string padded to cell width, known_role = show roles even for hidden cards (e.g. when captain is choosing a hint)
    def getStr(self, known_role : bool):
        #the role to color with
        role = self.role if known_role or not self.hidden else UNKNOWN
        return colored(f"{self.word : <{display_settings.cell_width}}", role, self.hidden)
    
    def __str__(self):
        return self.word
    
            



#associates a score with every card type
class CardScoring:
    my_team : float
    enemy_team : float
    assassin : float
    neutral : float
    
    def __init__(self, me, enemy, ass, neut):
        self.my_team = me
        self.enemy_team = enemy
        self.assassin = ass
        self.neutral = neut
    
    #return weights (swap my team and enemy team weights based on who should play right now)
    def weights(self, blue_turn):
        return {BLUE:self.my_team if blue_turn else self.enemy_team, RED:self.enemy_team if blue_turn else self.my_team, ASSASSIN:self.assassin, NEUTRAL:self.neutral}
    
    #default scoring - 1.0 for ally, -3.0 for enemy, -20.0 for assassin and -1.0 for neutral
    @staticmethod
    def Default():
        return CardScoring(1.0, -3.0, -20.0, -1.0) 



class Board:
    #list of all cards, and their count
    cards : List[BoardCard]
    size : int
    
    #how many red/blue cards are still hidden
    hidden_red_count : int
    hidden_blue_count : int
    #whether assassin was selected already
    assassin_selected : bool
    
    #mask of booleans, True means disabled hints (they were selected already, or they are too close to a word present on the board)
    disabled_hints : np.ndarray
    
    def __init__(self, words : List[int], roles : List[int]):
        self.cards = [BoardCard(w, r) for w, r in zip(words, roles)]
        self.size = len(self.cards)
        
        self.hidden_blue_count = self.countRoles(BLUE)
        self.hidden_red_count = self.countRoles(RED)
        
        self.assassin_selected = False
        
        #mask of disabled hints
        self.disabled_hints = np.full([dictionary.hint_word_count], False, dtype=np.bool8)
        for c in self.cards:
            for i, h in enumerate(dictionary.hint_words):
                #if a word is too close to a card (card contains word, word contains card, or the relative levenshtein distance is smaller than 50%), disable it
                if c.word in h or h in c.word or levenshtein_dist(c.word, h) / max(len(c.word), len(h)) <= 0.5:
                    self.disabled_hints[i] = True
                    continue
                            
    #count all cards of a given role
    def countRoles(self, role):
        return sum(1 for c in self.cards if c.role == role)
    
    #get weights for all hints and cards on board
    def getWeights(self, weights, hidden_val = 0.0):
        #return weights if card is hidden, else hidden val
        weights = np.array([weights[c.word_i] if c.hidden else np.full([dictionary.hint_word_count], hidden_val) for c in self.cards])
        #set all disabled hints as hidden
        weights[:, self.disabled_hints] = hidden_val
        return weights
    
    #get scores for all board cards, based on the team currently playing
    def getScores(self, team : int, scoring : CardScoring = CardScoring.Default()):
        #get a dictionary of weights
        ws = scoring.weights(team == BLUE)
        #get a score for each card based on all the weights, then return it
        return np.array([ws[c.role] for c in self.cards])
    
    #reveal a card at the given position
    def reveal(self, card_i : int):
        if self.cards[card_i].hidden:
            #reveal the card, update hidden counts based on type
            self.cards[card_i].hidden = False
            c = self.cards[card_i]
            if c.role == BLUE: self.hidden_blue_count -= 1
            if c.role == RED: self.hidden_red_count -= 1
            if c.role == ASSASSIN: self.assassin_selected = True
            #return the selected card
            return c
        else:
            raise RuntimeError("This word cannot be guessed - it is already revealed") 
    
    #disable a given hint (called when a captain says this hint)
    def disableHint(self, hint_i : int):
        self.disabled_hints[hint_i] = True
    
    #find the card with given word
    def findWord(self, word_i : int):
        return next(i for i, c in enumerate(self.cards) if c.word_i == word_i)
    
    #return true if given word can be guessed (=it exists on board and it is not hidden)
    def canGuess(self, word_i : int):
        try:
            i = self.findWord(word_i)
            return self.cards[i].hidden
        except ValueError:
            return False
    
    #select a random card of the given team color and reveal it
    def revealCardOfColor(self, team : int):
        #get indices of all cards of matching color, choose one at random
        c = random.choice([i for i, c in enumerate(self.cards) if c.hidden and c.role == team])
        #reveal it and return the card
        return self.reveal(c)
    
    #get a card at the given position    
    def getCard(self, card_i : int):
        return self.cards[card_i]
    
    #create a new random board, given the starting team
    @staticmethod
    def randomBoard(blue_starts : bool):
        return Board(dictionary.randomBoardWords(), game_settings.randomRoles(blue_starts))

    #true if either team has no hidden cards left or the assassin was revealed
    @property
    def game_ended(self):
        return self.blue_won or self.red_won or self.assassin_selected

    #=blue has no hidden cards left
    @property
    def blue_won(self):
        return self.hidden_blue_count == 0

    #=red has no hidden cards left
    @property
    def red_won(self):
        return self.hidden_red_count == 0
    


if __name__ == '__main__':
    import main