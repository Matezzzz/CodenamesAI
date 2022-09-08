from common import *
import io
from scipy.spatial.distance import cosine as cosine_dist


class ModelInitializer:    
    @property
    def weights_filename(self) -> str: return None
    
    def computeWeights(self):
        return np.zeros(dictionary.weights_size)
        
    def getWeights(self):
        if self.weights_filename is not None and utils.file_exists(self.weights_filename):
            ws = utils.load_weights(self.weights_filename)
        else:
            print (f"Generating weights for {type(self).__name__}... ", end="", flush=True)
            ws = self.computeWeights()
            if self.weights_filename is not None: utils.save_weights(self.weights_filename, ws)
            print ("Done.", flush=True)
        ws = self.transformWeights(ws)
        ws /= np.max(ws)
        assert ws.shape[0] == len(dictionary.board_words) and ws.shape[1] == len(dictionary.hint_words), "Computed weights do not have the required dimensions"
        return ws

    def newWeights(self, default = 0.0):
        return np.ones(dictionary.weights_size) * default

    def transformWeights(self, weights):
        return weights
   
   

class WordCollocationsInitializer(ModelInitializer):
    @property
    def weights_filename(self): return "data/word_collocations.npy"
    
    def computeWeights(self):
        weights = self.newWeights()
        for sentence in language_settings.openCorpora().split("."):
            words = sentence.split("\n")
            board_words_i = [dictionary.boardWordI(w) for w in words]
            hint_words_i = [dictionary.hintWordI(w) for w in words]
            for b, h in zip(board_words_i[1:], hint_words_i[:-1]):
                if b is not None and h is not None:
                    weights[b, h] += 1
            for b, h in zip(board_words_i[:-1], hint_words_i[1:]):
                if b is not None and h is not None:
                    weights[b, h] += 1
        return weights
    
    def transformWeights(self, weights):
        return np.log(np.where(weights > 5, weights, 0) / (np.sum(weights, 0, keepdims=True) + 1e-4) + 1.0)


class SentenceCollocationsInitializer(ModelInitializer):
    @property
    def weights_filename(self): return "data/sentence_collocations.npy"
    
    def computeWeights(self):
        weights = self.newWeights()
        for sentence in language_settings.openCorpora().split("."):
            words = sentence.split("\n")
            board_words_i = list(filter(lambda x: x is not None, [dictionary.boardWordI(w) for w in words]))
            hint_words_i  = list(filter(lambda x: x is not None, [dictionary.hintWordI(w) for w in words]))
            for b in board_words_i:
                weights[b, hint_words_i] += 1
        return weights
    
    def transformWeights(self, weights):
        return np.log(np.where(weights > 5, weights, 0) / (np.sum(weights, 0, keepdims=True) + 1e-4) + 1.0)



class FastTextInitializer(ModelInitializer):
    hint_threshold : float
    
    def __init__(self, hint_threshold):
        self.hint_threshold = hint_threshold
    
    @property
    def weights_filename(self): return "data/fasttext_cosine.npy"
    
    def computeWeights(self):
        fin = io.open(language_settings.fast_text_file, 'r', encoding='utf-8', newline='\n', errors='ignore')
        n, d = map(int, fin.readline().split())
        data = {}
        for line in fin:
            tokens = line.rstrip().split(' ')
            word = tokens[0]
            embed = np.array(list(map(float, tokens[1:])))
            if dictionary.contains(word):
                data[word] = embed
        weights = self.newWeights()
        for b in range(dictionary.board_word_count):
            for h in range(dictionary.hint_word_count):
                bw = data.get(dictionary.boardWord(b))
                hw = data.get(dictionary.hintWord(h))
                weights[b, h] = (1 - cosine_dist(bw, hw) / 2) if bw is not None and hw is not None else 0
        return weights
    
    def transformWeights(self, weights):
        return np.maximum(weights - self.hint_threshold, 0) / (1 - self.hint_threshold)


class WordAssociationInitializer(ModelInitializer):
    @property
    def weights_filename(self): return "data/word_associations.npy"
    
    def computeWeights(self):
        WBASE, WASSOC, FSG, MSG = 0, 1, 5, 7
        lines = open("data/associations/data.txt").read().splitlines()
        weights = self.newWeights()
        for l in lines:
            a = l.lower().split(", ")
            hw = dictionary.hintWordI(a[WBASE])
            bw = dictionary.boardWordI(a[WASSOC])
            if hw is not None and bw is not None:
                w = float(a[FSG])
                try:
                    w += float(a[MSG])
                except ValueError:
                    pass
                weights[bw, hw] += w
        return weights


class CombinedInitializer(ModelInitializer):
    initializers : list[ModelInitializer]
    weights : list[float]
    
    def __init__(self, initializers, weights):
        self.initializers = initializers
        self.weights = weights
        
    def computeWeights(self):
        weights = self.newWeights()
        for w, i in zip(self.weights, self.initializers):
            weights += i.getWeights() * w
        return weights
    
if __name__ == "__main__":
    import main