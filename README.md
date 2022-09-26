# Codenames AI

## Update from last version
Please download the datasets again! I added one more to the mix. Directory structure is the same. [Link here](https://mega.nz/file/w9cAHCaa#0JxkJar4sUgGQPSSJGBdvPiC8cwzfCCj8D2HVh7OcH0)


## Introduction

Codenames is a game based on word association, where two teams compete to figure out which ones of the 25 cards laid on the table belong to them first. The game is played as follows - Each team has one captain, who, for each card on the table, knows which type it is (blue team, red team, neutral, assassin), and at the beginning of each teams' turn, he gives a hint - one word and a number of words associated with it. After that, the other person in his team, an agent, must pick words out of the ones available on the board, trying to guess which ones the captain meant (and which therefore have the color of his team). This is just an outline, the full rules can be read [here](https://mega.nz/file/8xFVTRKD#w644GdHOzIfocFdJ_RpkzYrbTXyfz4g6SM9Fw44vemM).

And, my task is to make an AI, that can function both as a captain as an agent. For this, I choose the following model:
 * One that has a matrix of weights of size possible hints by all game words, position (x, y) indicates how close hint x is to word y. I use matrix of size (404 x 10000, or (existing board words)x(10000 most frequent english word lemmas))
 * Captain model - giving a hint - select only the rows corresponding to words on the board, select the best hint among them
 * Agent model - select the column corresponding to the hint, from it only elements corresponding to board words. Select a word based on those weights
 * To simplify playing the game (so I don't have to play with multiple teams), I use the so-called auto team. It turns over one of its' cards each turn

The UI is really simple - all cards that we know the color of are colored, if they are revealed the background is colored as well. The text in the console should do explain the rest.


## Running

In addition to the source code available here, you need to download the required datasets. These can be downloaded here : [mega.nz](https://mega.nz/file/w9cAHCaa#0JxkJar4sUgGQPSSJGBdvPiC8cwzfCCj8D2HVh7OcH0). They should be unzipped, and pasted into the project directory. (if */project/main.py* is the path to the main file, */project/data/* directory should exist too, and contain *word_associations_en_board.npy*, *board_words_en.txt* and other files)

After that, run the *main.py* python file in the project directory to run the app.


## Required libraries

I use the following packages:
* numpy
* scipy
* Levenshtein (for the levenshtein metric. [Link](https://pypi.org/project/Levenshtein/))
* colorama (for printing colored text. [Link](https://pypi.org/project/colorama/))

And the following datasets:
* [COCA, lemmatized form](https://www.english-corpora.org/coca/)
* [fast text embeddings](https://fasttext.cc)
* [word associations](http://w3.usf.edu/FreeAssociation/)

## Models

### Captain model

Select only the rows corresponding to words on the board. After that, for every possible hint:
* Sort board words in descending order by their weights - I believe the first one will be selected first, then the second, and so on
* For each sorted word weight - multiply it by a score. score is positive when the word is mine, and negative otherwise
* Make a cumulative sum over all the words. This will get me the score when selecting all the words until the current one.
* Find the largest score over all positions and all hints - this is the hint I give.


### Agent model
Take my matrix of weights, and select just the columns with the words on board. Then select just the row with the hint given. After that, based on a chance specified when the agent is created, do one of the following things:
* Select the word with the highest score
* Take the word weights, apply a softmax to them, select a word based on the resulting probabilities.


### Creating a matrix of weights

There are many ways to create a matrix of weights that will later be used by either an agent or a captain model. Each method is called an initializer. After finishing the weights computation, I rescale every weights matrix so that the largest value is 1. I list all the ones I use below:
* Collocation initializers
    * All are computed by going through a corpus of lemmatized data, and checking which words occur close to each other
    * Word collocations - when two words are neighbours of one another, add 1 to the corresponding cell in the weights matrix
    * Sentence collocations - when two words are in the same sentence, add 1 to the corresponding cell in the weights matrix
    * After going through the whole corpus, I apply the following transformation:
        * Discard all values < 5
        * Divide each column by the largest value in it
        * Add 1 to everything, then take the logarithm of every value. This provides a smooth approximation of PMI (pointwise mutual information)
* Fast text embeddings initializer - the value in the matrix is equal to the cosine similarity between the embeddings of the two words. After that I divide the value by 2 and add 0.5 to get a similarity value between 0 and 1. I found experimentally that all words with similarity `< 0.685` are not similar at all, for that reason, I subtract this threshold from all values and set all values below zero to zero.
* Word assocation initializer - Set all weights to 0 by default. Then, read the word association dataset, and for every two words mentioned, set the value in the weights matrix to FSG (forward assocation strength) + MSG (mediated association strength)
* Double link initializer - try to approximate mediated associations in a dataset. Logic is, if A associates with B and B associates with C, A associates a bit with C. To compute the weights matrix, I use another method of creating weights as an input, and then for every target words A and C, I compute the mediated association weight as weight[A, B] * weight[B, C], and take a sum over all possible values B.
* Combined initializer - combine multiple creation methods into one. Because all the method outputs are all scaled to have a max value of 1, this works rather well. So, I take all the weights generated by subset method, multiply each by a weight associated with each creation method given to the combining function, and then sum the result.

The final AI uses the following initializer:
* Combined initializer, consisting of:
    * Combined dataset, weight 1.0, consisting of:
        * Word collocations, weight 1.0
        * Sentence collocations, weight 0.5
        * Fast text embeddings, weight 0.75
        * Word associations, weight 1.0
    * Double link data, weight 1.0, computed on the combined dataset defined above


## Code structure

I will list all files available in this project, and what they contain:
* `board.py` - class for a board card, scoring system used by captain models and the board class
* `common.py` - basic definitions used across many other files, including the global dictionary, settings related to the language currently being used, board display settings, game settings (how many cards does each team have), and few utility methods for saving and loading data
* `datasets.py` - all weight initializers as mentioned in the paragraph above
* `main.py` - start the game with teams as defined by the user, and play one round
* `model.py` - hint class, classes that describe the logic of both captain and agent models
* `players.py` - classes for both human and AI captain or agent players. Also provides the classes for teams that can play a turn, and the game class, which can run rounds of a game
* `renderer.py` - utility methods for printing the board or colored text into the console


## Details

### Disabling hints

All hints that are a substring of a word on board, contain a word from the board, or have a relative levenshtein distance to a word on board smaller than 0.5 are disabled, and cannot be used this round. Words that were hinted are disabled as well, to prevent the AI from using the same hint multiple times. Also, all words shorter than 3 characters are discarded from the dictionary and never used.

### Initializer saving

All of the initializers that have to do some heavy computation - this is everything except the combined inititializer - save their results to the disk when computed. After that, they are loaded instead of being recomputed every time.

### Default values
 * 25 cards, 9 of the first team, 8 of the second, 7 neutral cards and one assassin. Rendered as 5x5 board.
 * cards of the blue team are blue, those of the red team are red, neutral cards are yellow and the assassin is gray

 