import typing
from common import *
import io


#base class for all initializers
class ModelInitializer:   
    weights_filename : typing.Optional[str] = None
    
    #should be overriden by child classes. Return weights - these will be saved in the file later
    def computeWeights(self, dictionary : Dictionary):
        return np.zeros(dictionary.weights_size)
    
    #load weights from a file if possible, else use the computeWeights method to compute them
    def getWeights(self, dictionary : Dictionary = dictionary):
        weights_filename = None if self.weights_filename is None else os.path.join("data", f"{self.weights_filename}_{dictionary.name}.npy")
        #if weights can be loaded, load them
        if weights_filename is not None and utils.file_exists(weights_filename):
            ws = utils.load_weights(weights_filename)
        #compute all weights
        else:
            print (f"Generating weights for {type(self).__name__}... ", end="", flush=True)
            ws = self.computeWeights(dictionary)
            #save weights if they should be saved
            if weights_filename is not None: utils.save_weights(weights_filename, ws)
            print ("Done.", flush=True)
        #transform weights - this is division by the largest value by default, can be overriden by child classes too
        ws = self.transformWeights(ws)
        #if computed weights do not match the dictionary, throw an error
        assert ws.shape[0] == len(dictionary.board_words) and ws.shape[1] == len(dictionary.hint_words), "Computed weights do not have the required dimensions"
        return ws

    #return a new weights array matching the dictionary, with given value
    def newWeights(self, dictionary : Dictionary, default = 0.0):
        return np.full(dictionary.weights_size, default)

    #divide weights by their largest value. Can be overriden in child classes
    def transformWeights(self, weights):
        return weights / np.max(weights)
   
   
#collocations initializer
class CollocationsInitializer(ModelInitializer):
    #before dividing by max value, remove all values smaller than 5, divide by the sum in each row, add 1.0, and take the logarithm of that
    def transformWeights(self, weights):
        return super().transformWeights(np.log(np.where(weights > 5, weights, 0) / (np.sum(weights, 0, keepdims=True) + 1e-4) + 1.0))


#initializer for word collocations
class WordCollocationsInitializer(CollocationsInitializer):
    def __init__(self, fname = "word_collocations"):
        self.weights_filename = fname
    
    def computeWeights(self, dictionary : Dictionary):
        weights = self.newWeights(dictionary)
        #go over all sentences in the corpora
        for sentence in language_settings.openCorpora().split("."):
            #go over all words get hint and word index for each one
            words = sentence.split("\n")
            board_words_i = [dictionary.boardWordI(w) for w in words]
            hint_words_i = [dictionary.hintWordI(w) for w in words]
            #go over all neighboring words, if they both are in the respective dictionaries, add 1 to the respective spot weights matrix
            for b, h in zip(board_words_i[1:], hint_words_i[:-1]):
                if b is not None and h is not None:
                    weights[b, h] += 1
            for b, h in zip(board_words_i[:-1], hint_words_i[1:]):
                if b is not None and h is not None:
                    weights[b, h] += 1
        #note - weights will be transformed using the parent transformWeights method before being used
        return weights
    
    
#initializer for sentence collocations
class SentenceCollocationsInitializer(CollocationsInitializer):
    def __init__(self, fname = "sentence_collocations"):
        self.weights_filename = fname

    def computeWeights(self, dictionary : Dictionary):
        weights = self.newWeights(dictionary)
        #go over all sentences in the corpora
        for sentence in language_settings.openCorpora().split("."):
            words = sentence.split("\n")
            board_words_i = list(filter(lambda x: x is not None, [dictionary.boardWordI(w) for w in words]))
            hint_words_i  = list(filter(lambda x: x is not None, [dictionary.hintWordI(w) for w in words]))
            #for all doubles in hint words i, board words i: add 1 to the target spot
            for b in board_words_i:
                weights[b, hint_words_i] += 1
        return weights



#fast text initializer 
class FastTextInitializer(ModelInitializer):
    #all cosine similarities transformed to <0, 1> below this threshold are deemed to be too far away, having similarity 0
    hint_threshold : float
    
    def __init__(self, hint_threshold, fname="fasttext_cosine"):
        self.hint_threshold = hint_threshold
        self.weights_filename = fname

    def computeWeights(self, dictionary : Dictionary):
        #open fast text embeddings file
        fin = io.open(language_settings.fast_text_file, 'r', encoding='utf-8', newline='\n', errors='ignore')
        n, d = map(int, fin.readline().split())
        #load embeddings into a dictionary - one element for a word and its embedding
        data = {}
        for line in fin:
            tokens = line.rstrip().split(' ')
            word = tokens[0]
            embed = np.array(list(map(float, tokens[1:])))
            if dictionary.contains(word):
                data[word] = embed
        
        #get a list of words, return a list of embeddings normalized to length 1 in euclidean space
        def embed(ws):
            elem = next(iter(data.values()))
            vals = np.stack([data.get(word, np.full_like(elem, np.nan)) for word in ws])
            lens = np.sqrt(np.sum(vals*vals, 1, keepdims=True))
            return vals / lens
        
        #embed both board and hint words
        board_embeds = embed(dictionary.board_words)
        hint_embeds = np.transpose(embed(dictionary.hint_words), [1, 0])
        
        #compute weights. Same as cosine similarity between words / 2 + 0.5
        weights = board_embeds @ hint_embeds / 2 + 0.5
        #if embedding didn't exist, the weights were set to nan -> all values relative to this embedding are now nan. Set them all to 0 (completely unrelated)
        weights = np.nan_to_num(weights)
        return weights
    
    #transform weights - subtract threshold from all, all smaller than 0 are set to 0. Then rescale the remaining values to lie between 0 and 1
    def transformWeights(self, weights):
        return np.maximum(weights - self.hint_threshold, 0) / (1 - self.hint_threshold)

#word associations
class WordAssociationInitializer(ModelInitializer):
    def __init__(self, fname = "word_associations"):
        self.weights_filename = fname 
    
    def computeWeights(self, dictionary : Dictionary):
        #base word, associated word, forward link strength, mediated link strength
        WBASE, WASSOC, FSG, MSG = 0, 1, 5, 7
        lines = open("data/associations/data.txt").read().splitlines()
        weights = self.newWeights(dictionary)
        #go over all word combinations in the dataset
        for l in lines:
            a = l.lower().split(", ")
            #if both words are available in the input dictionaries, add their weights into the array
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

#combines multiple initializaers into one
class CombinedInitializer(ModelInitializer):
    #combined initializers and the weights associated with each one
    initializers : list[ModelInitializer]
    weights : list[float]
    
    def __init__(self, initializers, weights):
        self.initializers = initializers
        self.weights = weights
        
    def computeWeights(self, dictionary : Dictionary):
        weights = self.newWeights(dictionary)
        #go over all initializers and sum their weights
        for w, i in zip(self.weights, self.initializers):
            weights += i.getWeights(dictionary) * w
        return weights
    
    DEFAULT_FASTTEXT_THRESHOLD = 0.685
    @staticmethod
    def DefaultInitializer(fast_text_threshold = DEFAULT_FASTTEXT_THRESHOLD):
        #create a combined initializer from all basic datasets
        basic = CombinedInitializer([WordCollocationsInitializer(), SentenceCollocationsInitializer(), FastTextInitializer(fast_text_threshold), WordAssociationInitializer()], [1, 0.5, 0.75, 1])

        #create a combined dataset of the basic dataset and the double link initializer of the basic dataset
        return CombinedInitializer([basic, DoubleLinkInitializer(basic)], [1.0, 1.0])



#similar idea to the mediated strength used in the associated dataset
#if a is close to b and b is close to c, humans will think of the connection a->c
class DoubleLinkInitializer(ModelInitializer):
    c_initializer : CombinedInitializer
    
    def __init__(self, combined_initializer : CombinedInitializer, fname="double_link"):
        self.weights_filename = fname
        self.c_initializer = combined_initializer

    def computeWeights(self, dictionary: Dictionary):
        #dictionary hint words * hint words
        full_dict = Dictionary(dictionary.hint_words, dictionary.hint_words, f"{language_settings.language}_full")
        #get weights for the full dictionary
        full_ws = self.c_initializer.getWeights(full_dict)
        #forbid each word from relating to itself
        np.fill_diagonal(full_ws, 0)
        
        board_ws = self.c_initializer.getWeights(dictionary)
        
        #compute mediated weights for all words
        weights = board_ws @ full_ws
        #forbid word having a weight to itself
        np.fill_diagonal(weights, 0)
        return weights
        
        
        
    
    
if __name__ == "__main__":
    import main