from board import Board
from common import *
from datasets import ModelInitializer

from scipy.special import softmax

from renderer import colored
    


#represents one hint - a word with a count of related words on the board
class Hint:
    word_i : int
    count : int
    
    #hinted cards are only given when debugging
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
    
    #return this hint as string, colored. If hinted cards was given to the constructor, print it as well
    def colored(self, team):
        s = f'{self.word} {self.count}'
        if self.hinted_cards is not None: s += " -> " + " ".join([c.word for c in self.hinted_cards])
        return colored(s, team)





#a model with weights
class Model:
    weights : np.ndarray

    def __init__(self, initializer : ModelInitializer):
        self.weights = initializer.getWeights()


#AI agent model
class AgentModel (Model):
    #random chance - chance to select a random option weighted by softmax of all weights instead of the best one
    def __init__(self, initializer : ModelInitializer, random_chance = 0.0):
        super().__init__(initializer)
        self.random_chance = random_chance

    def guess(self, board : Board, hint : Hint):
        #get weights for the given hint and all the words on board
        word_weights = board.getWeights(self.weights, -np.inf)[:, hint.word_i]
        #select random weight based on the softmax of all with a chance self.random_chance. else select the best one
        if random.random() < self.random_chance:
            return np.random.choice(np.arange(self.board.size), p=softmax(word_weights))
        else:
            return np.argmax(word_weights)


#AI captain model
class CaptainModel (Model):
    def __init__(self, initializer : ModelInitializer, hint_mode = "score", reveal_hinted=False):
        super().__init__(initializer)
        self.hint_mode = hint_mode
        self.reveal_hinted=reveal_hinted

    #give a hint for the given team
    def giveHint(self, team : int, board : Board) -> Hint:
        word_weights = board.getCaptainWeights(self.weights, 0.0)
        if self.hint_mode == "score":
            #we assume agent will pick the words from the most probable one to the least probable one - get the indices of sorted array, separately for each hint
            sorted_indices = np.argsort(word_weights, 0)[::-1]
            
            
            #get sorted weights
            sorted_ws = np.take_along_axis(word_weights, sorted_indices, 0)
           
            #get scores for all board cards, sort it in the same way as sorted weights for each hint
            scores = np.broadcast_to(np.expand_dims(board.getScores(team), 1), word_weights.shape)
            sorted_scores = np.take_along_axis(scores, sorted_indices, 0)
            
            #compute score for every word in the sorted array
            individual_hint_scores = sorted_ws * sorted_scores
            #user will take from the most probable one - take the cumulative sum to represent all words selected after a given hint
            hint_scores = np.cumsum(individual_hint_scores, 0)
            
            #find the index of the best hint, decompose it into hint index and count
            best_hint = np.unravel_index(np.argmax(hint_scores), hint_scores.shape)
            #return the found hint, including the words I am hinting at if reveal hinted is true
            return Hint(best_hint[1], best_hint[0] + 1, [board.getCard(i) for i in sorted_indices[:best_hint[0]+1, best_hint[1]]] if self.reveal_hinted else None)
        else:
            print("Invalid hint mode.")
            return Hint.Invalid()
        


if __name__ == '__main__':
    import main