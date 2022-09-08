from turtle import color
from board import Board
from common import *
from datasets import ModelInitializer

from scipy.special import softmax

from renderer import colored
    



class Hint:
    word_i : int
    count : int
    def __init__(self, word_i, count, hinted_cards=None):
        self.word_i = word_i
        self.count = count
        self.hinted_cards = hinted_cards
        
    @property
    def word(self):
        return dictionary.hintWord(self.word_i)
    
    @staticmethod
    def Invalid():
        return Hint(0, 0)
    
    def colored(self, team):
        s = f'{self.word} {self.count}'
        if self.hinted_cards is not None: s += " -> " + " ".join([c.word for c in self.hinted_cards])
        return colored(s, team)






class Model:
    weights : np.ndarray

    def __init__(self, initializer : ModelInitializer):
        self.weights = initializer.getWeights()



class AgentModel (Model):
    def __init__(self, initializer : ModelInitializer, random_chance = 0.0):
        super().__init__(initializer)
        self.random_chance = random_chance

    def guess(self, board : Board, hint : Hint):
        word_weights = board.getWeights(self.weights, -np.inf)[:, hint.word_i]
        if random.random() < self.random_chance:
            return np.random.choice(np.arange(self.board.size), p=softmax(word_weights))
        else:
            return np.argmax(word_weights)


class CaptainModel (Model):
    def __init__(self, initializer : ModelInitializer, hint_mode = "score", reveal_hinted=False):
        super().__init__(initializer)
        self.hint_mode = hint_mode
        self.reveal_hinted=reveal_hinted

    def giveHint(self, team : int, board : Board) -> Hint:
        word_weights = board.getWeights(self.weights, 0.0)
        #! take weights into account
        if self.hint_mode == "score":
            sorted_indices = np.argsort(word_weights, 0)[::-1]
            #score, but sort by weights. Then take the max of all sums
            scores = np.broadcast_to(np.expand_dims(board.getScores(team), 1), word_weights.shape)
            sorted_ws = np.take_along_axis(word_weights, sorted_indices, 0)
            #filtered_ws = np.where(sorted_ws > 0.1, sorted_ws, 0)
            sorted_scores = np.take_along_axis(scores, sorted_indices, 0)
            
            individual_hint_scores = sorted_ws * sorted_scores
            hint_scores = np.cumsum(individual_hint_scores, 0)
            
            debug_sorted = np.argsort(word_weights, 1)[:, ::-1]
            debug_sorted_ws = np.take_along_axis(word_weights, debug_sorted, 1)
            debug_hints = [", ".join([f"{dictionary.hintWord(w)}:{word_weights[i, w]}" for w in row[:100]]) for i, row in enumerate(debug_sorted)]
            debug_board_words = [c.word for c in board.cards]
            
            best_hint = np.unravel_index(np.argmax(hint_scores), hint_scores.shape)
            return Hint(best_hint[1], best_hint[0] + 1, [board.getCard(i) for i in sorted_indices[:best_hint[0]+1, best_hint[1]]] if self.reveal_hinted else None)
        else:
            print("Invalid hint mode.")
            return Hint.Invalid()
        


if __name__ == '__main__':
    import main