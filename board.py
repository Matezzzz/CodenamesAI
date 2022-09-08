from typing import List
from common import *
from renderer import colored
from Levenshtein import distance as levenshtein_dist



class CardScoring:
    my_team : int
    enemy_team : int
    assassin : int
    neutral : int
    
    def __init__(self, me, enemy, ass, neut):
        self.my_team = me
        self.enemy_team = enemy
        self.assassin = ass
        self.neutral = neut
        
    def weights(self, blue_turn):
        return {BLUE:self.my_team if blue_turn else self.enemy_team, RED:self.enemy_team if blue_turn else self.my_team, ASSASSIN:self.assassin, NEUTRAL:self.neutral}
    
    @staticmethod
    def Default():
        return CardScoring(1, -3, -20, -1) 



class BoardCard:
    word_i : int
    role : int
    hidden : bool

    def __init__(self, word_i, role, hidden = True):
        self.word_i = word_i
        self.role = role
        self.hidden = hidden
    
    @property
    def word(self):
        return dictionary.boardWord(self.word_i)
    
    def getStr(self, known_role):
        role = self.role if known_role or not self.hidden else UNKNOWN
        return colored(f"{self.word : <{display_settings.cell_width}}", role, self.hidden)
    
    def __str__(self):
        return self.word
    
            


class Board:
    cards : List[BoardCard]
    size : int
    
    hidden_red_count : int
    hidden_blue_count : int
    assassin_selected : bool
    
    def __init__(self, words, roles):
        self.cards = [BoardCard(w, r) for w, r in zip(words, roles)]
        self.size = len(self.cards)
        
        self.hidden_blue_count = self.countRoles(BLUE)
        self.hidden_red_count = self.countRoles(RED)
        
        self.assassin_selected = False
        
        disabled_hints_l = []
        for c in self.cards:
            for i, h in enumerate(dictionary.hint_words):
                if c.word in h or h in c.word or levenshtein_dist(c.word, h) / max(len(c.word), len(h)) <= 0.5:
                    disabled_hints_l.append(i)
                    continue
        self.disabled_hints = np.zeros([dictionary.hint_word_count], dtype=np.bool8)
        self.disabled_hints[disabled_hints_l] = True
                    
        
    def countRoles(self, role):
        return sum(1 for c in self.cards if c.role == role)
    
    def getWeights(self, weights, hidden_val = 0.0):
        weights = np.array([weights[c.word_i] if c.hidden else np.full([dictionary.hint_word_count], hidden_val) for c in self.cards])
        weights[:, self.disabled_hints] = 0
        return weights
    
    def getScores(self, team : int, scoring : CardScoring = CardScoring.Default()):
        ws = scoring.weights(team == BLUE)
        scores = np.array([ws[c.role] for c in self.cards])
        return scores
    
    def reveal(self, card_i):
        if self.cards[card_i].hidden:
            self.cards[card_i].hidden = False
            c = self.cards[card_i]
            if c.role == BLUE: self.hidden_blue_count -= 1
            if c.role == RED: self.hidden_red_count -= 1
            if c.role == ASSASSIN: self.assassin_selected = True
            return c
        else:
            raise RuntimeError("This word cannot be guessed - it is already revealed") 
    
    def disableHint(self, hint_i):
        self.disabled_hints[hint_i] = True
    
    def findWord(self, word_i):
        return next(i for i, c in enumerate(self.cards) if c.word_i == word_i)
    
    def guess(self, card_i):
        return self.reveal(card_i)
        
    def canGuess(self, word_i):
        try:
            i = self.findWord(word_i)
            return self.cards[i].hidden
        except ValueError:
            return False
        
    def revealCardOfColor(self, team : int):
        c = random.choice([i for i, c in enumerate(self.cards) if c.hidden and c.role == team])
        self.reveal(c)
        return self.cards[c]
    
    def getCard(self, card_i : int):
        return self.cards[card_i]
    
    
    
    @staticmethod
    def randomBoard(blue_starts):
        return Board(dictionary.randomBoardWords(), game_settings.randomRoles(blue_starts))

    @property
    def game_ended(self):
        return self.blue_won or self.red_won or self.assassin_selected

    @property
    def blue_won(self):
        return self.hidden_blue_count == 0

    @property
    def red_won(self):
        return self.hidden_red_count == 0
    


if __name__ == '__main__':
    import main