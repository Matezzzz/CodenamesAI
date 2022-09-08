## Codenames AI project

### Markings
 * Lines without a square marks facts, and not things to be implemented
 * 🟩 marks steps that have to be completed for the project to be considered finished
 * 🟨 marks optional ideas. Might be cool, but not needed for the project to be considered complete
 * 🟥 marks optional ideas with a high chance of not working
 * 🟦 marks stuff that's already finished
 * This is the scope I would aim for during the 'NPRG045 Individual software project' subject. As I do not know the expected size of the project, I set only the bare minimum to (hopefully) be able to match the thesis as green squares.  


### Terminology
 * Captain model - the model designed to give hints
 * Agent model - the model designed to guess words on board based on hints given
 * Dataset/weighted/trained models - models based on how they are created


### Models
 * Have a matrix of weights of size possible hints by all game words, position (x, y) indicates how close hint x is to word y


### Captain model
 * 🟦 Giving hints - based on my matrix of weights. Select columns based on words on the table excluding invalid hints (e.g. words too similar to the ones on the board) then select a hint based on a strategy below
   * 🟦 Take the hint where most words are my color and the probability of hitting an assassin is low enough
   * 🟨 Take softmax(row) as probabilities of each word. Then select the hint with and word count based on them
     * 🟨 Just use them to select the best possible out of many with the same count
     * 🟨 Discard all except the best options based on a heuristic. Then build a tree of all possible selected moves - each leaf will represent a list of selected cards. Because our turn ends when we hit a word that is not ours, all possibilities can be iterated over in a reasonable amount of time. Then we know the probabilities of selecting the assassin/enemy card/a number of our own. Select the one that has a low enough chance to select the assassin and the largest difference between our and enemy cards.
     * 🟨 Add behavior to any strategy above based on the current game state as well. E.g. when we are losing, and the enemy has just one card left, we should give more risky hints to at least try to win the game before it's their turn again.

### Agent model
  * 🟦 Guessing - take my matrix of weights, and select just the columns with the words on board. Then select just the row with the hint given. Then:
    * 🟦 Select the word with the highest score
    * 🟦 Take the word probabilities, then select one good enough at random - this won't be as good for the AI-AI team, but might be better at emulating human behavior. It should also be better for training. Something in between the two might be considered
  * 🟨 Extension for words not available in the dictionary. When a human is giving hints, it might often happen that a word is not in the matrix. Then, I can try using a character-level embedding neural network to guess the closest words present in the dictionary and work with an average of their matrices. Or, just generate a word embedding when working with an embedding model


### Dataset models
  * 🟦 The weight matrix is created by a function from a given dataset
  * Usable datasets might be:
    * 🟦 fast-text embeddings
    * 🟨 transformer embeddings (BERT/RobeCzech/Roberta, something like that)
    * 🟦 sentence/word collocations
    * 🟩 dataset of synonyms/antonyms/hypernyms
    * 🟨 finetune a transformer model directly to predict similarity between two given words: I would use some weight matrices that were already as a dataset, and hope, that a finetuned transformer model would be able to generalize better than original data. Would enable guessing even when worlds are not present in the dictionary 
    * 🟨 and more
  * 🟨 Might be useful to save how persuaded a dataset is that two words are close. E.g. when I don't have that much data, two words might be used together just by accident.

### Weighted models
  * 🟦 Weights are a weighted average of multiple dataset models. Weight for each dataset might be determined based on multiple factors:
    * 🟨 How reliable a dataset is (can be for each word, see section before, separate for each pair of words)
    * 🟦 Same weight for every dataset (moves problem to the dataset creation function)
    * 🟩 Selected randomly
    * 🟨 Selected to maximize evaluation score
  * 🟨 Results should probably be normalized in some way - so that different weights do not produce different magnitudes of results

### Trained models
  * Weights are not given at the start but are trained over many games
  * Select a role - captain/agent. Take a separate model for the other player on this team.
  * 🟩 If captain, generate a hint based on my weights. Let the other model guess. Increase weight for the word agent guessed (Most for the first guess, a little bit for the second, and so on).
  * 🟨 If agent, guess based on my weights. If the word is the color of my team, increase its weight, otherwise decrease it.
  * The other model can be one of the following:
    * 🟩 A weighted model. Its' weights should be changed sometimes so the trained model won't just learn an exact copy of what was saved in it.
    * 🟥 A dataset model. Just an extreme case of special weights, it is probably bad since many datasets will miss many word combinations
    * 🟩 A trained model. It is good that the model can learn something beyond what is in the datasets, however, it can also learn invalid associations. To prevent this, we might introduce regularization that will slightly move values back to what was in a weighted model. Weights would be selected at random and might change during training.


### Evaluation
 * 🟩 Captain models - let the model generate a hint, then a human guesses the words that were meant. Check that the captain and human meant the same words.
 * 🟨 Agent models - let a human give a hint, then guess the words that were meant. Problem - words not present in the dictionary, getting a decent amount of data for evaluating agent models is harder than for captain models - especially for hints with more words. (Making up good hints is hard, guessing is much easier)
 * 🟩 Forming a team of an agent and a captain, how long does it take them to win a game
   * 🟨 How many games do they lose when playing against other models?
   * 🟩 How often do they lose, when playing auto-bot (one that turns some of its cards over during each turn)?


### User interfaces
 * 🟩 All played turns that a human participated in are recorded and saved, for future evaluation
 * 🟦 Basic python - colored word grid in the command line. Input is done using the command line as well, hints are given as a string and a number, and guesses are given as lists of words. Easy to play and implement.
 * 🟨 Actual UI, use the web one from the master's thesis or make my own in pygame